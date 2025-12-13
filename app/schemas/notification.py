# app/schemas/notification.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationBase(BaseModel):
    user_id: str
    title: str
    message: str
    notification_type: str = "message"
    data: Optional[dict] = None
    thread_id: Optional[str] = None

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    id: str
    is_read: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True

class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total_unread: int