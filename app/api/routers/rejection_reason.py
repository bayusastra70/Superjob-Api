from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.api.deps import get_db
from app.models.rejection_reason import RejectionReason
from app.schemas.rejection_reason_schema import (
    RejectionReasonCreate,
    RejectionReasonResponse,
    RejectionReasonUpdate,
)

router = APIRouter(prefix="/rejection-reasons", tags=["Rejection Reasons"])


@router.get(
    "/",
    response_model=List[RejectionReasonResponse],
    summary="List Rejection Reasons",
    description="""
    Mendapatkan daftar alasan penolakan kandidat.
    
    **Query Parameter:**
    - `active_only`: Filter hanya yang aktif (default: true)
    
    **Test Data ID 1-11:**
    - `SKILL_MISMATCH` - Keterampilan tidak sesuai
    - `EXPERIENCE_LACK` - Pengalaman kurang
    - `SALARY_MISMATCH` - Ekspektasi gaji tidak sesuai
    - `CULTURE_FIT` - Tidak cocok budaya
    - `COMMUNICATION` - Komunikasi kurang
    - `POSITION_FILLED` - Posisi sudah terisi
    - `NO_RESPONSE` - Tidak merespons
    - `DOCUMENT_INCOMPLETE` - Dokumen tidak lengkap
    - `OVERQUALIFIED` - Terlalu berkualifikasi
    - `LOCATION_ISSUE` - Lokasi tidak sesuai
    - `OTHER` - Alasan lainnya
    """,
)
async def get_rejection_reasons(
    active_only: bool = True, db: AsyncSession = Depends(get_db)
):
    """
    Mendapatkan daftar rejection reasons
    """
    stmt = select(RejectionReason)
    if active_only:
        stmt = stmt.where(RejectionReason.is_active == True)
    result = await db.execute(stmt)
    reasons = list(result.scalars().all())
    return reasons


@router.post(
    "/", response_model=RejectionReasonResponse, status_code=status.HTTP_201_CREATED
)
async def create_rejection_reason(
    reason: RejectionReasonCreate, db: AsyncSession = Depends(get_db)
):
    """
    Membuat rejection reason baru
    """
    db_reason = RejectionReason(
        reason_code=reason.reason_code,
        reason_text=reason.reason_text,
        is_custom=reason.is_custom,
        created_by=reason.created_by,
        is_active=True,
    )
    db.add(db_reason)
    await db.commit()
    await db.refresh(db_reason)
    return db_reason


@router.get("/{reason_id}", response_model=RejectionReasonResponse)
async def get_rejection_reason(reason_id: int, db: AsyncSession = Depends(get_db)):
    """
    Mendapatkan rejection reason berdasarkan ID
    """
    stmt = select(RejectionReason).where(RejectionReason.id == reason_id)
    result = await db.execute(stmt)
    db_reason = result.scalar_one_or_none()

    if not db_reason:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rejection reason with id {reason_id} not found",
        )

    return db_reason


@router.patch("/{reason_id}", response_model=RejectionReasonResponse)
async def update_rejection_reason(
    reason_id: int,
    reason_update: RejectionReasonUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update rejection reason
    """
    stmt = select(RejectionReason).where(RejectionReason.id == reason_id)
    result = await db.execute(stmt)
    db_reason = result.scalar_one_or_none()

    if not db_reason:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rejection reason with id {reason_id} not found",
        )

    if reason_update.reason_code is not None:
        db_reason.reason_code = reason_update.reason_code
    if reason_update.reason_text is not None:
        db_reason.reason_text = reason_update.reason_text
    if reason_update.is_active is not None:
        db_reason.is_active = reason_update.is_active

    await db.commit()
    await db.refresh(db_reason)
    return db_reason


@router.patch("/{reason_id}/deactivate", response_model=RejectionReasonResponse)
async def soft_delete_rejection_reason(
    reason_id: int, db: AsyncSession = Depends(get_db)
):
    """
    Deactivate rejection reason (soft delete)
    """
    stmt = select(RejectionReason).where(RejectionReason.id == reason_id)
    result = await db.execute(stmt)
    db_reason = result.scalar_one_or_none()

    if not db_reason:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rejection reason with id {reason_id} not found",
        )

    db_reason.is_active = False
    await db.commit()
    await db.refresh(db_reason)
    return db_reason
