from fastapi import APIRouter, HTTPException, Depends, Query, Path, Request
from typing import Optional
import logging

from app.schemas.job import JobCreate, JobResponse, JobListResponse
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
    description="""
    Mendapatkan metrik performa semua lowongan kerja milik employer.
    
    **⚠️ UPDATE (2025-12-22):** Table `job_postings` telah dikonsolidasikan ke `jobs`.
    Semua job menggunakan **Integer ID**.
    
    **Format employer_id:** Integer (contoh: `8`)
    
    **Query Parameters:**
    - `status`: Filter berdasarkan status (active, draft, closed, published, archived)
    - `sort_by`: Field untuk sorting (views, applicants, apply_rate, status)
    - `order`: Urutan sorting (asc, desc)
    - `page`: Halaman (1-based)
    - `limit`: Jumlah item per halaman (1-100)
    
    **Test Data:**
    - employer_id `8` - punya beberapa jobs (termasuk ex-job_postings)
    - employer_id `3` - punya beberapa jobs
    """,
    responses={
        200: {"description": "Metrik performa berhasil diambil"},
        404: {"description": "Employer tidak ditemukan"},
        500: {"description": "Internal server error"},
    },
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
    """
    Mendapatkan daftar metrik performa lowongan kerja.

    Args:
        employer_id: ID employer untuk filter data.
        status: Filter status lowongan.
        sort_by: Field untuk sorting.
        order: Urutan sorting (asc/desc).
        page: Nomor halaman (1-based).
        limit: Jumlah item per halaman.
        current_user: User yang sedang login.

    Returns:
        JobPerformanceResponse: Daftar metrik performa dengan pagination info.
    """
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
    description="""
    Mendapatkan daftar posisi pekerjaan dari tabel `jobs`.
    
    **⚠️ Catatan:** Endpoint ini menggunakan tabel `jobs` dengan ID **Integer**.
    Untuk job postings dengan UUID, gunakan `/employers/{employer_id}/jobs`.
    
    **Status yang valid:** open, closed, draft
    
    **Test Data:**
    - job_id `1` - Software Engineer
    - job_id `2` - Data Analyst
    - job_id `3` - Product Manager
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
)
async def get_jobs(
    status: Optional[str] = Query(
        None,
        description="Filter by status (open, closed, draft)",
    ),
    department: Optional[str] = Query(
        None,
        description="Filter by department",
    ),
    limit: int = Query(50, ge=1, le=100, description="Jumlah item per halaman"),
    offset: int = Query(0, ge=0, description="Offset untuk pagination"),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get list of job positions"""
    try:
        jobs = job_service.get_jobs(status, department, limit, offset)

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
    description="""
    Mendapatkan detail posisi pekerjaan berdasarkan ID.
    
    **Format job_id:** Integer (contoh: `1`)
    
    **Data yang Dikembalikan:**
    - `id`: ID job
    - `title`: Judul posisi
    - `description`: Deskripsi pekerjaan
    - `department`: Departemen
    - `location`: Lokasi
    - `salary_min`, `salary_max`: Range gaji
    - `status`: Status (open, closed, draft)
    - `requirements`: Persyaratan
    - `created_at`, `updated_at`: Timestamps
    
    **Test Data:**
    - job_id `1` - Software Engineer
    - job_id `2` - Data Analyst
    - job_id `3` - Product Manager
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
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
    """
    Mendapatkan detail posisi pekerjaan berdasarkan ID.

    Args:
        job_id: ID job yang ingin diambil.
        current_user: User yang sedang login.

    Returns:
        JobResponse: Detail posisi pekerjaan.

    Raises:
        HTTPException: 404 jika job tidak ditemukan.
        HTTPException: 500 jika terjadi error.
    """
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
    description="""
    Membuat posisi pekerjaan baru.
    
    **Request Body:**
    - `title` (required): Judul posisi
    - `description` (optional): Deskripsi pekerjaan
    - `department` (optional): Departemen
    - `location` (optional): Lokasi
    - `salary_min`, `salary_max` (optional): Range gaji
    - `status` (optional): Status awal (default: draft)
    - `requirements` (optional): Persyaratan
    
    **Contoh Request Body:**
    ```json
    {
        "title": "Senior Software Engineer",
        "description": "Mengembangkan aplikasi web...",
        "department": "Engineering",
        "location": "Jakarta",
        "salary_min": 15000000,
        "salary_max": 25000000,
        "status": "draft"
    }
    ```
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Job berhasil dibuat"},
        400: {"description": "Gagal membuat job"},
        500: {"description": "Internal server error"},
    },
)
async def create_job(
    job_data: JobCreate, current_user: UserResponse = Depends(get_current_user)
):
    """
    Membuat posisi pekerjaan baru.

    Args:
        job_data: Data job yang akan dibuat.
        current_user: User yang membuat job.

    Returns:
        dict: Message sukses dengan job_id.

    Raises:
        HTTPException: 400 jika gagal membuat job.
        HTTPException: 500 jika terjadi error.
    """
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
    description="""
    Update posisi pekerjaan.
    
    **Format job_id:** Integer (contoh: `1`)
    
    **Request Body (partial update):**
    - `title`: Judul posisi
    - `description`: Deskripsi pekerjaan
    - `department`: Departemen
    - `location`: Lokasi
    - `salary_min`, `salary_max`: Range gaji
    - `status`: Status (draft, open, closed, published)
    - `requirements`: Persyaratan
    
    **Contoh - Publish Job:**
    ```json
    {
        "status": "published"
    }
    ```
    
    **Contoh - Update Details:**
    ```json
    {
        "title": "Senior Software Engineer",
        "salary_max": 30000000
    }
    ```
    
    **⚠️ Membutuhkan Authorization Token!**
    
    **Catatan:**
    - Activity log dicatat saat status berubah.
    - Publish job akan membuat log khusus.
    """,
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
    job_data: JobCreate = None,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Update posisi pekerjaan.

    Args:
        request: Request object untuk logging.
        job_id: ID job yang akan diupdate.
        job_data: Data yang akan diupdate.
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
    - Status job akan diubah menjadi `closed`.
    - Ini adalah soft delete untuk menjaga data historis.
    
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
    - `job`: Detail job
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
                "open": 15,
                "closed": 8,
                "draft": 2
            }
        },
        "application_statistics": {
            "total_applications": 150,
            "by_status": {
                "applied": 50,
                "in_review": 40,
                "qualified": 30
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
