from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status as http_status,
)
from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.job_posting import JobStatus
from app.schemas.job_performance import JobPerformanceItem, JobPerformanceResponse

router = APIRouter(
    prefix="/employers/{employer_id}/job-performance", tags=["job-performance"]
)

SORT_MAP = {
    "views": "views_count",
    "applicants": "applicants_count",
    "apply_rate": "apply_rate",
    "status": "status",
}

STATUS_MAP = {
    "active": JobStatus.published.value,
    "draft": JobStatus.draft.value,
    "closed": JobStatus.archived.value,
}


async def _fetch_metrics(
    db: AsyncSession,
    employer_id: int,
    status_filter: Optional[str],
    sort_by: str,
    order: str,
    limit: int,
    offset: int,
):
    base_status_clause = ""
    params = {
        "employer_id": employer_id,
        "limit": limit,
        "offset": offset,
    }
    if status_filter:
        base_status_clause = "AND jp.status = :status_filter"
        params["status_filter"] = STATUS_MAP[status_filter]

    # Note: job_views and applications tables reference jobs.id (Integer),
    # but job_postings.id is String(36). These can't be directly joined.
    # For now, we return job_postings data without views/applicants stats.
    # TODO: Either migrate data or update schema to use consistent IDs.
    sql = f"""
    SELECT
        jp.id AS job_id,
        COALESCE(jp.title, '') AS job_title,
        0 AS views_count,
        0 AS applicants_count,
        0.00 AS apply_rate,
        jp.status AS status,
        jp.updated_at AS updated_at
    FROM job_postings jp
    WHERE jp.employer_id = :employer_id
    {base_status_clause}
    ORDER BY {SORT_MAP[sort_by]} {order.upper()}
    LIMIT :limit OFFSET :offset
    """
    return await db.execute(text(sql), params)


async def _fetch_total(
    db: AsyncSession, employer_id: int, status_filter: Optional[str]
) -> int:
    params = {"employer_id": employer_id}
    clause = ""
    if status_filter:
        clause = "AND status = :status_filter"
        params["status_filter"] = STATUS_MAP[status_filter]
    result = await db.execute(
        text(
            f"""
            SELECT COUNT(*) FROM job_postings
            WHERE employer_id = :employer_id
            {clause}
            """
        ),
        params,
    )
    return int(result.scalar_one() or 0)


@router.get(
    "",
    response_model=JobPerformanceResponse,
    summary="List Job Performance Metrics",
    description="""
    Mendapatkan metrik performa semua lowongan kerja milik employer.
    
    **Format employer_id:** Integer (contoh: `8`)
    
    **Query Parameters:**
    - `sort_by`: Field untuk sorting (views, applicants, apply_rate, status)
    - `order`: Urutan sorting (asc, desc)
    - `status`: Filter berdasarkan status (active, draft, closed)
    - `page`: Halaman (1-based)
    - `limit`: Jumlah item per halaman (1-100)
    
    **Test Data yang tersedia:**
    - employer_id `8` (employer@superjob.com) - punya 4 job postings
    - employer_id `3` (tanaka@gmail.com) - punya 2 job postings
    
    **Catatan:** Views dan applicants saat ini return 0 karena belum ada data.
    """,
)
async def list_job_performance(
    employer_id: int = Path(
        ...,
        description="ID Employer. Contoh: 8 (employer@superjob.com)",
        example=8,
    ),
    sort_by: str = Query(
        "views",
        pattern="^(views|applicants|apply_rate|status)$",
        description="Field untuk sorting",
    ),
    order: str = Query(
        "desc",
        pattern="^(asc|desc)$",
        description="Urutan sorting",
    ),
    status: Optional[str] = Query(
        None,
        pattern="^(active|draft|closed)$",
        description="Filter berdasarkan status job",
    ),
    page: int = Query(1, ge=1, description="Nomor halaman"),
    limit: int = Query(20, ge=1, le=100, description="Jumlah item per halaman"),
    db: AsyncSession = Depends(get_db),
) -> JobPerformanceResponse:
    offset = (page - 1) * limit

    try:
        total = await _fetch_total(db, employer_id, status)
        result = await _fetch_metrics(
            db, employer_id, status, sort_by, order, limit, offset
        )
        rows = result.mappings().all()
    except SQLAlchemyError as exc:
        logger.exception(
            "Failed to fetch job performance", exc=exc, employer_id=str(employer_id)
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch job performance",
        )
    except Exception:
        # When tables like job_views/applications don't exist, return empty safely.
        logger.warning(
            "Job performance query failed, returning empty",
            employer_id=str(employer_id),
        )
        total = 0
        rows = []

    items = [
        JobPerformanceItem(
            job_id=row["job_id"],
            job_title=row["job_title"],
            views_count=row["views_count"],
            applicants_count=row["applicants_count"],
            apply_rate=float(row["apply_rate"]),
            status=row["status"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]

    return JobPerformanceResponse(
        items=items,
        page=page,
        limit=limit,
        total=total,
        sort_by=sort_by,
        order=order,
        status_filter=status,
        message="Belum ada job posting" if total == 0 else None,
        meta={},
    )
