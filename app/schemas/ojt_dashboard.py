from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.ojt_agenda import OjtAgendaResponse
from app.schemas.ojt_task import OjtTaskResponse

class OjtProgramSummary(BaseModel):
    id: int
    title: str
    trainer_name: Optional[str] = None
    role: Optional[str] = None
    progress_percentage: float = 0.0 # Berdasarkan tasks completed
    status: str # ongoing
    
    model_config = {"from_attributes": True}

class OjtDashboardData(BaseModel):
    active_program: Optional[OjtProgramSummary] = None
    upcoming_agenda: Optional[OjtAgendaResponse] = None
    pending_tasks_count: int = 0
    attendance_summary: str = "0/0" # "8/10"
    recent_tasks: List[OjtTaskResponse] = []
