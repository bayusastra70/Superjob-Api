from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, Request, UploadFile, File, Form
from typing import List, Optional
from loguru import logger
import uuid
import os
from datetime import datetime

from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationStatus,
    InterviewStage,
)
from app.schemas.application_file import (
    ApplicationFileCreate,
    ApplicationFileResponse,
    ApplicationFileUploadResponse,
    FileUploadStatus,
)
from app.services.application_service import ApplicationService
from app.services.application_file_service import ApplicationFileService
from app.core.security import get_current_user
from app.schemas.user import UserResponse

from app.schemas.response import BaseResponse
from app.utils.response import (
    success_response,
    unauthorized_response,
    internal_server_error_response,
    not_found_response,
    bad_request_response,
    created_response
)

from app.services.database import get_db_connection


router = APIRouter(prefix="/applications", tags=["Applications"])

application_service = ApplicationService()
application_file_service = ApplicationFileService()


@router.get(
    "/",
    response_model=BaseResponse[ApplicationListResponse] ,
    summary="List Applications",
    
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
    search: Optional[str] = Query(
        None,
        description="Cari berdasarkan nama/email",
    ),
    limit: int = Query(50, ge=1, le=100, description="Jumlah item per halaman"),
    page: int = Query(1, ge=1, description="Nomor halaman (current page)"),
    sort_by: str = Query("created_at", description="Field untuk sorting"),
    sort_order: str = Query("desc", description="Urutan: asc atau desc"),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get list of applications with filters"""
    try:
        offset = (page - 1) * limit

        applications = application_service.get_applications(
            job_id=job_id,
            status=status,
            search=search,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        conn = get_db_connection()
        cursor = conn.cursor()

        count_query = """
            SELECT COUNT(*) as total 
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN users u ON a.candidate_id = u.id
            WHERE 1=1
        """
        params = []

        if job_id:
            count_query += " AND job_id = %s"
            params.append(job_id)

        if status:
            count_query += " AND application_status = %s"
            params.append(status)

        if search:
            count_query += " AND (u.full_name ILIKE %s OR u.email ILIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]
        cursor.close()

        total_pages = (total + limit - 1) // limit

        data = ApplicationListResponse(
            applications=applications,
            total=total,
            limit=limit,
            page=page,
            total_pages=total_pages
        )

        return success_response(data=data)

    except Exception as e:
        logger.error(f"Error getting applications: {e}")
        raise


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Get Application Details",
    
    responses={
        200: {},
        422: {},
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
    
    try:
        application = application_service.get_application_by_id(application_id)

        if not application:
            raise not_found_response(message="Application not found")

        return application

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application {application_id}: {e}")
        raise 


@router.post(
    "/submit",
    response_model=BaseResponse[dict],
    summary="Submit Application with Files",
)
async def submit_application(
    request: Request,
    job_id: int = Form(...),
    full_name: str = Form(...),
    whatsapp_number: str = Form(...),
    coverletter: Optional[str] = Form(None),
    coverletter_file: Optional[UploadFile] = File(None),  # New field
    portfolio: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    cv: Optional[UploadFile] = File(None),
    cv_link: Optional[str] = Form(None),
    portfolio_file: Optional[UploadFile] = File(None),
    current_user: UserResponse = Depends(get_current_user),
):
    """Submit application - all logic in service layer"""
    try:
        # Validation: Either cv OR cv_link must be provided
        if not cv and not cv_link:
            return bad_request_response(
                message="Either CV file or CV link must be provided",
                raise_exception=False
            )
        
        if cv and cv_link:
            return bad_request_response(
                message="Provide either CV file OR CV link, not both",
                raise_exception=False
            )
        
        # Validate CV file if provided
        if cv:
            allowed_types = ['application/pdf', 'application/msword', 
                            'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            if cv.content_type not in allowed_types:
                return bad_request_response(
                    message="CV must be PDF or Word document",
                    raise_exception=False
                )
        
        # Validate cover letter file if provided
        if coverletter_file:
            allowed_types = ['application/pdf', 'application/msword', 
                            'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            if coverletter_file.content_type not in allowed_types:
                return bad_request_response(
                    message="Cover letter file must be PDF or Word document",
                    raise_exception=False
                )
        
        # Validate portfolio file if provided
        if portfolio_file:
            allowed_types = ['application/pdf', 'application/msword', 
                            'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            if portfolio_file.content_type not in allowed_types:
                return bad_request_response(
                    message="Portfolio file must be PDF or Word document",
                    raise_exception=False
                )
        
        # Validate whatsapp number format (optional validation)
        import re
        if not re.match(r'^[0-9+\-\s()]{10,20}$', whatsapp_number):
            return bad_request_response(
                message="Invalid WhatsApp number format",
                raise_exception=False
            )
        
        # Call service
        application_id = await application_service.create_application_with_files(
            job_id=job_id,
            full_name=full_name,
            whatsapp_number=whatsapp_number,
            coverletter=coverletter,
            coverletter_file=coverletter_file,  # Pass new field
            portfolio_link=portfolio,
            location=location,
            cv_file=cv,
            cv_link=cv_link,
            portfolio_file=portfolio_file,
            candidate_id=current_user.id,
            actor_role=getattr(current_user, "role", None),
            actor_ip=request.client.host,
            actor_user_agent=request.headers.get("user-agent")
        )

        if not application_id:
            return bad_request_response(
                message="Failed to create application",
                raise_exception=False
            )
        
        data = {"application_id": application_id}
        return success_response(data=data)

    except Exception as e:
        logger.error(f"❌ Router error in submit_application: {type(e).__name__}: {str(e)}")
        raise


@router.post(
    "/",
    response_model=dict,
    summary="Create Application",
)
async def create_application(
    request: Request,
    application_data: ApplicationCreate,
    current_user: UserResponse = Depends(get_current_user),
):
    
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
        raise


@router.put(
    "/{application_id}/status",
    response_model=dict,
    summary="Update Application Status",
    
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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put(
    "/{application_id}/scores",
    response_model=dict,
    summary="Update Application Scores",
    
    responses={
        200: {},
        422: {},
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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{application_id}/history",
    response_model=List[dict],
    summary="Get Application History",
    
    responses={
        200: {},
        422: {},
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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/statistics/dashboard",
    response_model=dict,
    summary="Get Dashboard Statistics",
    
    responses={
        200: {},
        422: {},
    },
)
async def get_dashboard_statistics(
    current_user: UserResponse = Depends(get_current_user),
):
    
    try:
        stats = application_service.get_application_statistics()

        

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
        raise HTTPException(status_code=500, detail="Internal server error")



    


# =================================================================

@router.post(
    "/{application_id}/files",
    response_model=ApplicationFileUploadResponse,
    summary="Upload File for Application",
    responses={
        200: {},
        422: {},
        
    },
)
async def upload_application_file(
    request: Request,
    application_id: int = Path(
        ...,
        description="Application ID (Integer)",
        example=2,
    ),
    file: UploadFile = File(
        ...,
        description="File yang akan diupload",
        media_type="multipart/form-data"
    ),
    file_type: str = Form(
        "resume",
        description="Tipe file: resume, portfolio, certificate, cover_letter, other"
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        # Validasi: Check if application exists
        application = application_service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Validasi file type
        valid_file_types = ["resume", "portfolio", "certificate", "cover_letter", "other"]
        if file_type not in valid_file_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Valid types: {', '.join(valid_file_types)}"
            )
        
        # Validasi file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        file.file.seek(0, 2)  # Move to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is 10MB. Current size: {file_size/1024/1024:.2f}MB"
            )
        
        # Validasi file extension
        allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File extension not allowed. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Generate unique filename
        original_filename = file.filename
        unique_filename = f"{file_type}_{uuid.uuid4().hex}{file_extension}"
        
        # Upload file
        upload_result = await application_file_service.upload_file(
            application_id=application_id,
            file=file,
            original_filename=original_filename,
            stored_filename=unique_filename,
            file_type=file_type,
            uploader_id=current_user.id,
            uploader_ip=request.client.host,
            uploader_user_agent=request.headers.get("user-agent")
        )
        
        if not upload_result:
            raise HTTPException(
                status_code=500, 
                detail="Failed to upload file"
            )
        
        return upload_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file for application {application_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{application_id}/files",
    response_model=List[ApplicationFileResponse],
    summary="Get Application Files",
    responses={
        200: {},
        422: {},
    },
)
async def get_application_files(
    application_id: int = Path(
        ...,
        description="Application ID (Integer)",
        example=2,
    ),
    file_type: Optional[str] = Query(
        None,
        description="Filter by file type (resume, portfolio, certificate, cover_letter, other)"
    ),
    upload_status: Optional[str] = Query(
        None,
        description="Filter by upload status (pending, uploading, completed, failed)"
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    
    try:
        # Validasi: Check if application exists
        application = application_service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        files = application_file_service.get_application_files(
            application_id=application_id,
            file_type=file_type,
            upload_status=upload_status
        )
        
        return files
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting files for application {application_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{application_id}/files/{file_id}",
    response_model=ApplicationFileResponse,
    summary="Get File Details",
    responses={
        200: {},
        422: {},
    },
)
async def get_application_file(
    application_id: int = Path(
        ...,
        description="Application ID (Integer)",
        example=2,
    ),
    file_id: int = Path(
        ...,
        description="File ID (Integer)",
        example=1,
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        # Validasi: Check if application exists
        application = application_service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        file = application_file_service.get_file_by_id(file_id, application_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        return file
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file {file_id} for application {application_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/{application_id}/files/{file_id}",
    response_model=dict,
    summary="Delete Application File",
    responses={
        200: {},
        422: {},
    },
)
async def delete_application_file(
    application_id: int = Path(
        ...,
        description="Application ID (Integer)",
        example=2,
    ),
    file_id: int = Path(
        ...,
        description="File ID (Integer)",
        example=1,
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        # Validasi: Check if application exists
        application = application_service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        success = await application_file_service.delete_file(
            file_id=file_id,
            application_id=application_id,
            deleter_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="File not found or failed to delete")
        
        return {
            "message": "File deleted successfully",
            "application_id": application_id,
            "file_id": file_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id} for application {application_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
