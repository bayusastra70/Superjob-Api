from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.ojt_attendance import OjtAttendanceResponse  # Forward reference

class OjtAgendaBase(BaseModel):
    title: str
    description: Optional[str] = None
    session_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    order_number: Optional[int] = None

class OjtAgendaCreate(OjtAgendaBase):
    pass

class OjtAgendaUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    session_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    order_number: Optional[int] = None
    trainer_id: Optional[int] = None

class OjtAgendaResponse(OjtAgendaBase):
    id: int
    program_id: int
    trainer_id: Optional[int] = None
    trainer_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Untuk detail view, bisa ada status attendance user ini
    user_attendance: Optional[str] = None # present/absent/excused/none

    model_config = {"from_attributes": True}

class OjtAgendaList(BaseModel):
    agendas: List[OjtAgendaResponse]
    total: int
