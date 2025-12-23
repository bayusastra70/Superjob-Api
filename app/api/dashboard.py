import uuid
from datetime import datetime
from typing import Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from loguru import logger
from sqlalchemy import text, select, func
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.job import JobStatus, Job
from app.schemas.dashboard import (
    QuickActionsBadges,
    QuickActionsMetrics,
    QuickActionsResponse,
    MarkSeenRequest,
)
from app.services.dashboard_state import mark_seen_items, reset_badges
from app.schemas.dashboard import (
    QuickActionsBadges,
    QuickActionsMetrics,
    QuickActionsResponse,
    MarkSeenRequest,
)
from fastapi import Body

router = APIRouter(
    prefix="/employers/{employer_id}/dashboard", tags=["Dashboard Metrics"]
)


async def _safe_count(db: AsyncSession, query: str, params: dict) -> int:
    try:
        result = await db.execute(text(query), params)
        row = result.scalar_one()
        return int(row or 0)
    except (ProgrammingError, SQLAlchemyError) as exc:
        logger.warning("Count query failed, returning 0", exc=exc, query=query)
        return 0


async def _get_seen_times(db: AsyncSession, employer_id: int) -> Dict[str, datetime]:
    try:
        result = await db.execute(
            text(
                """
                SELECT item_key, seen_at FROM dashboard_seen
                WHERE employer_id = :employer_id
                """
            ),
            {"employer_id": str(employer_id)},
        )
        rows = result.fetchall()
        return {row[0]: row[1] for row in rows if row[0] and row[1]}
    except Exception:
        return {}


@router.get(
    "/quick-actions",
    response_model=QuickActionsResponse,
    summary="Get Quick Actions Metrics",
    description="""
    Mendapatkan metrik quick actions untuk dashboard employer.
    
    **Format employer_id:** Integer (contoh: `8`)
    
    **Metrics yang dikembalikan:**
    - `active_jobs`: Jumlah lowongan aktif
    - `new_applicants`: Jumlah pelamar baru
    - `unread_messages`: Jumlah pesan belum dibaca
    - `pending_reminders`: Jumlah reminder pending
    
    **Test Data:**
    - employer_id `8` (employer@superjob.com)
    - employer_id `3` (tanaka@gmail.com)
    """,
)
async def get_quick_actions_metrics(
    employer_id: int = Path(
        ...,
        description="ID Employer. Contoh: 8",
        example=8,
    ),
    last_viewed_applicant_at: Optional[datetime] = Query(
        None,
        description="Timestamp terakhir melihat applicants (ISO format)",
    ),
    last_viewed_job_post_at: Optional[datetime] = Query(
        None,
        description="Timestamp terakhir melihat job posts (ISO format)",
    ),
    db: AsyncSession = Depends(get_db),
) -> QuickActionsResponse:
    seen_times = await _get_seen_times(db, employer_id)
    applicant_cutoff = last_viewed_applicant_at or seen_times.get("newApplicants")
    job_cutoff = last_viewed_job_post_at or seen_times.get("newJobPosts")
    # Active jobs
    try:
        active_jobs = await db.scalar(
            select(func.count())
            .select_from(Job)
            .where(
                Job.employer_id == employer_id,
                Job.status == JobStatus.published.value,
            )
        )
    except Exception as exc:
        logger.warning("Active job count failed, returning 0", exc=exc)
        active_jobs = 0

    # Total applicants (table may not exist yet; safe fallback)
    total_applicants = await _safe_count(
        db,
        """
        SELECT COUNT(*) FROM applicants
        WHERE employer_id = :employer_id
        """,
        {"employer_id": employer_id},
    )

    # New applicants: created after last viewed or unbounded if null
    new_applicants = await _safe_count(
        db,
        """
        SELECT COUNT(*) FROM applicants
        WHERE employer_id = :employer_id
          AND status = 'applied'
          AND (:applicant_cutoff IS NULL OR created_at > :applicant_cutoff)
        """,
        {"employer_id": employer_id, "applicant_cutoff": applicant_cutoff},
    )

    # New messages: unread
    new_messages = await _safe_count(
        db,
        """
        SELECT COUNT(*) FROM messages
        WHERE employer_id = :employer_id
          AND is_read = false
        """,
        {"employer_id": employer_id},
    )

    # New job posts: created after last viewed
    try:
        conds = [
            Job.employer_id == employer_id,
            Job.status == JobStatus.published.value,
        ]
        if job_cutoff:
            conds.append(Job.created_at > job_cutoff)
        new_job_posts = await db.scalar(
            select(func.count()).select_from(Job).where(*conds)
        )
    except Exception as exc:
        logger.warning("New job posts count failed, returning 0", exc=exc)
        new_job_posts = 0

    metrics = QuickActionsMetrics(
        activeJobPosts=active_jobs,
        totalApplicants=total_applicants,
        newApplicants=new_applicants,
        newMessages=new_messages,
        newJobPosts=new_job_posts,
    )
    badges = QuickActionsBadges(
        newApplicants=new_applicants > 0,
        newMessages=new_messages > 0,
        newJobPosts=new_job_posts > 0,
    )

    return QuickActionsResponse(
        employer_id=employer_id,
        metrics=metrics,
        badges=badges,
        lookback_start_applicants=applicant_cutoff,
        lookback_start_job_posts=job_cutoff,
    )


@router.post(
    "/metrics/mark-seen",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark Metrics as Seen",
    description="""
    Menandai item dashboard tertentu sebagai sudah dilihat oleh employer.
    
    **Tujuan:**
    Endpoint ini digunakan untuk memperbarui timestamp "terakhir dilihat" 
    untuk berbagai metrik dashboard, sehingga badge notifikasi dapat di-reset.
    
    **Request Body:**
    - `items`: List string nama metrik yang ingin ditandai sebagai seen.
      - Nilai yang valid: `"newApplicants"`, `"newMessages"`, `"newJobPosts"`
    
    **Contoh Request Body:**
    ```json
    {
        "items": ["newApplicants", "newMessages"]
    }
    ```
    
    **Response:**
    - `204 No Content`: Berhasil menandai item sebagai seen.
    - `500 Internal Server Error`: Gagal memproses request.
    
    **Catatan:**
    - Setelah item ditandai sebagai seen, badge count akan di-reset pada request selanjutnya.
    - Timestamp seen disimpan di tabel `dashboard_seen`.
    """,
    responses={
        204: {"description": "Item berhasil ditandai sebagai seen"},
        500: {"description": "Internal server error saat memproses request"},
    },
)
async def mark_seen(
    employer_id: int = Path(
        ...,
        description="ID Employer yang ingin menandai item sebagai seen",
        example=8,
    ),
    payload: MarkSeenRequest = Body(
        ...,
        description="Request body berisi list item yang ingin ditandai sebagai seen",
        examples=[
            {
                "summary": "Mark single item",
                "value": {"items": ["newApplicants"]},
            },
            {
                "summary": "Mark multiple items",
                "value": {"items": ["newApplicants", "newMessages", "newJobPosts"]},
            },
        ],
    ),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Menandai item dashboard sebagai sudah dilihat.

    Args:
        employer_id: ID employer yang melakukan request.
        payload: Request body berisi list item yang ingin ditandai.
        db: Database session.

    Raises:
        HTTPException: 500 jika gagal memproses request.
    """
    try:
        await mark_seen_items(db, employer_id, payload.items)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "Failed to mark metrics as seen", exc=exc, employer_id=str(employer_id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark items as seen",
        )


@router.patch(
    "/reset-badges",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset Dashboard Badges",
    description="""
    Mereset badge notifikasi pada dashboard employer.
    
    **Tujuan:**
    Endpoint ini digunakan untuk mereset badge notifikasi ke 0 (false)
    tanpa harus mengupdate timestamp seen. Berguna ketika user ingin
    menghilangkan badge tanpa perlu load data detailnya.
    
    **Request Body:**
    - `items`: List string nama badge yang ingin di-reset.
      - Nilai yang valid: `"newApplicants"`, `"newMessages"`, `"newJobPosts"`
    
    **Contoh Request Body:**
    ```json
    {
        "items": ["newApplicants"]
    }
    ```
    
    **Response:**
    - `204 No Content`: Berhasil mereset badges.
    - `500 Internal Server Error`: Gagal memproses request.
    
    **Perbedaan dengan mark-seen:**
    - `mark-seen`: Memperbarui timestamp terakhir dilihat, badge akan reset berdasarkan waktu.
    - `reset-badges`: Langsung mereset badge ke false tanpa mengubah timestamp.
    """,
    responses={
        204: {"description": "Badge berhasil di-reset"},
        500: {"description": "Internal server error saat memproses request"},
    },
)
async def reset_badges_endpoint(
    employer_id: int = Path(
        ...,
        description="ID Employer yang ingin mereset badges",
        example=8,
    ),
    payload: MarkSeenRequest = Body(
        ...,
        description="Request body berisi list badge yang ingin di-reset",
        examples=[
            {
                "summary": "Reset single badge",
                "value": {"items": ["newApplicants"]},
            },
            {
                "summary": "Reset all badges",
                "value": {"items": ["newApplicants", "newMessages", "newJobPosts"]},
            },
        ],
    ),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Mereset badge notifikasi dashboard.

    Args:
        employer_id: ID employer yang melakukan request.
        payload: Request body berisi list badge yang ingin di-reset.
        db: Database session.

    Raises:
        HTTPException: 500 jika gagal memproses request.
    """
    try:
        await reset_badges(db, employer_id, payload.items)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "Failed to reset badges", exc=exc, employer_id=str(employer_id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset badges",
        )
