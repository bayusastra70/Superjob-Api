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
        stmt = stmt.where(RejectionReason.is_active.is_(True))
    result = await db.execute(stmt)
    reasons = list(result.scalars().all())
    return reasons


@router.post(
    "/",
    response_model=RejectionReasonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Rejection Reason",
    description="""
    Membuat alasan penolakan kandidat baru.
    
    **Request Body:**
    - `reason_code` (required): Kode unik alasan (uppercase, underscore)
    - `reason_text` (required): Teks deskripsi alasan
    - `is_custom` (optional): Apakah alasan custom dari employer (default: false)
    - `created_by` (optional): ID user yang membuat
    
    **Contoh Request Body:**
    ```json
    {
        "reason_code": "RELOCATION_ISSUE",
        "reason_text": "Kandidat tidak bersedia relokasi",
        "is_custom": true,
        "created_by": 8
    }
    ```
    
    **Response:**
    - `201 Created`: Rejection reason berhasil dibuat
    """,
    responses={
        201: {"description": "Rejection reason berhasil dibuat"},
    },
)
async def create_rejection_reason(
    reason: RejectionReasonCreate, db: AsyncSession = Depends(get_db)
):
    """
    Membuat rejection reason baru.

    Args:
        reason: Data rejection reason yang akan dibuat.
        db: Database session.

    Returns:
        RejectionReasonResponse: Rejection reason yang baru dibuat.
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


@router.get(
    "/{reason_id}",
    response_model=RejectionReasonResponse,
    summary="Get Rejection Reason by ID",
    description="""
    Mendapatkan detail alasan penolakan berdasarkan ID.
    
    **Format reason_id:** Integer (contoh: `1`)
    
    **Data yang Dikembalikan:**
    - `id`: ID rejection reason
    - `reason_code`: Kode alasan (e.g., SKILL_MISMATCH)
    - `reason_text`: Teks deskripsi alasan
    - `is_custom`: Apakah alasan custom
    - `is_active`: Status aktif
    - `created_by`: ID pembuat
    - `created_at`: Waktu dibuat
    
    **Response:**
    - `200 OK`: Detail rejection reason berhasil diambil
    - `404 Not Found`: Rejection reason tidak ditemukan
    """,
    responses={
        200: {"description": "Detail rejection reason berhasil diambil"},
        404: {"description": "Rejection reason tidak ditemukan"},
    },
)
async def get_rejection_reason(
    reason_id: int = Path(
        ...,
        description="Rejection Reason ID",
        example=1,
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Mendapatkan rejection reason berdasarkan ID.

    Args:
        reason_id: ID rejection reason yang ingin diambil.
        db: Database session.

    Returns:
        RejectionReasonResponse: Detail rejection reason.

    Raises:
        HTTPException: 404 jika tidak ditemukan.
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


@router.patch(
    "/{reason_id}",
    response_model=RejectionReasonResponse,
    summary="Update Rejection Reason",
    description="""
    Update alasan penolakan (partial update).
    
    **Format reason_id:** Integer (contoh: `1`)
    
    **Request Body (partial update):**
    - `reason_code` (optional): Kode alasan baru
    - `reason_text` (optional): Teks deskripsi baru
    - `is_active` (optional): Status aktif
    
    **Contoh Request Body:**
    ```json
    {
        "reason_text": "Keterampilan teknis tidak sesuai dengan kebutuhan posisi"
    }
    ```
    
    **Response:**
    - `200 OK`: Rejection reason berhasil diupdate
    - `404 Not Found`: Rejection reason tidak ditemukan
    """,
    responses={
        200: {"description": "Rejection reason berhasil diupdate"},
        404: {"description": "Rejection reason tidak ditemukan"},
    },
)
async def update_rejection_reason(
    reason_id: int = Path(
        ...,
        description="Rejection Reason ID",
        example=1,
    ),
    reason_update: RejectionReasonUpdate = ...,
    db: AsyncSession = Depends(get_db),
):
    """
    Update rejection reason (partial update).

    Args:
        reason_id: ID rejection reason yang akan diupdate.
        reason_update: Data yang akan diupdate.
        db: Database session.

    Returns:
        RejectionReasonResponse: Rejection reason yang sudah diupdate.

    Raises:
        HTTPException: 404 jika tidak ditemukan.
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


@router.patch(
    "/{reason_id}/deactivate",
    response_model=RejectionReasonResponse,
    summary="Deactivate Rejection Reason",
    description="""
    Menonaktifkan alasan penolakan (soft delete).
    
    **Format reason_id:** Integer (contoh: `1`)
    
    **Tujuan:**
    Endpoint ini digunakan untuk menonaktifkan rejection reason
    tanpa menghapus data dari database.
    
    **Response:**
    - `200 OK`: Rejection reason berhasil dinonaktifkan
    - `404 Not Found`: Rejection reason tidak ditemukan
    
    **Catatan:**
    - Ini adalah soft delete, data tetap ada di database.
    - Rejection reason yang dinonaktifkan tidak muncul di list.
    - Untuk mengaktifkan kembali, gunakan PATCH /{reason_id} dengan `is_active: true`.
    """,
    responses={
        200: {"description": "Rejection reason berhasil dinonaktifkan"},
        404: {"description": "Rejection reason tidak ditemukan"},
    },
)
async def soft_delete_rejection_reason(
    reason_id: int = Path(
        ...,
        description="Rejection Reason ID",
        example=1,
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Menonaktifkan rejection reason (soft delete).

    Args:
        reason_id: ID rejection reason yang akan dinonaktifkan.
        db: Database session.

    Returns:
        RejectionReasonResponse: Rejection reason yang sudah dinonaktifkan.

    Raises:
        HTTPException: 404 jika tidak ditemukan.
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
