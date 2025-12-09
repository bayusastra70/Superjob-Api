from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from fastapi import HTTPException

from app.models.candidate_application import CandidateApplication
from app.models.rejection_reason import RejectionReason
from app.schemas.candidate_application_schema import CandidateApplicationCreate


async def create_candidate_application(
    db: AsyncSession, 
    candidate: CandidateApplicationCreate
) -> CandidateApplication:
    """
    Membuat candidate application baru
    """
    db_candidate = CandidateApplication(
        name=candidate.name,
        email=candidate.email,
        applied_position=candidate.applied_position,
        status=candidate.status,
        rejection_reason_id=candidate.rejection_reason_id
    )
    db.add(db_candidate)
    await db.commit()
    await db.refresh(db_candidate)
    return db_candidate


async def get_candidate_applications(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100
) -> List[CandidateApplication]:
    """
    Mendapatkan semua candidate applications dengan pagination
    """
    stmt = select(CandidateApplication).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_candidate_application(
    db: AsyncSession, 
    candidate_id: int
) -> Optional[CandidateApplication]:
    """
    Mendapatkan candidate application berdasarkan ID
    """
    stmt = select(CandidateApplication).where(CandidateApplication.id == candidate_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_candidate_application_with_reason(
    db: AsyncSession, 
    candidate_id: int
) -> Optional[CandidateApplication]:
    """
    Mendapatkan candidate application dengan rejection reason
    """
    stmt = (
        select(CandidateApplication)
        .options(selectinload(CandidateApplication.rejection_reason))
        .where(CandidateApplication.id == candidate_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_candidate_application(
    db: AsyncSession,
    candidate_id: int,
    status: Optional[str] = None,
    rejection_reason_id: Optional[int] = None
) -> Optional[CandidateApplication]:
    """
    Update candidate application (status dan/atau rejection_reason_id)
    """
    db_candidate = await get_candidate_application(db, candidate_id)
    if not db_candidate:
        return None
    
    if rejection_reason_id is not None and status != "not_qualified":
        raise HTTPException(
            status_code=400,
            detail="Rejection reason hanya boleh diisi jika status = 'not_qualified'"
        )

    if status is not None:
        db_candidate.status = status
    if rejection_reason_id is not None:
        db_candidate.rejection_reason_id = rejection_reason_id
    
    await db.commit()
    await db.refresh(db_candidate)
    return db_candidate


async def delete_candidate_application(
    db: AsyncSession,
    candidate_id: int
) -> bool:
    """
    Menghapus candidate application
    """
    db_candidate = await get_candidate_application(db, candidate_id)
    if not db_candidate:
        return False
    
    await db.delete(db_candidate)
    await db.commit()
    return True

