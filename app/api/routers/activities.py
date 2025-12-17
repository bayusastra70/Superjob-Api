import logging
import math
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.schemas.activity import (
    Activity,
    ActivityDashboardStats,
    ActivityDashboardResponse,
    ActivityDetailResponse,
    ActivityAssociatedData,
    ActivityUserInvolved,
    TimelineListResponse,
)
from app.schemas.user import UserResponse
from app.services.activity_log_service import activity_log_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/employer/{employer_id}/activities", tags=["activities"])
actions_router = APIRouter(prefix="/activities", tags=["activities"])


def _parse_redirect(meta: Any) -> str | None:
    if isinstance(meta, dict):
        return meta.get("cta") or meta.get("redirect_url")
    return None


def _fetch_activity_row(activity_id: int) -> dict | None:
    return activity_log_service.get_activity_by_id(activity_id)


def _row_to_activity(row: dict) -> Activity:
    """Helper to convert a database row to Activity schema"""
    meta = row.get("meta_data") or {}
    redirect_url = _parse_redirect(meta)
    return Activity(
        id=row["id"],
        employer_id=str(row["employer_id"]),
        type=row["type"],
        title=row["title"],
        subtitle=row.get("subtitle"),
        meta_data=meta if isinstance(meta, dict) else {},
        job_id=str(row["job_id"]) if row.get("job_id") else None,
        applicant_id=row.get("applicant_id"),
        message_id=str(row["message_id"]) if row.get("message_id") else None,
        timestamp=row["timestamp"],
        is_read=row["is_read"],
        redirect_url=redirect_url,
        user_name=row.get("user_name"),
    )


# =============================================================================
# DASHBOARD ENDPOINT (Gambar 1)
# Stats Last 24 Hour + Recent Activities (limit 3)
# =============================================================================
@router.get(
    "/dashboard",
    response_model=ActivityDashboardResponse,
    summary="Activity Log Dashboard",
    description="""
    Mendapatkan data untuk halaman Activity Log Dashboard (Tab Dashboard/Widget).
    
    **Response includes:**
    - Stats Last 24 Hour: Job Published, New Applicant, Application status changed, Team member updated
    - Recent activities (limit 3 untuk dashboard)
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
)
def get_activity_dashboard(
    employer_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get activity log dashboard data - Stats + Recent Activities"""
    # Guard: hanya boleh akses milik sendiri atau superuser
    if str(current_user.id) != str(employer_id) and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    try:
        # Get stats last 24 hours
        stats = activity_log_service.get_dashboard_stats(employer_id)
        # Get recent activities (limit 3 for dashboard widget)
        rows, total = activity_log_service.list_timeline_activities(
            employer_id=str(employer_id),
            limit=3,
            offset=0,
        )
        items: List[Activity] = [_row_to_activity(row) for row in rows]

        return ActivityDashboardResponse(
            stats=ActivityDashboardStats(**stats),
            recent_activities=items,
            total=total,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to fetch activity dashboard", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "FAILED_FETCH_DASHBOARD",
                "message": "Failed to fetch activity dashboard",
            },
        )


# =============================================================================
# TIMELINE ENDPOINT (Gambar 2)
# Full list dengan pagination, tanpa filter
# =============================================================================
@router.get(
    "/timeline",
    response_model=TimelineListResponse,
    summary="Activity Timeline",
    description="""
    Mendapatkan full list aktivitas untuk Tab Timeline.
    Semua aktivitas ditampilkan dengan pagination, tanpa filter.
    
    **Pagination:**
    - `page`: Nomor halaman (default: 1)
    - `limit`: Jumlah item per halaman (default: 10, max: 10000)
    
    **Response includes:**
    - Full list of activities
    - Pagination info (page, limit, total, total_pages)
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
)
def get_activity_timeline(
    employer_id: str,
    limit: int = Query(10, ge=1, le=10000, description="Jumlah item per halaman"),
    page: int = Query(1, ge=1, description="Nomor halaman"),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get full activity list for Timeline tab"""
    # Guard: hanya boleh akses milik sendiri atau superuser
    if str(current_user.id) != str(employer_id) and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    offset = (page - 1) * limit

    try:
        rows, total = activity_log_service.list_timeline_activities(
            employer_id=str(employer_id),
            limit=limit,
            offset=offset,
        )

        items: List[Activity] = [_row_to_activity(row) for row in rows]
        total_pages = math.ceil(total / limit) if total > 0 else 1

        return TimelineListResponse(
            items=items,
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to fetch activity timeline", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "FAILED_FETCH_TIMELINE",
                "message": "Failed to fetch activity timeline",
            },
        )


def _get_summary_from_type(activity_type: str, title: str) -> str:
    """Generate summary based on activity type (matching highfi)"""
    type_to_summary = {
        "new_applicant": "New Applicant",
        "status_update": "Application status changed",
        "job_published": "Job published",
        "new_message": "New message",
        "job_performance_alert": "Performance alert",
        "team_member_updated": "Team member updated",
        "system_event": "System event",
    }
    return type_to_summary.get(activity_type, title)


# =============================================================================
# ACTIVITY DETAIL ENDPOINT (Gambar 3)
# Detail lengkap satu activity
# =============================================================================
@router.get(
    "/{activity_id}",
    response_model=ActivityDetailResponse,
    summary="Activity Detail",
    description="""
    Mendapatkan detail lengkap satu aktivitas.
    
    **Response includes:**
    - Activity Description
    - Associated Data (Activity ID, Source, IP Address, Browser/OS)
    - User Involved (name, email, role)
    - Status (Successful/Failed)
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
)
def get_activity_detail(
    employer_id: str,
    activity_id: int,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get detailed information for a single activity"""
    # Guard: hanya boleh akses milik sendiri atau superuser
    if str(current_user.id) != str(employer_id) and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    try:
        row = activity_log_service.get_activity_detail_by_id(activity_id)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ACTIVITY_NOT_FOUND", "message": "Activity not found"},
            )

        # Verify ownership
        if str(row["employer_id"]) != str(employer_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": "Activity does not belong to this employer",
                },
            )

        meta = row.get("meta_data") or {}
        associated_raw = (
            meta.get("associated_data", {}) if isinstance(meta, dict) else {}
        )

        # Build Associated Data
        associated_data = ActivityAssociatedData(
            activity_id=f"act_{row['id']:x}",  # Format like "act_1a2b3c4d5e6f7g8h"
            source=associated_raw.get("source", "Web Browser"),
            ip_address=associated_raw.get("ip_address"),
            browser_os=associated_raw.get("user_agent"),
            job_id=str(row["job_id"])
            if row.get("job_id")
            else associated_raw.get("job_id"),
            applicant_id=row.get("applicant_id") or associated_raw.get("applicant_id"),
            from_status=associated_raw.get("from_status"),
            to_status=associated_raw.get("to_status"),
            extra={
                k: v
                for k, v in associated_raw.items()
                if k
                not in [
                    "source",
                    "ip_address",
                    "user_agent",
                    "job_id",
                    "applicant_id",
                    "from_status",
                    "to_status",
                ]
            },
        )

        # Build User Involved
        user_involved = None
        if row.get("user_id"):
            user_involved = ActivityUserInvolved(
                user_id=row.get("user_id"),
                name=row.get("user_name"),
                email=row.get("user_email"),
                role=row.get("user_role", "User"),
                avatar_url=None,  # Can be extended later
            )

        # Determine status from meta or default
        activity_status = (
            meta.get("status", "Successful") if isinstance(meta, dict) else "Successful"
        )

        return ActivityDetailResponse(
            id=row["id"],
            employer_id=str(row["employer_id"]),
            type=row["type"],
            title=row["title"],
            status=activity_status,
            timestamp=row["timestamp"],
            description=meta.get("description")
            if isinstance(meta, dict)
            else row.get("subtitle"),
            associated_data=associated_data,
            user_involved=user_involved,
            redirect_url=_parse_redirect(meta),
            is_read=row["is_read"],
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to fetch activity detail", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "FAILED_FETCH_ACTIVITY_DETAIL",
                "message": "Failed to fetch activity detail",
            },
        )


# =============================================================================
# MARK AS READ ENDPOINT
# =============================================================================
@actions_router.patch("/{activity_id}/read")
def mark_activity_read(
    activity_id: int,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Tandai aktivitas sebagai sudah dibaca.
    Jika redirect tidak tersedia, balas error ringan (400).
    """
    try:
        row = _fetch_activity_row(activity_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ACTIVITY_NOT_FOUND", "message": "Activity not found"},
            )

        if (
            str(row["employer_id"]) != str(current_user.id)
            and not current_user.is_superuser
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Forbidden"},
            )

        meta = row.get("meta_data") or {}
        redirect_url = _parse_redirect(meta)
        if not redirect_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "REDIRECT_UNAVAILABLE",
                    "message": "Redirect target unavailable",
                },
            )

        updated = activity_log_service.mark_read(activity_id)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "FAILED_MARK_READ",
                    "message": "Failed to mark activity as read",
                },
            )

        return {
            "id": activity_id,
            "is_read": True,
            "redirect_url": redirect_url,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to mark activity as read", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "FAILED_MARK_READ",
                "message": "Failed to mark activity as read",
            },
        )
