from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OjtProgramStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class OjtProgramResponse(BaseModel):
    """Data program OJT yang dikembalikan ke frontend"""

    id: int
    title: str
    description: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    duration_days: Optional[int] = None
    trainer_id: Optional[int] = None
    trainer_name: Optional[str] = None
    max_participants: Optional[int] = None
    current_participants: Optional[int] = None
    requirements: Optional[str] = None
    skills: Optional[List[str]] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OjtProgramListData(BaseModel):
    """Wrapper untuk list program + total (pagination)"""

    programs: List[OjtProgramResponse] = []
    total: int = 0
    page: int = 1
    total_pages: int = 1
