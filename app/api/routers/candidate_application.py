from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_db
from app.schemas.candidate_application_schema import (
    CandidateApplicationCreate,
    CandidateApplicationRead,
    CandidateApplicationUpdate,
    CandidateApplicationResponse,
)
from app.services.candidate_application_service import (
    create_candidate_application,
    get_candidate_applications,
    get_candidate_application,
    get_candidate_application_with_reason,
    update_candidate_application,
    delete_candidate_application,
)

router = APIRouter(prefix="/candidate-applications", tags=["Candidate Applications"])


@router.post(
    "/",
    response_model=CandidateApplicationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Candidate Application",
    description="""
    Membuat candidate application baru.
    
    **Tujuan:**
    Endpoint ini digunakan untuk mendaftarkan lamaran kandidat baru
    ke dalam sistem.
    
    **Request Body:**
    - `candidate_name` (required): Nama lengkap kandidat
    - `candidate_email` (required): Email kandidat
    - `job_id` (required): ID lowongan yang dilamar
    - `resume_url` (optional): URL ke resume/CV
    - `cover_letter` (optional): Surat lamaran
    - `status` (optional): Status awal (default: applied)
    
    **Contoh Request Body:**
    ```json
    {
        "candidate_name": "John Doe",
        "candidate_email": "john@example.com",
        "job_id": 1,
        "resume_url": "https://example.com/resume.pdf"
    }
    ```
    
    **Response:**
    - `201 Created`: Candidate application berhasil dibuat
    """,
    responses={
        201: {"description": "Candidate application berhasil dibuat"},
    },
)
async def create_candidate(
    candidate: CandidateApplicationCreate, db: AsyncSession = Depends(get_db)
):
    """
    Membuat candidate application baru.

    Args:
        candidate: Data kandidat yang akan didaftarkan.
        db: Database session.

    Returns:
        CandidateApplicationRead: Data kandidat yang baru dibuat.
    """
    return await create_candidate_application(db, candidate)


@router.get(
    "/",
    response_model=List[CandidateApplicationRead],
    summary="List Candidate Applications",
    description="""
    Mendapatkan daftar semua candidate applications dengan pagination.
    
    **Query Parameters:**
    - `skip`: Jumlah record yang di-skip (default: 0)
    - `limit`: Jumlah maksimal record yang dikembalikan (default: 100)
    
    **Data yang Dikembalikan per Item:**
    - `id`: ID candidate application
    - `candidate_name`: Nama kandidat
    - `candidate_email`: Email kandidat
    - `job_id`: ID lowongan yang dilamar
    - `status`: Status lamaran (applied, in_review, rejected, hired)
    - `created_at`: Waktu lamaran dibuat
    - `updated_at`: Waktu terakhir diupdate
    
    **Contoh:**
    - `GET /candidate-applications/?skip=0&limit=10` - Ambil 10 data pertama
    - `GET /candidate-applications/?skip=10&limit=10` - Ambil halaman kedua
    """,
    responses={
        200: {"description": "Daftar candidate applications berhasil diambil"},
    },
)
async def read_candidates(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """
    Mendapatkan semua candidate applications dengan pagination.

    Args:
        skip: Jumlah record yang di-skip untuk pagination.
        limit: Jumlah maksimal record yang dikembalikan.
        db: Database session.

    Returns:
        List[CandidateApplicationRead]: Daftar candidate applications.
    """
    return await get_candidate_applications(db, skip=skip, limit=limit)


@router.get(
    "/{candidate_id}",
    response_model=CandidateApplicationResponse,
    summary="Get Candidate Application Detail",
    description="""
    Mendapatkan detail candidate application berdasarkan ID.
    
    **Format candidate_id:** Integer (contoh: `1`)
    
    **Data yang Dikembalikan:**
    - `id`: ID candidate application
    - `candidate_name`: Nama kandidat
    - `candidate_email`: Email kandidat
    - `job_id`: ID lowongan yang dilamar
    - `status`: Status lamaran
    - `rejection_reason`: Detail alasan rejection (jika ada)
      - `id`: ID reason
      - `reason_code`: Kode alasan
      - `reason_text`: Teks alasan
      - `is_custom`: Apakah alasan custom
    - `created_at`, `updated_at`: Timestamps
    
    **Catatan:**
    - Endpoint ini mengembalikan rejection_reason jika status adalah 'rejected'.
    """,
    responses={
        200: {"description": "Detail candidate application berhasil diambil"},
        404: {"description": "Candidate application tidak ditemukan"},
    },
)
async def read_candidate(candidate_id: int, db: AsyncSession = Depends(get_db)):
    """
    Mendapatkan candidate application berdasarkan ID dengan rejection reason.

    Args:
        candidate_id: ID candidate application yang ingin diambil.
        db: Database session.

    Returns:
        CandidateApplicationResponse: Detail candidate application.

    Raises:
        HTTPException: 404 jika candidate tidak ditemukan.
    """
    candidate = await get_candidate_application_with_reason(db, candidate_id)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate application with id {candidate_id} not found",
        )

    # Convert to response format
    response_data = CandidateApplicationResponse.model_validate(candidate)
    if candidate.rejection_reason:
        response_data.rejection_reason = {
            "id": candidate.rejection_reason.id,
            "reason_code": candidate.rejection_reason.reason_code,
            "reason_text": candidate.rejection_reason.reason_text,
            "is_custom": candidate.rejection_reason.is_custom,
        }

    return response_data


@router.patch(
    "/{candidate_id}",
    response_model=CandidateApplicationRead,
    summary="Update Candidate Application",
    description="""
    Update candidate application (partial update).
    
    **Format candidate_id:** Integer (contoh: `1`)
    
    **Request Body (partial update):**
    - `status` (optional): Status baru
      - Valid values: `applied`, `in_review`, `qualified`, `rejected`, `hired`
    - `rejection_reason_id` (optional): ID alasan rejection
      - Wajib diisi jika status diubah ke `rejected`
    
    **Contoh Request Body - Update Status:**
    ```json
    {
        "status": "in_review"
    }
    ```
    
    **Contoh Request Body - Reject dengan Alasan:**
    ```json
    {
        "status": "rejected",
        "rejection_reason_id": 1
    }
    ```
    
    **Response:**
    - `200 OK`: Candidate application berhasil diupdate
    - `404 Not Found`: Candidate tidak ditemukan
    """,
    responses={
        200: {"description": "Candidate application berhasil diupdate"},
        404: {"description": "Candidate application tidak ditemukan"},
    },
)
async def update_candidate(
    candidate_id: int,
    candidate_update: CandidateApplicationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update candidate application (status dan/atau rejection_reason_id).

    Args:
        candidate_id: ID candidate application yang akan diupdate.
        candidate_update: Data yang akan diupdate.
        db: Database session.

    Returns:
        CandidateApplicationRead: Candidate application yang sudah diupdate.

    Raises:
        HTTPException: 404 jika candidate tidak ditemukan.
    """
    updated_candidate = await update_candidate_application(
        db,
        candidate_id,
        status=candidate_update.status,
        rejection_reason_id=candidate_update.rejection_reason_id,
    )
    if updated_candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate application with id {candidate_id} not found",
        )
    return updated_candidate


@router.delete(
    "/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Candidate Application",
    description="""
    Menghapus candidate application dari database.
    
    **Format candidate_id:** Integer (contoh: `1`)
    
    **Response:**
    - `204 No Content`: Candidate application berhasil dihapus
    - `404 Not Found`: Candidate tidak ditemukan
    
    **Catatan:**
    - Operasi ini bersifat permanen dan tidak dapat di-undo.
    - Pastikan untuk mengkonfirmasi dengan user sebelum menghapus.
    """,
    responses={
        204: {"description": "Candidate application berhasil dihapus"},
        404: {"description": "Candidate application tidak ditemukan"},
    },
)
async def delete_candidate(candidate_id: int, db: AsyncSession = Depends(get_db)):
    """
    Menghapus candidate application.

    Args:
        candidate_id: ID candidate application yang akan dihapus.
        db: Database session.

    Returns:
        None: Tidak mengembalikan content (204).

    Raises:
        HTTPException: 404 jika candidate tidak ditemukan.
    """
    success = await delete_candidate_application(db, candidate_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate application with id {candidate_id} not found",
        )
    return None
