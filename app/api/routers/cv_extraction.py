from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Request
from typing import Optional
from fastapi.security import HTTPBearer
from loguru import logger

from app.core.security import get_current_user
from app.core.limiter import limiter
from app.schemas.cv_extraction import CVExtractedData, CVExtractionResponse
from app.schemas.user import UserResponse
from app.services.cv_extraction_service import cv_extraction_service

router = APIRouter(prefix="/candidates", tags=["CV Extraction"])
security = HTTPBearer()


def validate_pdf_file(file: UploadFile) -> None:
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content-Type header is missing",
        )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF files are allowed. Got: {file.content_type}",
        )

    import os

    file_extension = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if file_extension != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have .pdf extension",
        )


@router.post(
    "/cv/scan",
    response_model=CVExtractionResponse,
    summary="Scan CV and Extract Data",
    description="""
    Upload a CV/resume (PDF) to extract structured data using AI.

    **Features:**
    - Extracts personal info, work experience, education, skills, languages, and certifications
    - Returns grouped JSON response for easy integration
    - Rate limited: 5 requests per minute

    **Input:**
    - PDF file (max 10MB)

    **Output:**
    - Structured data grouped by: profile, experience, education, skills, languages, certifications
    """,
    responses={
        200: {"description": "CV extracted successfully"},
        400: {"description": "Invalid file type or size"},
        401: {"description": "Unauthorized"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Extraction failed"},
    },
)
@limiter.limit("5/minute")
async def scan_cv(
    request: Request,
    cv_file: UploadFile = File(..., description="CV file in PDF format"),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        logger.info(
            f"CV scan requested by user {current_user.id}: {current_user.email}"
        )

        validate_pdf_file(cv_file)

        max_size = 10 * 1024 * 1024
        content = await cv_file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size is 10MB",
            )

        await cv_file.seek(0)

        extracted_data = await cv_extraction_service.extract_from_pdf_content(content)

        logger.info(f"CV scan completed for user {current_user.id}")

        return CVExtractionResponse(
            success=True,
            message="CV extracted successfully",
            data=extracted_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV scan failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract CV data: {str(e)}",
        )
