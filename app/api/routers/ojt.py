from fastapi import APIRouter, Depends, Query, Path, Form, File, UploadFile, status
from typing import Optional, Literal
from loguru import logger
import math

from app.schemas.ojt_program import OjtProgramResponse, OjtProgramListData
from app.schemas.ojt_application import (
    OjtApplicationCreate,
    OjtApplicationResponse,
    OjtApplicationListData,
)
from app.services.ojt_program_service import OjtProgramService
from app.services.ojt_application_service import OjtApplicationService
from app.core.security import get_current_user, get_current_user_optional
from app.schemas.user import UserResponse

from app.utils.response import (
    success_response,
    not_found_response,
    bad_request_response,
    created_response,
    forbidden_response,
    internal_server_error_response,
)
from app.schemas.response import BaseResponse


router = APIRouter(prefix="/ojt", tags=["OJT - On the Job Training"])

ojt_program_service = OjtProgramService()
ojt_application_service = OjtApplicationService()


# ═══════════════════════════════════════════════════════════
# ENDPOINT 1: GET /ojt/programs — List OJT Programs (US-1)
# ═══════════════════════════════════════════════════════════
@router.get(
    "/programs",
    response_model=BaseResponse[OjtProgramListData],
    summary="List OJT Programs",
    description="Ambil daftar program OJT yang tersedia dengan filter opsional.",
)
async def get_ojt_programs(
    role: Optional[str] = Query(None, description="Filter by role/posisi"),
    location: Optional[str] = Query(None, description="Filter by lokasi"),
    training_type: Optional[Literal['onsite', 'remote', 'hybrid']] = Query(
        None, description="Filter by tipe pelatihan (onsite, remote, hybrid)"
    ),
    duration_min: Optional[int] = Query(None, ge=1, description="Durasi minimum (hari)"),
    duration_max: Optional[int] = Query(None, ge=1, description="Durasi maksimum (hari)"),
    status: Optional[str] = Query(
        "published", description="Filter by status (default: published)"
    ),
    search: Optional[str] = Query(None, description="Search by title/description"),
    page: int = Query(1, ge=1, description="Nomor halaman"),
    limit: int = Query(10, ge=1, le=50, description="Jumlah per halaman"),
    current_user: Optional[UserResponse] = Depends(get_current_user_optional),
):
    try:
        offset = (page - 1) * limit
        user_id = current_user.id if current_user else None

        programs = ojt_program_service.get_programs(
            role=role,
            location=location,
            training_type=training_type,
            duration_min=duration_min,
            duration_max=duration_max,
            status=status,
            search=search,
            limit=limit,
            offset=offset,
            user_id=user_id,
        )

        total = ojt_program_service.get_programs_count(
            role=role,
            location=location,
            training_type=training_type,
            duration_min=duration_min,
            duration_max=duration_max,
            status=status,
            search=search,
        )

        total_pages = math.ceil(total / limit) if total > 0 else 1

        data = OjtProgramListData(
            programs=[OjtProgramResponse(**p) for p in programs],
            total=total,
            page=page,
            total_pages=total_pages,
        )

        return success_response(
            data=data,
            message=f"Page {page} of {total_pages} — {total} programs found",
        )
    except Exception as e:
        logger.error(f"Error listing OJT programs: {e}")
        return internal_server_error_response(
            message="Internal server error", raise_exception=False
        )


# ═══════════════════════════════════════════════════════════
# ENDPOINT 2: GET /ojt/programs/{id} — Program Detail (US-2)
# ═══════════════════════════════════════════════════════════
@router.get(
    "/programs/{program_id}",
    response_model=BaseResponse[OjtProgramResponse],
    summary="Get OJT Program Detail",
    description="Ambil detail program OJT berdasarkan ID.",
)
async def get_ojt_program_detail(
    program_id: int = Path(..., description="ID program OJT"),
    current_user: Optional[UserResponse] = Depends(get_current_user_optional),
):
    try:
        user_id = current_user.id if current_user else None
        program = ojt_program_service.get_program_by_id(program_id, user_id)

        if not program:
            return not_found_response(
                message=f"Program OJT dengan ID {program_id} tidak ditemukan",
                raise_exception=False,
            )

        data = OjtProgramResponse(**program)

        return success_response(
            data=data,
            message="Program detail retrieved successfully",
        )
    except Exception as e:
        logger.error(f"Error getting OJT program {program_id}: {e}")
        return internal_server_error_response(
            message="Internal server error", raise_exception=False
        )


# ═══════════════════════════════════════════════════════════
# ENDPOINT 3: POST /ojt/applications — Apply to OJT (US-3)
# ═══════════════════════════════════════════════════════════
@router.post(
    "/applications",
    response_model=BaseResponse[OjtApplicationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Daftar ke program OJT",
)
async def create_ojt_application(
    program_id: int = Form(..., description="ID program OJT"),
    full_name: str = Form(..., description="Nama Lengkap"),
    phone_number: str = Form(..., description="Nomor WhatsApp"),
    domicile: str = Form(..., description="Domisili"),
    cover_letter: Optional[str] = Form(None, description="Cover Letter"),
    cv_file: UploadFile = File(..., description="File CV (PDF)"),
    portfolio_file: Optional[UploadFile] = File(None, description="File Portfolio (PDF, Optional)"),
    portfolio_url: Optional[str] = Form(None, description="Link Portfolio (Optional)"),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Talent mendaftar ke program OJT dengan upload CV dan Portfolio.
    """
    try:
        # Panggil service (async)
        result = await ojt_application_service.create_application(
            talent_id=current_user.id,
            program_id=program_id,
            full_name=full_name,
            phone_number=phone_number,
            domicile=domicile,
            cv_file=cv_file,
            portfolio_file=portfolio_file,
            portfolio_url=portfolio_url,
            cover_letter=cover_letter,
        )

        if "error" in result:
            return error_response(
                message=result["error"], status_code=result["code"]
            )

        return success_response(
            data=result, message="Berhasil mendaftar ke program OJT"
        )

    except Exception as e:
        logger.error(f"Error applying to OJT: {e}")
        return error_response(
            message=f"Terjadi kesalahan: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ═══════════════════════════════════════════════════════════
# ENDPOINT 4: GET /ojt/applications/me — My Applications (US-4)
# ═══════════════════════════════════════════════════════════
@router.get(
    "/applications/me",
    response_model=BaseResponse[OjtApplicationListData],
    summary="Get My OJT Applications",
    description="Ambil daftar pendaftaran OJT milik talent yang sedang login.",
)
async def get_my_ojt_applications(
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        applications = ojt_application_service.get_my_applications(
            talent_id=current_user.id
        )

        data = OjtApplicationListData(
            applications=[OjtApplicationResponse(**a) for a in applications],
            total=len(applications),
        )

        return success_response(
            data=data,
            message=f"{len(applications)} application(s) found",
        )
    except Exception as e:
        logger.error(f"Error getting my OJT applications: {e}")
        return internal_server_error_response(
            message="Internal server error", raise_exception=False
        )


# ═══════════════════════════════════════════════════════════
# ENDPOINT 5: POST /ojt/applications/{id}/register — Confirm (US-5)
# ═══════════════════════════════════════════════════════════
@router.post(
    "/applications/{application_id}/register",
    response_model=BaseResponse[OjtApplicationResponse],
    summary="Register (Confirm) OJT Application",
    description="Konfirmasi keikutsertaan OJT setelah application di-accept. Status berubah accepted → registered.",
)
async def register_ojt_application(
    application_id: int = Path(..., description="ID pendaftaran OJT"),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        result = ojt_application_service.register_application(
            application_id=application_id,
            talent_id=current_user.id,
        )

        if not result:
            return internal_server_error_response(
                message="Gagal registrasi", raise_exception=False
            )

        # Cek apakah result mengandung error
        if "error" in result:
            code = result.get("code", 400)
            if code == 404:
                return not_found_response(
                    message=result["error"], raise_exception=False
                )
            if code == 403:
                return forbidden_response(
                    message=result["error"], raise_exception=False
                )
            return bad_request_response(
                message=result["error"], raise_exception=False
            )

        data = OjtApplicationResponse(**result)

        return success_response(
            data=data,
            message="Berhasil registrasi ke program OJT",
        )
    except Exception as e:
        logger.error(f"Error registering OJT application: {e}")
        return internal_server_error_response(
            message="Internal server error", raise_exception=False
        )


# ═══════════════════════════════════════════════════════════
# SPRINT 2: LEARNING EXPERIENCE ENDPOINTS
# ═══════════════════════════════════════════════════════════

from app.schemas.ojt_dashboard import OjtDashboardData
from app.services.ojt_dashboard_service import ojt_dashboard_service
from app.schemas.ojt_agenda import OjtAgendaList, OjtAgendaResponse
from app.services.ojt_agenda_service import ojt_agenda_service
from app.schemas.ojt_attendance import OjtAttendanceCreate, OjtAttendanceResponse
from app.schemas.ojt_task import (
    OjtTaskList,
    OjtTaskResponse,
    OjtTaskSubmissionCreate,
    OjtTaskSubmissionResponse,
    OjtTaskSubmissionScore
)
from app.services.ojt_task_service import ojt_task_service


# ═══════════════════════════════════════════════════════════
# ENDPOINT 6: GET /ojt/dashboard (US-6)
# ═══════════════════════════════════════════════════════════
@router.get(
    "/dashboard",
    response_model=BaseResponse[OjtDashboardData],
    summary="Get OJT Dashboard",
    description="Ringkasan visual untuk talent: active program, progress, agenda hari ini, pending tasks.",
)
async def get_ojt_dashboard(
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        dashboard_data = ojt_dashboard_service.get_talent_dashboard(current_user.id)
        return success_response(data=dashboard_data, message="Dashboard data retrieved")
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        return internal_server_error_response(message="Internal server error")


# ═══════════════════════════════════════════════════════════
# ENDPOINT 7: GET /ojt/programs/{id}/agendas (US-7)
# ═══════════════════════════════════════════════════════════
@router.get(
    "/programs/{program_id}/agendas",
    response_model=BaseResponse[OjtAgendaList],
    summary="List Program Agendas",
    description="Daftar jadwal pelatihan untuk suatu program OJT.",
)
async def get_program_agendas(
    program_id: int = Path(..., description="ID program OJT"),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        agendas = ojt_agenda_service.get_agendas_by_program(program_id, current_user.id)
        return success_response(
            data={"agendas": agendas, "total": len(agendas)}, 
            message=f"{len(agendas)} agendas found"
        )
    except Exception as e:
        logger.error(f"Error listing agendas: {e}")
        return internal_server_error_response(message="Internal server error")


# ═══════════════════════════════════════════════════════════
# ENDPOINT 8: GET /ojt/agendas/{id} (US-8)
# ═══════════════════════════════════════════════════════════
@router.get(
    "/agendas/{agenda_id}",
    response_model=BaseResponse[OjtAgendaResponse],
    summary="Get Agenda Detail",
    description="Detail sesi pelatihan beserta status kehadiran user.",
)
async def get_agenda_detail(
    agenda_id: int = Path(..., description="ID agenda"),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        agenda = ojt_agenda_service.get_agenda_by_id(agenda_id, current_user.id)
        if not agenda:
            return not_found_response(message="Agenda not found")
        return success_response(data=agenda, message="Agenda detail retrieved")
    except Exception as e:
        logger.error(f"Error getting agenda detail: {e}")
        return internal_server_error_response(message="Internal server error")


# ═══════════════════════════════════════════════════════════
# ENDPOINT 9: POST /ojt/attendance (US-9)
# ═══════════════════════════════════════════════════════════
@router.post(
    "/attendance",
    response_model=BaseResponse[dict],
    summary="Submit Attendance",
    description="Talent melakukan absensi kehadiran pada suatu sesi (agenda).",
)
async def submit_attendance(
    attendance_data: OjtAttendanceCreate,
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        result = ojt_agenda_service.record_attendance(
            attendance_data.agenda_id, current_user.id
        )
        
        if not result["success"]:
            return bad_request_response(message=result["message"])
            
        return success_response(data=result, message="Attendance recorded")
    except Exception as e:
        logger.error(f"Error submitting attendance: {e}")
        return internal_server_error_response(message="Internal server error")


# ═══════════════════════════════════════════════════════════
# ENDPOINT 10: GET /ojt/programs/{id}/tasks (US-11)
# ═══════════════════════════════════════════════════════════
@router.get(
    "/programs/{program_id}/tasks",
    response_model=BaseResponse[OjtTaskList],
    summary="List Program Tasks",
    description="Daftar tugas dalam program OJT.",
)
async def get_program_tasks(
    program_id: int = Path(..., description="ID program OJT"),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        tasks = ojt_task_service.get_tasks_by_program(program_id, current_user.id)
        return success_response(
            data={"tasks": tasks, "total": len(tasks)}, 
            message=f"{len(tasks)} tasks found"
        )
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return internal_server_error_response(message="Internal server error")


# ═══════════════════════════════════════════════════════════
# ENDPOINT 11: POST /ojt/tasks/{id}/submissions (US-12)
# ═══════════════════════════════════════════════════════════
@router.post(
    "/tasks/{task_id}/submissions",
    response_model=BaseResponse[dict],
    summary="Submit Task",
    description="Mengirim jawaban tugas (teks atau file URL).",
)
async def submit_task(
    submission_data: OjtTaskSubmissionCreate,
    task_id: int = Path(..., description="ID tugas"),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        result = ojt_task_service.submit_task(
            task_id, 
            current_user.id, 
            submission_data.content, 
            submission_data.file_url
        )
        
        if not result:
             return internal_server_error_response(message="Failed to submit task")
             
        return success_response(data=result, message="Task submitted successfully")
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        return internal_server_error_response(message="Internal server error")


# ═══════════════════════════════════════════════════════════
# ENDPOINT 12: GET /ojt/tasks/{id}/submissions/me (US-13)
# ═══════════════════════════════════════════════════════════
@router.get(
    "/tasks/{task_id}/submissions/me",
    response_model=BaseResponse[OjtTaskSubmissionResponse],
    summary="Get My Submission",
    description="Lihat detail submission saya untuk tugas tertentu.",
)
async def get_my_submission(
    task_id: int = Path(..., description="ID tugas"),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        submission = ojt_task_service.get_my_submission(task_id, current_user.id)
        if not submission:
            return not_found_response(message="Submission not found")
        return success_response(data=submission, message="Submission retrieved")
    except Exception as e:
        logger.error(f"Error getting submission: {e}")
        return internal_server_error_response(message="Internal server error")


# ═══════════════════════════════════════════════════════════
# ENDPOINT 13: GET /ojt/programs/{id}/scores/me (US-14)
# ═══════════════════════════════════════════════════════════
@router.get(
    "/programs/{program_id}/scores/me",
    response_model=BaseResponse[list], # Using list as generic response for scores
    summary="Get My Scores",
    description="Lihat semua nilai dan feedback saya di program ini.",
)
async def get_my_scores(
    program_id: int = Path(..., description="ID program OJT"),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        scores = ojt_task_service.get_my_scores(program_id, current_user.id)
        return success_response(data=scores, message="Scores retrieved")
    except Exception as e:
        logger.error(f"Error getting scores: {e}")
        return internal_server_error_response(message="Internal server error")

