
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Request
from typing import Optional, List, Dict
import logging
from decimal import Decimal

from app.schemas.job import JobCreate, JobResponse, JobListResponse, JobUpdate
from app.schemas.application import ApplicationListResponse
from app.services.job_service import JobService
from app.services.application_service import ApplicationService
from app.services.database import get_db_connection
from app.core.security import get_current_user
from app.schemas.user import UserResponse
from app.services.activity_log_service import activity_log_service
from app.schemas.job_performance import JobPerformanceItem, JobPerformanceResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["Jobs (Unified - Integer ID)"])

job_service = JobService()
application_service = ApplicationService()


@router.get(
    "/employers/{employer_id}/job-performance",
    response_model=JobPerformanceResponse,
    summary="Get Job Performance Metrics",
    
)
async def get_job_performance(
    employer_id: int = Path(
        ...,
        description="ID Employer",
        example=8,
    ),
    status: Optional[str] = Query(
        None,
        pattern="^(active|draft|closed)$",
        description="Filter status job",
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
    page: int = Query(1, ge=1, description="Nomor halaman"),
    limit: int = Query(20, ge=1, le=100, description="Jumlah item per halaman"),
    current_user: UserResponse = Depends(get_current_user),
) -> JobPerformanceResponse:
    
    try:
        # Hitung offset
        offset = (page - 1) * limit

        # Ambil data dari database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query untuk mendapatkan total
        count_query = """
        SELECT COUNT(*) as total 
        FROM jobs 
        WHERE created_by = %s
        """
        params = [employer_id]

        if status:
            status_map = {"active": "published", "draft": "draft", "closed": "archived"}
            count_query += " AND status = %s"
            params.append(status_map.get(status, status))

        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]

        # Query untuk mendapatkan data dengan pagination dan sorting
        query = """
        SELECT 
            j.id as job_id,
            j.title as job_title,
            COALESCE(v.views_count, 0) as views_count,
            COALESCE(a.applicants_count, 0) as applicants_count,
            CASE 
                WHEN COALESCE(v.views_count, 0) > 0 
                THEN ROUND((COALESCE(a.applicants_count, 0) * 100.0 / v.views_count), 2)
                ELSE 0 
            END as apply_rate,
            j.status,
            j.updated_at
        FROM jobs j
        LEFT JOIN (
            SELECT job_id, COUNT(*) as views_count
            FROM job_views
            GROUP BY job_id
        ) v ON j.id = v.job_id
        LEFT JOIN (
            SELECT job_id, COUNT(*) as applicants_count
            FROM applications
            WHERE job_id IS NOT NULL
            GROUP BY job_id
        ) a ON j.id = a.job_id
        WHERE j.created_by = %s
        """

        query_params = [employer_id]

        # Tambahkan filter status
        if status:
            query += " AND j.status = %s"
            query_params.append(status_map.get(status, status))

        # Tambahkan sorting
        sort_map = {
            "views": "views_count",
            "applicants": "applicants_count",
            "apply_rate": "apply_rate",
            "status": "status",
        }

        query += f" ORDER BY {sort_map[sort_by]} {order}"

        # Tambahkan pagination
        query += " LIMIT %s OFFSET %s"
        query_params.extend([limit, offset])

        cursor.execute(query, query_params)
        rows = cursor.fetchall()
        cursor.close()

        # Format data response
        items = []
        for row in rows:
            items.append(
                JobPerformanceItem(
                    job_id=str(row["job_id"]),
                    job_title=row["job_title"],
                    views_count=row["views_count"],
                    applicants_count=row["applicants_count"],
                    apply_rate=float(row["apply_rate"]),
                    status=row["status"],
                    updated_at=row["updated_at"],
                )
            )

        # Jika tidak ada data
        message = None
        if total == 0:
            message = "Belum ada job posting untuk employer ini"

        return JobPerformanceResponse(
            items=items,
            page=page,
            limit=limit,
            total=total,
            sort_by=sort_by,
            order=order,
            status_filter=status,
            message=message,
            meta={},
        )

    except Exception as e:
        logger.error(f"Error getting job performance for employer {employer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/",
    response_model=JobListResponse,
    summary="List Job Positions",
    
)
async def get_jobs(
    status: Optional[str] = Query(
        None,
        description="Filter by status (open, closed, draft, published, archived)",
    ),
    department: Optional[str] = Query(
        None,
        description="Filter by department",
    ),
    employment_type: Optional[str] = Query(
        None,
        description="Filter by employment type",
    ),
    location: Optional[str] = Query(
        None,
        description="Filter by location",
    ),
    working_type: Optional[str] = Query(
        None,
        description="Filter by working type (onsite, remote, hybrid)",
    ),
    limit: int = Query(50, ge=1, le=100, description="Jumlah item per halaman"),
    offset: int = Query(0, ge=0, description="Offset untuk pagination"),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get list of job positions dengan semua field dari database"""
    try:
        jobs = job_service.get_jobs(
            status=status, 
            department=department, 
            employment_type=employment_type,
            location=location,
            working_type=working_type,
            limit=limit, 
            offset=offset
        )

        # Get total count for pagination
        conn = get_db_connection()
        cursor = conn.cursor()
        count_query = "SELECT COUNT(*) as total FROM jobs WHERE 1=1"
        params = []

        if status:
            count_query += " AND status = %s"
            params.append(status)

        if department:
            count_query += " AND department = %s"
            params.append(department)

        if employment_type:
            count_query += " AND employment_type = %s"
            params.append(employment_type)

        if location:
            count_query += " AND location ILIKE %s"
            params.append(f"%{location}%")

        if working_type:
            count_query += " AND working_type = %s"
            params.append(working_type)

        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]
        cursor.close()

        return JobListResponse(jobs=jobs, total=total)

    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get Job Details",
    
    responses={
        200: {"description": "Detail job berhasil diambil"},
        404: {"description": "Job tidak ditemukan"},
        500: {"description": "Internal server error"},
    },
)
async def get_job(
    job_id: int = Path(
        ...,
        description="Job ID (Integer)",
        example=1,
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    
    try:
        job = job_service.get_job_by_id(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return job

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/",
    response_model=dict,
    summary="Create Job Position",
    responses={
        200: {"description": "Job berhasil dibuat"},
        400: {"description": "Gagal membuat job"},
        500: {"description": "Internal server error"},
    },
)
async def create_job(
    job_data: JobCreate, current_user: UserResponse = Depends(get_current_user)
):
    
    try:
        job_id = job_service.create_job(job_data, current_user.id)

        if not job_id:
            raise HTTPException(status_code=400, detail="Failed to create job")

        return {"message": "Job created successfully", "job_id": job_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{job_id}",
    response_model=dict,
    summary="Update Job Position",
    
    responses={
        200: {"description": "Job berhasil diupdate"},
        400: {"description": "Tidak ada data untuk diupdate"},
        404: {"description": "Job tidak ditemukan"},
        500: {"description": "Internal server error"},
    },
)
async def update_job(
    request: Request,
    job_id: int = Path(
        ...,
        description="Job ID (Integer)",
        example=1,
    ),
    job_data: JobUpdate = None,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Update posisi pekerjaan dengan semua field.

    Args:
        request: Request object untuk logging.
        job_id: ID job yang akan diupdate.
        job_data: Data yang akan diupdate (semua field optional).
        current_user: User yang melakukan update.

    Returns:
        dict: Message sukses dengan job_id.

    Raises:
        HTTPException: 400 jika tidak ada data.
        HTTPException: 404 jika job tidak ditemukan.
        HTTPException: 500 jika terjadi error.
    """
    try:
        # Get old job data first (untuk check status berubah ke published)
        old_job = job_service.get_job_by_id(job_id)
        old_status = old_job.get("status") if old_job else None

        # Convert Pydantic model to dict (exclude unset fields)
        update_data = job_data.dict(exclude_unset=True) if job_data else {}

        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")

        success = job_service.update_job(job_id, update_data)

        if not success:
            raise HTTPException(
                status_code=404, detail="Job not found or update failed"
            )

        # Log jika status berubah ke published
        new_status = update_data.get("status")
        job_title = update_data.get("title") or old_job.get("title")

        # Log perubahan status job (semua perubahan status)
        if new_status and new_status != old_status:
            if new_status == "published" and old_status != "published":
                # Log published khusus
                activity_log_service.log_job_published(
                    employer_id=current_user.id,
                    job_id=job_id,
                    job_title=job_title,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    role="employer",
                )
                return {"message": "Job published successfully", "job_id": job_id}
            else:
                # Log perubahan status lainnya
                activity_log_service.log_job_status_changed(
                    employer_id=current_user.id,
                    job_id=job_id,
                    job_title=job_title,
                    old_status=old_status,
                    new_status=new_status,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    role="employer",
                )

        return {"message": "Job updated successfully", "job_id": job_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{job_id}",
    response_model=dict,
    summary="Delete Job Position",
    description="""
    Menghapus (soft delete) posisi pekerjaan.
    
    **Format job_id:** Integer (contoh: `1`)
    
    **Catatan:**
    - Job tidak benar-benar dihapus dari database.
    - Status job akan diubah menjadi `closed` atau `archived` (tergantung implementasi).
    - Ini adalah soft delete untuk menjaga data historis.
    - Field lainnya tetap tersimpan di database.
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Job berhasil ditandai sebagai closed"},
        404: {"description": "Job tidak ditemukan"},
        500: {"description": "Internal server error"},
    },
)
async def delete_job(
    job_id: int = Path(
        ...,
        description="Job ID (Integer)",
        example=1,
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Menghapus (soft delete) posisi pekerjaan.

    Args:
        job_id: ID job yang akan dihapus.
        current_user: User yang menghapus job.

    Returns:
        dict: Message sukses dengan job_id.

    Raises:
        HTTPException: 404 jika job tidak ditemukan.
        HTTPException: 500 jika terjadi error.
    """
    try:
        success = job_service.delete_job(job_id)

        if not success:
            raise HTTPException(status_code=404, detail="Job not found")

        return {"message": "Job marked as closed", "job_id": job_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{job_id}/applications",
    response_model=ApplicationListResponse,
    summary="Get Job Applications",
    description="""
    Mendapatkan daftar lamaran untuk job tertentu.
    
    **Format job_id:** Integer (contoh: `1`)
    
    **Query Parameters:**
    - `status`: Filter by status (applied, in_review, qualified, not_qualified)
    - `stage`: Filter by interview stage
    - `search`: Cari berdasarkan nama/email
    - `limit`: Jumlah item per halaman (1-100)
    - `offset`: Offset untuk pagination
    - `sort_by`: Field untuk sorting (default: created_at)
    - `sort_order`: Urutan (asc/desc)
    
    **Data yang Dikembalikan:**
    - `applications`: Array lamaran
    - `total`: Total jumlah lamaran
    - `filters`: Filter yang aktif
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Daftar lamaran berhasil diambil"},
        500: {"description": "Internal server error"},
    },
)
async def get_job_applications(
    job_id: int = Path(
        ...,
        description="Job ID (Integer)",
        example=1,
    ),
    status: Optional[str] = Query(
        None,
        description="Filter by status",
    ),
    stage: Optional[str] = Query(
        None,
        description="Filter by interview stage",
    ),
    search: Optional[str] = Query(
        None,
        description="Search in name/email",
    ),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc/desc"),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Mendapatkan daftar lamaran untuk job tertentu.

    Args:
        job_id: ID job.
        status: Filter by status.
        stage: Filter by interview stage.
        search: Search query.
        limit: Items per page.
        offset: Pagination offset.
        sort_by: Sort field.
        sort_order: Sort order.
        current_user: User yang sedang login.

    Returns:
        ApplicationListResponse: Daftar lamaran dengan pagination.

    Raises:
        HTTPException: 500 jika terjadi error.
    """
    try:
        applications = application_service.get_applications(
            job_id=job_id,
            status=status,
            stage=stage,
            search=search,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Get total count
        conn = get_db_connection()
        cursor = conn.cursor()
        count_query = "SELECT COUNT(*) as total FROM applications WHERE job_id = %s"
        params = [job_id]

        if status:
            count_query += " AND application_status = %s"
            params.append(status)

        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]
        cursor.close()

        return ApplicationListResponse(
            applications=applications,
            total=total,
            filters={
                "job_id": job_id,
                "status": status,
                "stage": stage,
                "search": search,
            },
        )

    except Exception as e:
        logger.error(f"Error getting job applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{job_id}/statistics",
    response_model=dict,
    summary="Get Job Statistics",
    description="""
    Mendapatkan statistik untuk job tertentu.
    
    **Format job_id:** Integer (contoh: `1`)
    
    **Data yang Dikembalikan:**
    - `job`: Detail job dengan semua field
    - `statistics`: Statistik lamaran
      - `total_applications`: Total lamaran
      - `by_status`: Distribusi per status
      - `by_stage`: Distribusi per interview stage
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Statistik job berhasil diambil"},
        404: {"description": "Job tidak ditemukan"},
        500: {"description": "Internal server error"},
    },
)
async def get_job_statistics(
    job_id: int = Path(
        ...,
        description="Job ID (Integer)",
        example=1,
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Mendapatkan statistik untuk job tertentu.

    Args:
        job_id: ID job.
        current_user: User yang sedang login.

    Returns:
        dict: Detail job dan statistik lamaran.

    Raises:
        HTTPException: 404 jika job tidak ditemukan.
        HTTPException: 500 jika terjadi error.
    """
    try:
        # Get job details first
        job = job_service.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get application statistics
        stats = application_service.get_application_statistics(job_id)

        return {"job": job, "statistics": stats}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/statistics/overall",
    response_model=dict,
    summary="Get Overall Statistics",
    description="""
    Mendapatkan statistik keseluruhan job dan lamaran.
    
    **Data yang Dikembalikan:**
    
    **Job Statistics:**
    - `total_jobs`: Total semua job
    - `by_status`: Distribusi job per status
    - `by_department`: Distribusi job per departemen
    - `by_employment_type`: Distribusi per jenis pekerjaan
    - `by_working_type`: Distribusi per jenis kerja (onsite/remote/hybrid)
    - `by_industry`: Distribusi per industri
    
    **Application Statistics:**
    - `total_applications`: Total semua lamaran
    - `by_status`: Distribusi lamaran per status
    - `by_stage`: Distribusi lamaran per interview stage
    
    **Contoh Response:**
    ```json
    {
        "job_statistics": {
            "total_jobs": 25,
            "by_status": {
                "open": 10,
                "published": 8,
                "closed": 5,
                "draft": 2
            },
            "by_department": {
                "Engineering": 10,
                "Marketing": 5,
                "Sales": 4,
                "HR": 3,
                "Other": 3
            },
            "by_working_type": {
                "onsite": 15,
                "hybrid": 7,
                "remote": 3
            }
        },
        "application_statistics": {
            "total_applications": 150,
            "by_status": {
                "applied": 50,
                "in_review": 40,
                "qualified": 30,
                "not_qualified": 20,
                "hired": 10
            }
        }
    }
    ```
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Statistik keseluruhan berhasil diambil"},
        500: {"description": "Internal server error"},
    },
)
async def get_overall_statistics(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Mendapatkan statistik keseluruhan job dan lamaran.

    Args:
        current_user: User yang sedang login.

    Returns:
        dict: Statistik job dan application.

    Raises:
        HTTPException: 500 jika terjadi error.
    """
    try:
        job_stats = job_service.get_job_statistics()
        app_stats = application_service.get_application_statistics()

        return {"job_statistics": job_stats, "application_statistics": app_stats}

    except Exception as e:
        logger.error(f"Error getting overall statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/search/filters",
    response_model=Dict[str, List[str]],
    summary="Get Available Filters",
    description="""
    Mendapatkan daftar filter yang tersedia untuk pencarian job.
    
    **Data yang Dikembalikan:**
    - `departments`: List departemen unik
    - `locations`: List lokasi unik
    - `employment_types`: List jenis pekerjaan unik
    - `working_types`: List jenis kerja unik
    - `industries`: List industri unik
    - `statuses`: List status yang tersedia
    
    **Contoh Response:**
    ```json
    {
        "departments": ["Engineering", "Marketing", "Sales", "HR"],
        "locations": ["Jakarta", "Bandung", "Surabaya", "Remote"],
        "employment_types": ["Full-time", "Part-time", "Contract", "Internship"],
        "working_types": ["onsite", "remote", "hybrid"],
        "industries": ["Technology", "Finance", "Healthcare", "Retail"],
        "statuses": ["draft", "published", "open", "closed", "archived"]
    }
    ```
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Filter tersedia berhasil diambil"},
        500: {"description": "Internal server error"},
    },
)
async def get_available_filters(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Mendapatkan daftar filter yang tersedia.

    Args:
        current_user: User yang sedang login.

    Returns:
        Dict[str, List[str]]: Daftar nilai unik untuk setiap field filter.

    Raises:
        HTTPException: 500 jika terjadi error.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        filters = {}

        # Get unique departments
        cursor.execute("SELECT DISTINCT department FROM jobs WHERE department IS NOT NULL ORDER BY department")
        filters["departments"] = [row["department"] for row in cursor.fetchall()]

        # Get unique locations
        cursor.execute("SELECT DISTINCT location FROM jobs WHERE location IS NOT NULL ORDER BY location")
        filters["locations"] = [row["location"] for row in cursor.fetchall()]

        # Get unique employment types
        cursor.execute("SELECT DISTINCT employment_type FROM jobs WHERE employment_type IS NOT NULL ORDER BY employment_type")
        filters["employment_types"] = [row["employment_type"] for row in cursor.fetchall()]

        # Get unique working types
        cursor.execute("SELECT DISTINCT working_type FROM jobs WHERE working_type IS NOT NULL ORDER BY working_type")
        filters["working_types"] = [row["working_type"] for row in cursor.fetchall()]

        # Get unique industries
        cursor.execute("SELECT DISTINCT industry FROM jobs WHERE industry IS NOT NULL ORDER BY industry")
        filters["industries"] = [row["industry"] for row in cursor.fetchall()]

        # Get unique statuses
        cursor.execute("SELECT DISTINCT status FROM jobs ORDER BY status")
        filters["statuses"] = [row["status"] for row in cursor.fetchall()]

        cursor.close()

        return filters

    except Exception as e:
        logger.error(f"Error getting available filters: {e}")
        raise HTTPException(status_code=500, detail=str(e))