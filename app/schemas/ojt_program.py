from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OjtProgramStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TrainingType(str, Enum):
    ONSITE = "onsite"
    REMOTE = "remote"
    HYBRID = "hybrid"


def format_duration(days: int) -> str:
    """Konversi jumlah hari ke format yang mudah dibaca.
    
    Contoh:
        90  → '3 bulan'
        75  → '2 bulan 15 hari'
        14  → '2 minggu'
        7   → '1 minggu'
        45  → '1 bulan 15 hari'
    """
    if days is None:
        return None

    months = days // 30
    remaining = days % 30
    weeks = remaining // 7
    remaining_days = remaining % 7

    parts = []
    if months > 0:
        parts.append(f"{months} bulan")
    if weeks > 0 and months == 0:
        parts.append(f"{weeks} minggu")
        if remaining_days > 0:
            parts.append(f"{remaining_days} hari")
    elif remaining > 0 and months > 0:
        parts.append(f"{remaining} hari")
    elif months == 0 and weeks == 0:
        parts.append(f"{days} hari")

    return " ".join(parts)


class CompanyInfo(BaseModel):
    """Info singkat company untuk ditampilkan di OJT list/detail"""
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None


class OjtProgramResponse(BaseModel):
    """Data program OJT yang dikembalikan ke frontend"""

    id: int
    title: str
    description: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    duration_days: Optional[int] = None
    duration_display: Optional[str] = None
    company_id: Optional[int] = None
    company: Optional[CompanyInfo] = None
    trainer_id: Optional[int] = None
    trainer_name: Optional[str] = None
    max_participants: Optional[int] = None
    current_participants: Optional[int] = None
    requirements: Optional[str] = None
    skills: Optional[List[str]] = None
    training_type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_duration_display(self):
        """Otomatis hitung duration_display dari duration_days"""
        if self.duration_days and not self.duration_display:
            self.duration_display = format_duration(self.duration_days)
        return self


class OjtProgramListData(BaseModel):
    """Wrapper untuk list program + total (pagination)"""

    programs: List[OjtProgramResponse] = []
    total: int = 0
    page: int = 1
    total_pages: int = 1


