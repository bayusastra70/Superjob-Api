import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.job_posting import JobPosting, JobStatus
from app.schemas.job import JobQualityResponse, JobUpdate
from app.services.job_scoring import compute_quality_score
from app.services.job_suggestions import get_job_suggestions

router = APIRouter(prefix="/jobs", tags=["job-quality"])


REQUIRED_FIELDS = ("title", "description", "salary", "experience_level", "location", "employment_type")
_CACHE_TTL_SECONDS = 300
_quality_cache: Dict[uuid.UUID, tuple[datetime, Dict]] = {}


def _has_minimum_data(job: JobPosting) -> bool:
    has_title = bool(job.title)
    has_desc = bool(job.description)
    has_salary = job.salary_min is not None or job.salary_max is not None
    has_level = bool(job.experience_level)
    has_location = bool(job.location)
    has_employment = bool(job.employment_type)
    return all([has_title, has_desc, has_salary, has_level, has_location, has_employment])


def _is_optimal(job: JobPosting, score: float, suggestions: list[str]) -> bool:
    """
    Optimal definition: score >= 90 and no improvement suggestions remain.
    Suggestions already encode completeness/threshold checks (desc length, skills count, etc).
    """
    return score >= 90 and len(suggestions) == 0


def _get_cached(job_id: uuid.UUID) -> Optional[Dict]:
    now = datetime.now(timezone.utc)
    cached = _quality_cache.get(job_id)
    if not cached:
        return None
    expires_at, payload = cached
    if expires_at < now:
        _quality_cache.pop(job_id, None)
        return None
    return payload


def _set_cache(job_id: uuid.UUID, payload: Dict) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=_CACHE_TTL_SECONDS)
    _quality_cache[job_id] = (expires_at, payload)


def clear_job_score_cache() -> None:
    _quality_cache.clear()


def invalidate_job_cache(job_id: uuid.UUID) -> None:
    _quality_cache.pop(job_id, None)


@router.get("/{job_id}/quality-score", response_model=JobQualityResponse)
async def get_job_quality_score(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> JobQualityResponse:
    cached = _get_cached(job_id)
    if cached:
        return cached

    job = await db.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    suggestions = get_job_suggestions(job)

    # Draft job returns null score/grade.
    if job.status == JobStatus.draft:
        response = JobQualityResponse(
            job_id=job.id,
            score=None,
            grade=None,
            optimal=False,
            details=None,
            message="Job masih draft; skor tidak dihitung",
            suggestions=suggestions,
        )
        _set_cache(job.id, response.model_dump())
        return response

    if not _has_minimum_data(job):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Data tidak cukup untuk menilai postingan",
                "suggestions": suggestions,
            },
        )

    try:
        result = compute_quality_score(job)
    except Exception as exc:
        logger.exception("Failed to compute job quality score", job_id=str(job_id), exc=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal menghitung skor",
        )

    response = JobQualityResponse(
        job_id=job.id,
        score=result.score,
        grade=result.grade,
        optimal=_is_optimal(job, result.score, suggestions),
        details=result.details,
        suggestions=suggestions,
    )
    _set_cache(job.id, response.model_dump())
    return response


@router.patch("/{job_id}", response_model=JobQualityResponse)
async def update_job_fields(
    job_id: uuid.UUID,
    payload: JobUpdate,
    db: AsyncSession = Depends(get_db),
) -> JobQualityResponse:
    job = await db.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    try:
        await db.commit()
        await db.refresh(job)
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to update job", job_id=str(job_id), exc=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job",
        )

    # invalidate cache after mutation
    invalidate_job_cache(job.id)

    # return fresh quality score + suggestions
    suggestions = get_job_suggestions(job)

    if job.status == JobStatus.draft:
        response = JobQualityResponse(
            job_id=job.id,
            score=None,
            grade=None,
            optimal=False,
            details=None,
            message="Job masih draft; skor tidak dihitung",
            suggestions=suggestions,
        )
        _set_cache(job.id, response.model_dump())
        return response

    if not _has_minimum_data(job):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Data tidak cukup untuk menilai postingan",
                "suggestions": suggestions,
            },
        )

    result = compute_quality_score(job)
    response = JobQualityResponse(
        job_id=job.id,
        score=result.score,
        grade=result.grade,
        optimal=_is_optimal(job, result.score, suggestions),
        details=result.details,
        suggestions=suggestions,
    )
    _set_cache(job.id, response.model_dump())
    return response
