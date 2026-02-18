from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    EXCUSED = "excused"

class OjtAttendanceCreate(BaseModel):
    agenda_id: int
    notes: Optional[str] = None
    # status default to 'present', but can be updated by admin/trainer
    # talent only needs agenda_id to clock in

class OjtAttendanceUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    checked_in_at: Optional[datetime] = None

class OjtAttendanceResponse(BaseModel):
    id: int
    agenda_id: int
    talent_id: int
    status: str
    checked_in_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    
    # Optional fields for list views
    talent_name: Optional[str] = None
    agenda_title: Optional[str] = None

    model_config = {"from_attributes": True}
