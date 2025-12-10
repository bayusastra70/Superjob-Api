import json
import logging
from datetime import datetime
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
                    "timestamp": (timestamp or datetime.utcnow()).isoformat(),
                    "is_read": False,
                    "description": meta.get("description") if isinstance(meta, dict) else None,
                    "associated_data": meta.get("associated_data") if isinstance(meta, dict) else None,
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

    def purge_older_than(self, days: int = 14) -> int:
        """
        Delete activity logs older than N days.
        Returns number of rows deleted.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM activity_logs WHERE timestamp < NOW() - INTERVAL '%s days'",
                (days,),
            )
            deleted = cursor.rowcount
            conn.commit()
            logger.info("Purged old activity logs", extra={"deleted": deleted, "days": days})
            return deleted
        except Exception as exc:
            logger.error("Failed to purge old activity logs", exc_info=exc)
            return 0

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
    ) -> Optional[int]:
        subtitle = f"{applicant_name} melamar untuk {job_title or 'posisi'}"
        meta = {
            "body": f"Pelamar baru: {applicant_name}",
            "description": subtitle,
            "cta": f"/jobs/{job_id}/applications/{applicant_id}" if job_id and applicant_id else None,
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
    ) -> Optional[int]:
        subtitle = f"Status {applicant_name or 'pelamar'} berubah: {old_status or '-'} -> {new_status}"
        meta = {
            "body": subtitle,
            "description": subtitle,
            "cta": f"/jobs/{job_id}/applications/{applicant_id}" if job_id and applicant_id else None,
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
    ) -> Optional[int]:
        subtitle = f"{sender_name} → {receiver_name}: {message_preview[:80]}"
        meta = {
            "body": message_preview,
            "description": subtitle,
            "cta": f"/chats/{thread_id}",
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


activity_log_service = ActivityLogService()
