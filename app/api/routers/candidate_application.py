from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_db
from app.schemas.candidate_application_schema import (
    CandidateApplicationCreate,
    CandidateApplicationRead,
    CandidateApplicationUpdate,
    CandidateApplicationResponse
)
from app.services.candidate_application_service import (
    create_candidate_application,
    get_candidate_applications,
    get_candidate_application,
    get_candidate_application_with_reason,
    update_candidate_application,
    delete_candidate_application
)

router = APIRouter(
    prefix="/candidate-applications",
    tags=["Candidate Applications"]
)


@router.post("/", response_model=CandidateApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    candidate: CandidateApplicationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Membuat candidate application baru
    """
    return await create_candidate_application(db, candidate)


@router.get("/", response_model=List[CandidateApplicationRead])
async def read_candidates(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Mendapatkan semua candidate applications dengan pagination
    """
    return await get_candidate_applications(db, skip=skip, limit=limit)


@router.get("/{candidate_id}", response_model=CandidateApplicationResponse)
async def read_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Mendapatkan candidate application berdasarkan ID dengan rejection reason
    """
    candidate = await get_candidate_application_with_reason(db, candidate_id)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate application with id {candidate_id} not found"
        )
    
    # Convert to response format
    response_data = CandidateApplicationResponse.model_validate(candidate)
    if candidate.rejection_reason:
        response_data.rejection_reason = {
            "id": candidate.rejection_reason.id,
            "reason_code": candidate.rejection_reason.reason_code,
            "reason_text": candidate.rejection_reason.reason_text,
            "is_custom": candidate.rejection_reason.is_custom
        }
    
    return response_data


@router.patch("/{candidate_id}", response_model=CandidateApplicationRead)
async def update_candidate(
    candidate_id: int,
    candidate_update: CandidateApplicationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update candidate application (status dan/atau rejection_reason_id)
    """
    updated_candidate = await update_candidate_application(
        db,
        candidate_id,
        status=candidate_update.status,
        rejection_reason_id=candidate_update.rejection_reason_id
    )
    if updated_candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate application with id {candidate_id} not found"
        )
    return updated_candidate


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Menghapus candidate application
    """
    success = await delete_candidate_application(db, candidate_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate application with id {candidate_id} not found"
        )
    return None

