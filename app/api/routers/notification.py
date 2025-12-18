# app/routes/notification.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from app.schemas.notification import NotificationListResponse
from app.services.notification_service import notification_service
from app.core.security import get_current_user
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="Get User Notifications",
    description="""
    Mendapatkan daftar notifikasi untuk user yang sedang login.
    
    **Query Parameters:**
    - `limit`: Jumlah maksimal notifikasi (default: 50, max: 100)
    - `offset`: Offset untuk pagination (default: 0)
    
    **Data yang Dikembalikan:**
    - `notifications`: Array notifikasi
      - `id`: ID notifikasi
      - `type`: Tipe notifikasi (new_applicant, message, reminder, etc.)
      - `title`: Judul notifikasi
      - `message`: Isi notifikasi
      - `is_read`: Status baca
      - `created_at`: Waktu dibuat
      - `data`: Data tambahan (metadata)
    - `total_unread`: Total notifikasi yang belum dibaca
    
    **Contoh Response:**
    ```json
    {
        "notifications": [
            {
                "id": "notif-123",
                "type": "new_applicant",
                "title": "Pelamar Baru",
                "message": "John Doe melamar posisi Software Engineer",
                "is_read": false,
                "created_at": "2024-01-15T10:30:00Z"
            }
        ],
        "total_unread": 5
    }
    ```
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Daftar notifikasi berhasil diambil"},
        500: {"description": "Internal server error"},
    },
)
async def get_notifications(
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Jumlah maksimal notifikasi",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Offset untuk pagination",
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Mendapatkan daftar notifikasi untuk user yang sedang login.

    Args:
        limit: Jumlah maksimal notifikasi.
        offset: Offset untuk pagination.
        current_user: User yang sedang login.

    Returns:
        NotificationListResponse: Daftar notifikasi dengan total unread.

    Raises:
        HTTPException: 500 jika terjadi error.
    """
    try:
        result = await notification_service.get_user_notifications(
            current_user.id, limit, offset
        )

        return NotificationListResponse(
            notifications=result["notifications"], total_unread=result["total_unread"]
        )

    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{notification_id}/read",
    summary="Mark Notification as Read",
    description="""
    Menandai notifikasi tertentu sebagai sudah dibaca.
    
    **Format notification_id:** String (contoh: `notif-123`)
    
    **Response:**
    - `200 OK`: Notifikasi berhasil ditandai sebagai dibaca
    - `404 Not Found`: Notifikasi tidak ditemukan
    
    **⚠️ Membutuhkan Authorization Token!**
    
    **Catatan:**
    - Hanya notifikasi milik user yang bisa ditandai.
    - Notifikasi yang sudah read tetap bisa di-mark lagi (idempotent).
    """,
    responses={
        200: {"description": "Notifikasi berhasil ditandai sebagai dibaca"},
        404: {"description": "Notifikasi tidak ditemukan"},
        500: {"description": "Internal server error"},
    },
)
async def mark_notification_as_read(
    notification_id: str, current_user: UserResponse = Depends(get_current_user)
):
    """
    Menandai notifikasi tertentu sebagai sudah dibaca.

    Args:
        notification_id: ID notifikasi yang akan ditandai.
        current_user: User yang sedang login.

    Returns:
        dict: Message sukses dengan notification_id.

    Raises:
        HTTPException: 404 jika notifikasi tidak ditemukan.
        HTTPException: 500 jika terjadi error.
    """
    try:
        success = await notification_service.mark_as_read(
            notification_id, current_user.id
        )

        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {
            "message": "Notification marked as read",
            "notification_id": notification_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/read-all",
    summary="Mark All Notifications as Read",
    description="""
    Menandai semua notifikasi user sebagai sudah dibaca.
    
    **Tujuan:**
    Endpoint ini digunakan untuk menandai semua notifikasi
    yang belum dibaca menjadi sudah dibaca sekaligus.
    
    **Response:**
    - `message`: Pesan sukses
    - `success`: Boolean status operasi
    
    **⚠️ Membutuhkan Authorization Token!**
    
    **Catatan:**
    - Berguna untuk fitur "Mark all as read" di UI.
    - Operasi ini atomic (semua atau tidak sama sekali).
    """,
    responses={
        200: {"description": "Semua notifikasi berhasil ditandai sebagai dibaca"},
        500: {"description": "Internal server error"},
    },
)
async def mark_all_notifications_as_read(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Menandai semua notifikasi user sebagai sudah dibaca.

    Args:
        current_user: User yang sedang login.

    Returns:
        dict: Message sukses dengan status.

    Raises:
        HTTPException: 500 jika terjadi error.
    """
    try:
        success = await notification_service.mark_all_as_read(current_user.id)

        return {"message": "All notifications marked as read", "success": success}

    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))
