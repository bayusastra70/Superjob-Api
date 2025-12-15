from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.reminder import ReminderStatus, ReminderTaskType


class ReminderBase(BaseModel):
    task_title: str = Field(..., max_length=255)
    task_type: ReminderTaskType
    redirect_url: str = Field(..., max_length=1024)
    job_id: Optional[str] = None
    candidate_id: Optional[int] = None
    due_at: Optional[datetime] = None


class ReminderCreate(ReminderBase):
    pass


class ReminderUpdate(BaseModel):
    task_title: Optional[str] = Field(None, max_length=255)
    task_type: Optional[ReminderTaskType] = None
    redirect_url: Optional[str] = Field(None, max_length=1024)
    job_id: Optional[str] = None
    candidate_id: Optional[int] = None
    due_at: Optional[datetime] = None
    status: Optional[ReminderStatus] = None


class ReminderResponse(ReminderBase):
    id: str
    employer_id: int
    status: ReminderStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
