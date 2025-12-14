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

@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user's notifications"""
    try:
        result = await notification_service.get_user_notifications(
            current_user.id, limit, offset
        )
        
        return NotificationListResponse(
            notifications=result["notifications"],
            total_unread=result["total_unread"]
        )
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Mark a notification as read"""
    try:
        success = await notification_service.mark_as_read(notification_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {
            "message": "Notification marked as read",
            "notification_id": notification_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/read-all")
async def mark_all_notifications_as_read(
    current_user: UserResponse = Depends(get_current_user)
):
    """Mark all notifications as read"""
    try:
        success = await notification_service.mark_all_as_read(current_user.id)
        
        return {
            "message": "All notifications marked as read",
            "success": success
        }
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))