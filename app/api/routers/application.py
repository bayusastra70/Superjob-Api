from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, Request
from typing import List, Optional
import logging

from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationStatus,
    InterviewStage,
)
from app.services.application_service import ApplicationService
from app.core.security import get_current_user
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/applications", tags=["Applications"])

application_service = ApplicationService()


@router.get(
    "/",
    response_model=ApplicationListResponse,
    summary="List Applications",
    description="""
    Mendapatkan daftar lamaran pekerjaan.
    
    **Status yang valid:**
    - `applied` - Baru melamar
    - `in_review` - Sedang direview
    - `qualified` - Lolos kualifikasi
    - `not_qualified` - Tidak lolos
    - `contract_signed` - Kontrak ditandatangani
    
    **Interview Stages:**
    - `first_interview` - Interview pertama
    - `second_interview` - Interview kedua
    - `contract_proposal` - Proposal kontrak
    - `contract_signed` - Kontrak ditandatangani
    
    **Test Data:**
    - application_id `1` - `5` (dari seed data)
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
)
async def get_applications(
    job_id: Optional[int] = Query(
        None,
        description="Filter by job ID (Integer)",
        example=1,
    ),
    status: Optional[str] = Query(
        None,
        description="Filter by status (applied, in_review, qualified, not_qualified, contract_signed)",
    ),
    stage: Optional[str] = Query(
        None,
        description="Filter by interview stage",
    ),
    search: Optional[str] = Query(
        None,
        description="Cari berdasarkan nama/email",
    ),
    limit: int = Query(50, ge=1, le=100, description="Jumlah item per halaman"),
    offset: int = Query(0, ge=0, description="Offset untuk pagination"),
    sort_by: str = Query("created_at", description="Field untuk sorting"),
    sort_order: str = Query("desc", description="Urutan: asc atau desc"),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get list of applications with filters"""
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
        from app.services.database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor()

        count_query = "SELECT COUNT(*) as total FROM applications WHERE 1=1"
        params = []

        if job_id:
            count_query += " AND job_id = %s"
            params.append(job_id)

        if status:
            count_query += " AND application_status = %s"
            params.append(status)

        if stage:
            count_query += " AND interview_stage = %s"
            params.append(stage)

        if search:
            count_query += " AND (candidate_name ILIKE %s OR candidate_email ILIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

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
        logger.error(f"Error getting applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Get Application Details",
    description="""
    Mendapatkan detail lengkap lamaran berdasarkan ID.
    
    **Format application_id:** Integer (contoh: `1`)
    
    **Data yang Dikembalikan:**
    - `id`: ID lamaran
    - `job_id`: ID lowongan yang dilamar
    - `candidate_name`: Nama kandidat
    - `candidate_email`: Email kandidat
    - `application_status`: Status lamaran
    - `interview_stage`: Tahap interview saat ini
    - `fit_score`, `skill_score`, `experience_score`: Skor penilaian
    - `applied_date`: Tanggal melamar
    - `interview_date`: Jadwal interview (jika ada)
    
    **Test Data:**
    - application_id `1` - `5` (dari seed data)
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Detail lamaran berhasil diambil"},
        404: {"description": "Lamaran tidak ditemukan"},
        500: {"description": "Internal server error"},
    },
)
async def get_application(
    application_id: int = Path(
        ...,
        description="Application ID (Integer)",
        example=1,
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Mengambil detail lengkap lamaran berdasarkan ID.

    Args:
        application_id: ID lamaran yang ingin diambil.
        current_user: User yang sedang login.

    Returns:
        ApplicationResponse: Detail lamaran.

    Raises:
        HTTPException: 404 jika lamaran tidak ditemukan.
        HTTPException: 500 jika terjadi error.
    """
    try:
        application = application_service.get_application_by_id(application_id)

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        return application

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application {application_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/",
    response_model=dict,
    summary="Create Application",
    description="""
    Membuat lamaran pekerjaan baru.
    
    **Tujuan:**
    Endpoint ini digunakan oleh kandidat untuk melamar pekerjaan.
    User yang sedang login akan otomatis menjadi pelamar.
    
    **Request Body:**
    - `job_id` (required): ID lowongan yang dilamar
    - `cover_letter` (optional): Surat lamaran
    - `resume_url` (optional): URL resume/CV
    - `expected_salary` (optional): Gaji yang diharapkan
    
    **Contoh Request Body:**
    ```json
    {
        "job_id": 1,
        "cover_letter": "Saya tertarik dengan posisi ini...",
        "resume_url": "https://example.com/resume.pdf"
    }
    ```
    
    **Response:**
    - `201 Created`: Lamaran berhasil dibuat
    - `400 Bad Request`: Gagal membuat lamaran
    - `500 Internal Server Error`: Terjadi error
    
    **⚠️ Membutuhkan Authorization Token!**
    
    **Catatan:**
    - Setiap lamaran akan dilog untuk audit trail.
    - Status awal lamaran adalah `applied`.
    """,
    responses={
        200: {"description": "Lamaran berhasil dibuat"},
        400: {"description": "Gagal membuat lamaran"},
        500: {"description": "Internal server error"},
    },
)
async def create_application(
    request: Request,
    application_data: ApplicationCreate,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Membuat lamaran pekerjaan baru.

    Args:
        request: Request object untuk mendapatkan IP dan user agent.
        application_data: Data lamaran yang akan dibuat.
        current_user: User yang sedang login (akan menjadi pelamar).

    Returns:
        dict: Message sukses dengan application_id.

    Raises:
        HTTPException: 400 jika gagal membuat lamaran.
        HTTPException: 500 jika terjadi error.
    """
    try:
        # For candidates applying, use their own ID
        # For employers adding candidates, they would specify candidate_id differently
        # Here we assume candidate is creating their own application
        application_id = application_service.create_application(
            application_data,
            candidate_id=current_user.id,
            actor_role=getattr(current_user, "role", None),
            actor_ip=request.client.host,
            actor_user_agent=request.headers.get("user-agent"),
        )

        if not application_id:
            raise HTTPException(status_code=400, detail="Failed to create application")

        return {
            "message": "Application created successfully",
            "application_id": application_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{application_id}/status",
    response_model=dict,
    summary="Update Application Status",
    description="""
    Update status dan/atau interview stage dari lamaran.
    
    **Format application_id:** Integer (contoh: `2`)
    
    **Status yang valid:**
    - `applied` - Baru melamar
    - `in_review` - Sedang direview
    - `qualified` - Lolos kualifikasi
    - `not_qualified` - Tidak lolos
    - `contract_signed` - Kontrak ditandatangani
    
    **Interview Stages yang valid:**
    - `first_interview` - Interview pertama
    - `second_interview` - Interview kedua
    - `contract_proposal` - Proposal kontrak
    - `contract_signed` - Kontrak ditandatangani
    
    **Test Data:**
    ```json
    {
        "new_status": "qualified",
        "new_stage": "first_interview",
        "reason": "Kandidat lolos screening awal"
    }
    ```
    
    **⚠️ Endpoint ini akan membuat Activity Log otomatis!**
    """,
)
async def update_application_status(
    request: Request,
    application_id: int = Path(
        ...,
        description="Application ID (Integer). Contoh: 2",
        example=2,
    ),
    new_status: str = Body(
        ...,
        embed=True,
        description="Status baru (applied, in_review, qualified, not_qualified, contract_signed)",
    ),
    new_stage: Optional[str] = Body(
        None,
        embed=True,
        description="Interview stage baru (opsional)",
    ),
    reason: Optional[str] = Body(
        None,
        embed=True,
        description="Alasan perubahan status (opsional)",
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    """Update application status and/or interview stage"""
    try:
        # Validate status
        valid_statuses = [s.value for s in ApplicationStatus]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Valid values: {valid_statuses}",
            )

        # Validate stage if provided
        if new_stage:
            valid_stages = [s.value for s in InterviewStage]
            if new_stage not in valid_stages:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid stage. Valid values: {valid_stages}",
                )

        success = application_service.update_application_status(
            application_id,
            new_status,
            new_stage,
            current_user.id,
            reason,
            actor_role=getattr(current_user, "role", None),
            actor_ip=request.client.host,
            actor_user_agent=request.headers.get("user-agent"),
        )

        if not success:
            raise HTTPException(status_code=404, detail="Application not found")

        return {
            "message": "Application status updated",
            "application_id": application_id,
            "new_status": new_status,
            "new_stage": new_stage,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating application status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{application_id}/scores",
    response_model=dict,
    summary="Update Application Scores",
    description="""
    Update skor penilaian kandidat.
    
    **Format application_id:** Integer (contoh: `2`)
    
    **Scores yang bisa diupdate (0-100):**
    - `fit_score`: Skor kesesuaian dengan posisi
    - `skill_score`: Skor kemampuan teknis
    - `experience_score`: Skor pengalaman kerja
    
    **Request Body:**
    ```json
    {
        "fit_score": 85.5,
        "skill_score": 90.0,
        "experience_score": 75.0
    }
    ```
    
    **Catatan:**
    - Semua score bersifat opsional (partial update).
    - Nilai harus antara 0 dan 100.
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Skor berhasil diupdate"},
        404: {"description": "Lamaran tidak ditemukan"},
        500: {"description": "Internal server error"},
    },
)
async def update_application_scores(
    application_id: int = Path(
        ...,
        description="Application ID (Integer)",
        example=2,
    ),
    fit_score: Optional[float] = Body(
        None,
        ge=0,
        le=100,
        description="Skor kesesuaian (0-100)",
    ),
    skill_score: Optional[float] = Body(
        None,
        ge=0,
        le=100,
        description="Skor kemampuan teknis (0-100)",
    ),
    experience_score: Optional[float] = Body(
        None,
        ge=0,
        le=100,
        description="Skor pengalaman kerja (0-100)",
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Update skor penilaian kandidat.

    Args:
        application_id: ID lamaran yang akan diupdate.
        fit_score: Skor kesesuaian (0-100).
        skill_score: Skor kemampuan teknis (0-100).
        experience_score: Skor pengalaman kerja (0-100).
        current_user: User yang sedang login.

    Returns:
        dict: Message sukses dengan application_id.

    Raises:
        HTTPException: 404 jika lamaran tidak ditemukan.
        HTTPException: 500 jika terjadi error.
    """
    try:
        success = application_service.update_application_scores(
            application_id, fit_score, skill_score, experience_score
        )

        if not success:
            raise HTTPException(status_code=404, detail="Application not found")

        return {
            "message": "Application scores updated",
            "application_id": application_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating application scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{application_id}/history",
    response_model=List[dict],
    summary="Get Application History",
    description="""
    Mendapatkan riwayat perubahan status lamaran.
    
    **Format application_id:** Integer (contoh: `2`)
    
    **Data yang Dikembalikan (per entry):**
    - `id`: ID history record
    - `application_id`: ID lamaran
    - `previous_status`: Status sebelumnya
    - `new_status`: Status baru
    - `previous_stage`: Stage interview sebelumnya
    - `new_stage`: Stage interview baru
    - `changed_by`: User ID yang mengubah
    - `reason`: Alasan perubahan
    - `changed_at`: Waktu perubahan
    
    **Test Data:**
    - application_id `2` memiliki beberapa history records
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Riwayat lamaran berhasil diambil"},
        404: {"description": "Lamaran tidak ditemukan"},
        500: {"description": "Internal server error"},
    },
)
async def get_application_history(
    application_id: int = Path(
        ...,
        description="Application ID (Integer)",
        example=2,
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Mengambil riwayat perubahan status lamaran.

    Args:
        application_id: ID lamaran yang ingin dilihat riwayatnya.
        current_user: User yang sedang login.

    Returns:
        List[dict]: Daftar riwayat perubahan status.

    Raises:
        HTTPException: 404 jika lamaran tidak ditemukan.
        HTTPException: 500 jika terjadi error.
    """
    try:
        history = application_service.get_application_history(application_id)

        if not history:
            # Check if application exists
            app = application_service.get_application_by_id(application_id)
            if not app:
                raise HTTPException(status_code=404, detail="Application not found")

        return history

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/statistics/dashboard",
    response_model=dict,
    summary="Get Dashboard Statistics",
    description="""
    Mendapatkan statistik untuk dashboard recruitment.
    
    **Data yang Dikembalikan:**
    
    **Application Statistics:**
    - `total_applications`: Total semua lamaran
    - `by_status`: Distribusi berdasarkan status
    - `by_stage`: Distribusi berdasarkan interview stage
    
    **Dashboard Metrics:**
    - `today_applications`: Lamaran hari ini
    - `needs_review`: Lamaran yang perlu direview
    - `upcoming_interviews`: Interview dalam 7 hari ke depan
    
    **Contoh Response:**
    ```json
    {
        "total_applications": 150,
        "by_status": {
            "applied": 45,
            "in_review": 30,
            "qualified": 25
        },
        "dashboard_metrics": {
            "today_applications": 5,
            "needs_review": 75,
            "upcoming_interviews": 12
        }
    }
    ```
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Statistik berhasil diambil"},
        500: {"description": "Internal server error"},
    },
)
async def get_dashboard_statistics(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Mengambil statistik untuk dashboard recruitment.

    Args:
        current_user: User yang sedang login.

    Returns:
        dict: Statistik lamaran dan metrics dashboard.

    Raises:
        HTTPException: 500 jika terjadi error.
    """
    try:
        stats = application_service.get_application_statistics()

        # Add some quick stats for dashboard
        from app.services.database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor()

        # Today's applications
        cursor.execute("""
        SELECT COUNT(*) as count 
        FROM applications 
        WHERE applied_date = CURRENT_DATE
        """)
        today_apps = cursor.fetchone()["count"]

        # Applications needing review
        cursor.execute("""
        SELECT COUNT(*) as count 
        FROM applications 
        WHERE application_status IN ('applied', 'in_review')
        """)
        needs_review = cursor.fetchone()["count"]

        # Upcoming interviews
        cursor.execute("""
        SELECT COUNT(*) as count 
        FROM applications 
        WHERE interview_date >= CURRENT_DATE 
        AND interview_date <= CURRENT_DATE + INTERVAL '7 days'
        """)
        upcoming_interviews = cursor.fetchone()["count"]

        cursor.close()

        return {
            **stats,
            "dashboard_metrics": {
                "today_applications": today_apps,
                "needs_review": needs_review,
                "upcoming_interviews": upcoming_interviews,
            },
        }

    except Exception as e:
        logger.error(f"Error getting dashboard statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/test/sample-data",
    response_model=dict,
    summary="Test Sample Data",
    description="""
    Endpoint test untuk memverifikasi sample data di database.
    
    **Tujuan:**
    Endpoint ini digunakan untuk debugging dan memastikan
    data seed sudah berhasil diload ke database.
    
    **Data yang Dikembalikan:**
    - `status`: Status sistem
    - `jobs_count`: Jumlah lowongan di database
    - `applications_count`: Jumlah lamaran di database
    - `status_distribution`: Distribusi lamaran per status
    - `endpoints_available`: Daftar endpoint yang tersedia
    
    **⚠️ Membutuhkan Authorization Token!**
    
    **Catatan:**
    - Endpoint ini sebaiknya di-disable di production.
    """,
    responses={
        200: {"description": "Sample data info berhasil diambil"},
        500: {"description": "Internal server error"},
    },
)
async def test_sample_data(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Test endpoint untuk memverifikasi sample data.

    Args:
        current_user: User yang sedang login.

    Returns:
        dict: Informasi tentang sample data dan endpoints.

    Raises:
        HTTPException: 500 jika terjadi error.
    """
    try:
        from app.services.database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM jobs")
        jobs_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM applications")
        apps_count = cursor.fetchone()["count"]

        cursor.execute("""
        SELECT 
            application_status, 
            COUNT(*) as count 
        FROM applications 
        GROUP BY application_status
        """)
        status_distribution = cursor.fetchall()

        cursor.close()

        return {
            "status": "Jobs and Applications system ready",
            "jobs_count": jobs_count,
            "applications_count": apps_count,
            "status_distribution": status_distribution,
            "endpoints_available": {
                "GET /api/v1/jobs": "List jobs",
                "GET /api/v1/jobs/{id}": "Get job details",
                "GET /api/v1/jobs/{id}/applications": "Get job applications",
                "GET /api/v1/applications": "List applications",
                "GET /api/v1/applications/{id}": "Get application details",
                "PUT /api/v1/applications/{id}/status": "Update status",
                "PUT /api/v1/applications/{id}/scores": "Update scores",
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
