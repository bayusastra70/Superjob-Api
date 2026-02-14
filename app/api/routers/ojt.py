from fastapi import APIRouter, Depends, Query, Path
from typing import Optional
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
from app.core.security import get_current_user
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
    status: Optional[str] = Query(
        "published", description="Filter by status (default: published)"
    ),
    search: Optional[str] = Query(None, description="Search by title/description"),
    page: int = Query(1, ge=1, description="Nomor halaman"),
    limit: int = Query(10, ge=1, le=50, description="Jumlah per halaman"),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        offset = (page - 1) * limit

        programs = ojt_program_service.get_programs(
            role=role,
            location=location,
            status=status,
            search=search,
            limit=limit,
            offset=offset,
        )

        total = ojt_program_service.get_programs_count(
            role=role,
            location=location,
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
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        program = ojt_program_service.get_program_by_id(program_id)

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
    summary="Apply to OJT Program",
    description="Mendaftar ke program OJT. Satu talent hanya bisa apply 1x per program.",
)
async def apply_to_ojt(
    application_data: OjtApplicationCreate,
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        result = ojt_application_service.create_application(
            talent_id=current_user.id,
            program_id=application_data.program_id,
            motivation_letter=application_data.motivation_letter,
        )

        if not result:
            return internal_server_error_response(
                message="Gagal membuat pendaftaran", raise_exception=False
            )

        # Cek apakah result mengandung error
        if "error" in result:
            code = result.get("code", 400)
            if code == 404:
                return not_found_response(
                    message=result["error"], raise_exception=False
                )
            return bad_request_response(
                message=result["error"], raise_exception=False
            )

        data = OjtApplicationResponse(**result)

        return created_response(
            data=data,
            message="Berhasil mendaftar ke program OJT",
        )
    except Exception as e:
        logger.error(f"Error applying to OJT: {e}")
        return internal_server_error_response(
            message="Internal server error", raise_exception=False
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
