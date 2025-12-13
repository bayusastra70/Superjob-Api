import uuid
from datetime import datetime
from typing import Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import text, select, func
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.job_posting import JobStatus, JobPosting
from app.schemas.dashboard import QuickActionsBadges, QuickActionsMetrics, QuickActionsResponse, MarkSeenRequest
from app.services.dashboard_state import mark_seen_items, reset_badges
from app.schemas.dashboard import QuickActionsBadges, QuickActionsMetrics, QuickActionsResponse, MarkSeenRequest
from fastapi import Body

router = APIRouter(prefix="/employers/{employer_id}/dashboard", tags=["dashboard-metrics"])


async def _safe_count(db: AsyncSession, query: str, params: dict) -> int:
    try:
        result = await db.execute(text(query), params)
        row = result.scalar_one()
        return int(row or 0)
    except (ProgrammingError, SQLAlchemyError) as exc:
        logger.warning("Count query failed, returning 0", exc=exc, query=query)
        return 0


async def _get_seen_times(db: AsyncSession, employer_id: uuid.UUID) -> Dict[str, datetime]:
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


@router.get("/quick-actions", response_model=QuickActionsResponse)
async def get_quick_actions_metrics(
    employer_id: uuid.UUID,
    last_viewed_applicant_at: Optional[datetime] = Query(None),
    last_viewed_job_post_at: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> QuickActionsResponse:
    seen_times = await _get_seen_times(db, employer_id)
    applicant_cutoff = last_viewed_applicant_at or seen_times.get("newApplicants")
    job_cutoff = last_viewed_job_post_at or seen_times.get("newJobPosts")
    # Active jobs
    try:
        active_jobs = await db.scalar(
            select(func.count()).select_from(JobPosting).where(
                JobPosting.employer_id == employer_id,
                JobPosting.status == JobStatus.published,
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
            JobPosting.employer_id == employer_id,
            JobPosting.status == JobStatus.published,
        ]
        if job_cutoff:
            conds.append(JobPosting.created_at > job_cutoff)
        new_job_posts = await db.scalar(select(func.count()).select_from(JobPosting).where(*conds))
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


@router.post("/metrics/mark-seen", status_code=status.HTTP_204_NO_CONTENT)
async def mark_seen(
    employer_id: uuid.UUID,
    payload: MarkSeenRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await mark_seen_items(db, employer_id, payload.items)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to mark metrics as seen", exc=exc, employer_id=str(employer_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark items as seen",
        )


@router.patch("/reset-badges", status_code=status.HTTP_204_NO_CONTENT)
async def reset_badges_endpoint(
    employer_id: uuid.UUID,
    payload: MarkSeenRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await reset_badges(db, employer_id, payload.items)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to reset badges", exc=exc, employer_id=str(employer_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset badges",
        )
