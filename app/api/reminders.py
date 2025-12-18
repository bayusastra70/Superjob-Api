from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.reminder import ReminderTask, ReminderStatus
from app.schemas.reminder import ReminderCreate, ReminderUpdate, ReminderResponse
from app.services.socketio_emitter import (
    emit_reminder_created,
    emit_reminder_updated,
)

router = APIRouter(prefix="/employers/{employer_id}/reminders", tags=["reminders"])


@router.get(
    "",
    response_model=List[ReminderResponse],
    status_code=status.HTTP_200_OK,
    summary="List Reminders",
    description="""
    Mendapatkan daftar reminder/task untuk employer.
    
    **Format employer_id:** Integer
    
    **Status yang valid:** pending, done, ignored
    
    **Test Data yang tersedia:**
    - employer_id `8` (employer@superjob.com) - 6 reminders
    - employer_id `3` (tanaka@gmail.com) - 1 reminder
    """,
)
async def list_reminders(
    employer_id: int = Path(
        ...,
        description="ID Employer. Gunakan 8 atau 3 untuk testing.",
        example=8,
    ),
    status: Optional[str] = Query(
        ReminderStatus.pending.value,
        description="Filter by status (pending, done, ignored). Kosongkan untuk semua.",
    ),
    db: AsyncSession = Depends(get_db),
) -> List[ReminderResponse]:
    stmt = select(ReminderTask).where(ReminderTask.employer_id == employer_id)
    if status not in (None, ""):
        try:
            status_enum = ReminderStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status filter",
            )
        stmt = stmt.where(ReminderTask.status == status_enum)

    stmt = stmt.order_by(
        ReminderTask.due_at.asc().nulls_last(),
        ReminderTask.created_at.desc(),
    )

    try:
        reminders = (await db.execute(stmt)).scalars().all()
    except SQLAlchemyError as exc:
        logger.exception(
            "Failed to fetch reminders",
            exc=exc,
            employer_id=str(employer_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch reminders",
        )

    return reminders


@router.post(
    "",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Reminder",
    description="""
    Membuat reminder/task baru untuk employer.
    
    **Tujuan:**
    Endpoint ini digunakan untuk membuat pengingat atau tugas baru
    yang akan ditampilkan di dashboard employer.
    
    **Request Body:**
    - `title` (required): Judul reminder
    - `description` (optional): Deskripsi detail reminder
    - `due_at` (optional): Waktu deadline dalam format ISO 8601
    - `status` (optional): Status awal (default: pending)
    
    **Contoh Request Body:**
    ```json
    {
        "title": "Follow up dengan kandidat John",
        "description": "Hubungi untuk jadwal interview",
        "due_at": "2024-01-20T10:00:00Z"
    }
    ```
    
    **Response:**
    - `201 Created`: Reminder berhasil dibuat
    - `500 Internal Server Error`: Gagal membuat reminder
    
    **Catatan:**
    - Setelah reminder dibuat, event WebSocket akan dikirim ke frontend.
    - Jika WebSocket gagal, API tetap sukses (frontend bisa poll).
    """,
    responses={
        201: {"description": "Reminder berhasil dibuat"},
        500: {"description": "Gagal membuat reminder"},
    },
)
async def create_reminder(
    employer_id: int = Path(
        ...,
        description="ID Employer yang membuat reminder",
        example=8,
    ),
    payload: ReminderCreate = ...,
    db: AsyncSession = Depends(get_db),
) -> ReminderResponse:
    """
    Membuat reminder baru untuk employer.

    Args:
        employer_id: ID employer pemilik reminder.
        payload: Data reminder yang akan dibuat.
        db: Database session.

    Returns:
        ReminderResponse: Reminder yang baru dibuat.

    Raises:
        HTTPException: 500 jika gagal menyimpan ke database.
    """
    reminder = ReminderTask(
        employer_id=employer_id,
        **payload.model_dump(),
    )

    db.add(reminder)
    try:
        await db.commit()
        await db.refresh(reminder)
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.exception(
            "Failed to create reminder task",
            exc=exc,
            employer_id=employer_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create reminder task",
        )

    try:
        await emit_reminder_created(reminder)
    except Exception:
        # Do not fail API if event emission breaks; FE can poll as fallback.
        logger.exception(
            "Failed to emit reminder_created event",
            employer_id=str(employer_id),
            reminder_id=str(reminder.id),
        )

    return reminder


@router.patch(
    "/{reminder_id}",
    response_model=ReminderResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Reminder",
    description="""
    Mengupdate reminder/task yang sudah ada.
    
    **Tujuan:**
    Endpoint ini digunakan untuk mengubah data reminder,
    termasuk menandai sebagai selesai (done) atau diabaikan (ignored).
    
    **Format reminder_id:** String UUID (contoh: `abc12345-...`)
    
    **Request Body (partial update):**
    - `title` (optional): Judul reminder baru
    - `description` (optional): Deskripsi baru
    - `due_at` (optional): Deadline baru
    - `status` (optional): Status baru (pending, done, ignored)
    
    **Contoh Request Body:**
    ```json
    {
        "status": "done"
    }
    ```
    
    **Response:**
    - `200 OK`: Reminder berhasil diupdate
    - `403 Forbidden`: Tidak memiliki akses ke reminder ini
    - `404 Not Found`: Reminder tidak ditemukan
    - `500 Internal Server Error`: Gagal mengupdate reminder
    
    **Auto-hide Behavior:**
    - Jika status diubah ke `done` atau `ignored`, reminder akan
      otomatis tersembunyi dari tampilan default frontend.
    
    **Catatan:**
    - Setelah update, event WebSocket akan dikirim ke frontend.
    - Hanya employer pemilik yang bisa mengupdate reminder.
    """,
    responses={
        200: {"description": "Reminder berhasil diupdate"},
        403: {"description": "Tidak memiliki akses ke reminder ini"},
        404: {"description": "Reminder tidak ditemukan"},
        500: {"description": "Gagal mengupdate reminder"},
    },
)
async def update_reminder(
    employer_id: int = Path(
        ...,
        description="ID Employer pemilik reminder",
        example=8,
    ),
    reminder_id: str = Path(
        ...,
        description="ID Reminder yang akan diupdate (UUID format)",
    ),
    payload: ReminderUpdate = ...,
    db: AsyncSession = Depends(get_db),
) -> ReminderResponse:
    """
    Mengupdate reminder yang sudah ada.

    Args:
        employer_id: ID employer pemilik reminder.
        reminder_id: ID reminder yang akan diupdate.
        payload: Data yang akan diupdate (partial).
        db: Database session.

    Returns:
        ReminderResponse: Reminder yang sudah diupdate.

    Raises:
        HTTPException: 403 jika bukan pemilik reminder.
        HTTPException: 404 jika reminder tidak ditemukan.
        HTTPException: 500 jika gagal menyimpan ke database.
    """
    # reminder_id is String(36) in database
    reminder = await db.get(ReminderTask, reminder_id)

    if reminder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
        )

    if reminder.employer_id != employer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to modify this reminder",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reminder, field, value)

    # Auto-hide behavior: if status moves to done/ignored, reminder stops showing on FE.
    if reminder.status in {ReminderStatus.done, ReminderStatus.ignored}:
        logger.debug(
            "Reminder status changed to terminal state; reminder will be hidden",
            reminder_id=str(reminder_id),
            status=reminder.status.value,
        )

    try:
        await db.commit()
        await db.refresh(reminder)
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.exception(
            "Failed to update reminder task",
            exc=exc,
            reminder_id=reminder_id,
            employer_id=employer_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reminder task",
        )

    try:
        await emit_reminder_updated(reminder)
    except Exception:
        logger.exception(
            "Failed to emit reminder_updated event",
            employer_id=str(employer_id),
            reminder_id=str(reminder_id),
        )

    return reminder
