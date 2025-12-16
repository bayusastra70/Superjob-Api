import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.services.database import get_db_connection
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class ActivityLogService:
    """
    Helper untuk mencatat aktivitas/notifikasi ke tabel activity_logs.
    Setiap payload mengikuti pola Title/Subtitle + meta_data untuk Body/CTA.
    """

    def __init__(self):
        pass

    def _normalize_id(self, value: Any, fallback: str = "unknown") -> str:
        if value is None:
            return fallback
        try:
            return str(value)
        except Exception:
            return fallback

    def _insert(
        self,
        *,
        employer_id: Any,
        type: str,
        title: str,
        subtitle: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None,
        job_id: Any = None,
        applicant_id: Optional[int] = None,
        message_id: Any = None,
        timestamp: Optional[datetime] = None,
    ) -> Optional[int]:
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            meta = meta_data or {}
            meta_json = json.dumps(meta)

            insert_query = """
            INSERT INTO activity_logs (
                employer_id, type, title, subtitle, meta_data,
                job_id, applicant_id, message_id, timestamp, is_read
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()), false)
            RETURNING id
            """

            cursor.execute(
                insert_query,
                (
                    self._normalize_id(employer_id),
                    type,
                    title,
                    subtitle,
                    meta_json,
                    self._normalize_id(job_id) if job_id is not None else None,
                    applicant_id,
                    self._normalize_id(message_id) if message_id is not None else None,
                    timestamp,
                ),
            )
            result = cursor.fetchone()
            conn.commit()
            activity_id = result["id"] if result else None

            # Push to WebSocket subscribers if available
            payload = {
                "type": "activity:new",
                "data": {
                    "id": activity_id,
                    "employer_id": str(employer_id),
                    "activity_type": type,
                    "title": title,
                    "subtitle": subtitle,
                    "meta_data": meta,
                    "job_id": str(job_id) if job_id else None,
                    "applicant_id": applicant_id,
                    "message_id": str(message_id) if message_id else None,
                    "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
                    "is_read": False,
                    "description": meta.get("description")
                    if isinstance(meta, dict)
                    else None,
                    "associated_data": meta.get("associated_data")
                    if isinstance(meta, dict)
                    else None,
                },
            }
            try:
                import asyncio

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(
                        websocket_manager.broadcast_activity(str(employer_id), payload)
                    )
                else:
                    loop.run_until_complete(
                        websocket_manager.broadcast_activity(str(employer_id), payload)
                    )
            except RuntimeError:
                # If no loop (e.g., running in sync context), skip WS push
                pass

            return activity_id
        except Exception as exc:
            logger.error("Failed to insert activity log", exc_info=exc)
            return None
        finally:
            if cursor:
                cursor.close()

    def get_activity_by_id(self, activity_id: int) -> Optional[dict]:
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, employer_id, type, title, subtitle, meta_data,
                       job_id, applicant_id, message_id, timestamp, is_read
                FROM activity_logs
                WHERE id = %s
                """,
                (activity_id,),
            )
            return cursor.fetchone()
        finally:
            if cursor:
                cursor.close()

    def get_activity_detail_by_id(self, activity_id: int) -> Optional[dict]:
        """
        Get activity detail with user information for detail page.
        Returns activity data with user info (name, email, role).
        """
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    a.id, a.employer_id, a.type, a.title, a.subtitle, a.meta_data,
                    a.job_id, a.applicant_id, a.message_id, a.timestamp, a.is_read,
                    u.id AS user_id,
                    COALESCE(u.full_name, u.username) AS user_name,
                    u.email AS user_email,
                    CASE 
                        WHEN u.is_superuser THEN 'Administrator'
                        ELSE 'User'
                    END AS user_role
                FROM activity_logs a
                LEFT JOIN users u ON CAST(a.employer_id AS INTEGER) = u.id
                WHERE a.id = %s
                """,
                (activity_id,),
            )
            return cursor.fetchone()
        finally:
            if cursor:
                cursor.close()

    def list_timeline_activities(
        self,
        *,
        employer_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """
        List all activities for timeline tab (no filters).
        Returns activities with pagination.
        """
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT a.id, a.employer_id, a.type, a.title, a.subtitle, a.meta_data,
                       a.job_id, a.applicant_id, a.message_id, a.timestamp, a.is_read,
                       COALESCE(u.full_name, u.username) AS user_name
                FROM activity_logs a
                LEFT JOIN users u ON CAST(a.employer_id AS INTEGER) = u.id
                WHERE a.employer_id = %s
                ORDER BY a.timestamp DESC
                LIMIT %s OFFSET %s
                """,
                (str(employer_id), limit, offset),
            )
            rows = cursor.fetchall()

            cursor.execute(
                "SELECT COUNT(*) AS total FROM activity_logs WHERE employer_id = %s",
                (str(employer_id),),
            )
            total = cursor.fetchone()["total"]

            return rows, total
        finally:
            if cursor:
                cursor.close()

    def export_activities(
        self,
        *,
        employer_id: str,
    ) -> list[dict]:
        """
        Export all activities for employer (for export feature).
        Returns all activities without pagination.
        """
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT a.id, a.employer_id, a.type, a.title, a.subtitle, a.meta_data,
                       a.job_id, a.applicant_id, a.message_id, a.timestamp, a.is_read,
                       COALESCE(u.full_name, u.username) AS user_name
                FROM activity_logs a
                LEFT JOIN users u ON CAST(a.employer_id AS INTEGER) = u.id
                WHERE a.employer_id = %s
                ORDER BY a.timestamp DESC
                """,
                (str(employer_id),),
            )
            return cursor.fetchall()
        finally:
            if cursor:
                cursor.close()

    def mark_read(self, activity_id: int) -> bool:
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE activity_logs SET is_read = true WHERE id = %s",
                (activity_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as exc:
            logger.error("Failed to mark activity as read", exc_info=exc)
            return False
        finally:
            if cursor:
                cursor.close()

    def purge_older_than(self, days: int = 14) -> int:
        """
        Delete activity logs older than N days.
        Returns number of rows deleted.
        """
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM activity_logs WHERE timestamp < NOW() - INTERVAL '%s days'",
                (days,),
            )
            deleted = cursor.rowcount
            conn.commit()
            logger.info(
                "Purged old activity logs", extra={"deleted": deleted, "days": days}
            )
            return deleted
        except Exception as exc:
            logger.error("Failed to purge old activity logs", exc_info=exc)
            return 0
        finally:
            if cursor:
                cursor.close()

    def log_new_applicant(
        self,
        *,
        employer_id: Any,
        job_id: Any,
        applicant_id: Optional[int],
        applicant_name: str,
        job_title: Optional[str],
        source: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        role: Optional[str] = None,
    ) -> Optional[int]:
        subtitle = f"{applicant_name} melamar untuk {job_title or 'posisi'}"
        meta = {
            "body": f"Pelamar baru: {applicant_name}",
            "description": subtitle,
            "cta": f"/jobs/{job_id}/applications/{applicant_id}"
            if job_id and applicant_id
            else None,
            "role": role or "unknown",
            "associated_data": {
                "job_id": str(job_id) if job_id else None,
                "applicant_id": applicant_id,
                "source": source or "application",
                "ip_address": ip_address or "unknown",
                "user_agent": user_agent or "unknown",
            },
        }
        return self._insert(
            employer_id=employer_id,
            type="new_applicant",
            title="Pelamar baru",
            subtitle=subtitle,
            meta_data=meta,
            job_id=job_id,
            applicant_id=applicant_id,
        )

    def log_status_update(
        self,
        *,
        employer_id: Any,
        job_id: Any,
        applicant_id: int,
        applicant_name: Optional[str],
        old_status: Optional[str],
        new_status: str,
        source: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        role: Optional[str] = None,
    ) -> Optional[int]:
        subtitle = f"Status {applicant_name or 'pelamar'} berubah: {old_status or '-'} -> {new_status}"
        meta = {
            "body": subtitle,
            "description": subtitle,
            "cta": f"/jobs/{job_id}/applications/{applicant_id}"
            if job_id and applicant_id
            else None,
            "role": role or "unknown",
            "associated_data": {
                "job_id": str(job_id) if job_id else None,
                "applicant_id": applicant_id,
                "from_status": old_status,
                "to_status": new_status,
                "source": source or "status_update",
                "ip_address": ip_address or "unknown",
                "user_agent": user_agent or "unknown",
            },
        }
        return self._insert(
            employer_id=employer_id,
            type="status_update",
            title="Update status pelamar",
            subtitle=subtitle,
            meta_data=meta,
            job_id=job_id,
            applicant_id=applicant_id,
        )

    def log_new_message(
        self,
        *,
        employer_id: Any,
        job_id: Any,
        applicant_id: Optional[int],
        message_id: Any,
        sender_name: str,
        receiver_name: str,
        message_preview: str,
        thread_id: Any,
        source: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        role: Optional[str] = None,
    ) -> Optional[int]:
        subtitle = f"{sender_name} → {receiver_name}: {message_preview[:80]}"
        meta = {
            "body": message_preview,
            "description": subtitle,
            "cta": f"/chats/{thread_id}",
            "role": role or "unknown",
            "associated_data": {
                "thread_id": thread_id,
                "job_id": str(job_id) if job_id else None,
                "applicant_id": applicant_id,
                "sender": sender_name,
                "receiver": receiver_name,
                "source": source or "chat",
                "ip_address": ip_address or "unknown",
                "user_agent": user_agent or "unknown",
            },
        }
        return self._insert(
            employer_id=employer_id,
            type="new_message",
            title="Pesan baru",
            subtitle=subtitle,
            meta_data=meta,
            job_id=job_id,
            applicant_id=applicant_id,
            message_id=message_id,
        )

    def log_job_performance_alert(
        self,
        *,
        employer_id: Any,
        job_id: Any,
        job_title: Optional[str],
        metric: str,
        current_value: Any,
        threshold: Any,
        status: Optional[str] = None,
        source: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        role: Optional[str] = None,
    ) -> Optional[int]:
        subtitle = f"{metric} di bawah ambang: {current_value} < {threshold}"
        meta = {
            "body": f"Job {job_title or job_id}: {subtitle}",
            "metric": metric,
            "current_value": current_value,
            "threshold": threshold,
            "status": status,
            "cta": f"/jobs/{job_id}/performance" if job_id else None,
            "description": subtitle,
            "role": role or "system",
            "associated_data": {
                "job_id": str(job_id) if job_id else None,
                "metric": metric,
                "current_value": current_value,
                "threshold": threshold,
                "status": status,
                "source": source or "job_performance",
                "ip_address": ip_address or "system",
                "user_agent": user_agent or "system",
            },
        }
        return self._insert(
            employer_id=employer_id,
            type="job_performance_alert",
            title="Peringatan performa lowongan",
            subtitle=subtitle,
            meta_data=meta,
            job_id=job_id,
        )

    def get_dashboard_stats(self, employer_id: str) -> dict:
        """
        Get activity stats for last 24 hours.
        Returns counts for: job_published, new_applicant, status_update, team_member_updated
        """
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT 
                    COALESCE(SUM(CASE WHEN type = 'job_published' THEN 1 ELSE 0 END), 0) AS job_published,
                    COALESCE(SUM(CASE WHEN type = 'new_applicant' THEN 1 ELSE 0 END), 0) AS new_applicant,
                    COALESCE(SUM(CASE WHEN type = 'status_update' THEN 1 ELSE 0 END), 0) AS application_status_changed,
                    COALESCE(SUM(CASE WHEN type = 'team_member_updated' THEN 1 ELSE 0 END), 0) AS team_member_updated
                FROM activity_logs
                WHERE employer_id = %s
                AND timestamp >= NOW() - INTERVAL '24 hours'
                """,
                (str(employer_id),),
            )
            result = cursor.fetchone()

            return {
                "job_published": result["job_published"] or 0,
                "new_applicant": result["new_applicant"] or 0,
                "application_status_changed": result["application_status_changed"] or 0,
                "team_member_updated": result["team_member_updated"] or 0,
            }
        except Exception as exc:
            logger.error("Failed to get dashboard stats", exc_info=exc)
            return {
                "job_published": 0,
                "new_applicant": 0,
                "application_status_changed": 0,
                "team_member_updated": 0,
            }
        finally:
            if cursor:
                cursor.close()

    def log_job_published(
        self,
        *,
        employer_id: Any,
        job_id: Any,
        job_title: Optional[str],
        source: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        role: Optional[str] = None,
    ) -> Optional[int]:
        """Log ketika job berhasil di-publish"""
        subtitle = f"Lowongan '{job_title or 'Untitled'}' berhasil dipublikasikan"
        meta = {
            "body": f"Job published: {job_title}",
            "description": subtitle,
            "cta": f"/jobs/{job_id}" if job_id else None,
            "role": role or "employer",
            "associated_data": {
                "job_id": str(job_id) if job_id else None,
                "job_title": job_title,
                "source": source or "job_publish",
                "ip_address": ip_address or "unknown",
                "user_agent": user_agent or "unknown",
            },
        }
        return self._insert(
            employer_id=employer_id,
            type="job_published",
            title="Job published",
            subtitle=subtitle,
            meta_data=meta,
            job_id=job_id,
        )

    def log_team_member_updated(
        self,
        *,
        employer_id: Any,
        member_name: str,
        action: str,  # 'added', 'removed', 'role_changed'
        new_role: Optional[str] = None,
        source: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        role: Optional[str] = None,
    ) -> Optional[int]:
        """Log ketika team member diupdate (added/removed/role changed)"""
        action_text = {
            "added": f"{member_name} ditambahkan ke tim",
            "removed": f"{member_name} dihapus dari tim",
            "role_changed": f"Role {member_name} diubah menjadi {new_role or 'N/A'}",
        }
        subtitle = action_text.get(action, f"Team member {member_name} updated")

        meta = {
            "body": f"Team update: {member_name}",
            "description": subtitle,
            "cta": "/team-members",
            "role": role or "employer",
            "associated_data": {
                "member_name": member_name,
                "action": action,
                "new_role": new_role,
                "source": source or "team_management",
                "ip_address": ip_address or "unknown",
                "user_agent": user_agent or "unknown",
            },
        }
        return self._insert(
            employer_id=employer_id,
            type="team_member_updated",
            title="Team member updated",
            subtitle=subtitle,
            meta_data=meta,
        )


activity_log_service = ActivityLogService()
