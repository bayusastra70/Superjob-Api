import logging
from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.schemas.activity import Activity, ActivityListResponse
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


@router.get("", response_model=ActivityListResponse)
def list_activities(
    employer_id: str,
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    activity_type: str | None = Query(None, description="Filter by activity type"),
    role: str | None = Query(
        None,
        description="Filter by user role (from meta_data.role or meta_data.user_role)",
    ),
    start_date: str | None = Query(None, description="Start date ISO (inclusive)"),
    end_date: str | None = Query(None, description="End date ISO (inclusive)"),
    search: str | None = Query(None, description="Search in title/subtitle/meta"),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Ambil daftar aktivitas/notifikasi terbaru untuk employer.
    Default urut terbaru (timestamp DESC).
    """
    # Simple guard: hanya boleh akses milik sendiri atau superuser
    if str(current_user.id) != str(employer_id) and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    offset = (page - 1) * limit

    try:
        # Validate dates early
        if start_date:
            try:
                datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_DATE",
                        "message": "Invalid start_date format",
                    },
                )

        if end_date:
            try:
                datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_DATE",
                        "message": "Invalid end_date format",
                    },
                )

        rows, total = activity_log_service.list_activities(
            employer_id=str(employer_id),
            limit=limit,
            offset=offset,
            activity_type=activity_type,
            role=role,
            start_date=start_date,
            end_date=end_date,
            search=search,
        )

        items: List[Activity] = []
        for row in rows:
            meta = row.get("meta_data") or {}
            redirect_url = _parse_redirect(meta)
            items.append(
                Activity(
                    id=row["id"],
                    employer_id=str(row["employer_id"]),
                    type=row["type"],
                    title=row["title"],
                    subtitle=row.get("subtitle"),
                    meta_data=meta if isinstance(meta, dict) else {},
                    job_id=str(row["job_id"]) if row.get("job_id") else None,
                    applicant_id=row.get("applicant_id"),
                    message_id=str(row["message_id"])
                    if row.get("message_id")
                    else None,
                    timestamp=row["timestamp"],
                    is_read=row["is_read"],
                    redirect_url=redirect_url,
                    user_name=row.get("user_name"),
                )
            )

        # Jika kosong, tetap kembalikan 200 dengan list kosong agar FE bisa render placeholder
        if total == 0:
            return ActivityListResponse(items=[], page=page, limit=limit, total=0)

        return ActivityListResponse(items=items, page=page, limit=limit, total=total)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to fetch activities", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "FAILED_FETCH_ACTIVITIES",
                "message": "Failed to fetch activities",
            },
        )


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
