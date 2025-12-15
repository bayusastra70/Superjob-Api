from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class JobPostingOut(BaseModel):
    id: str
    employer_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    skills: Optional[list[str]] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    education: Optional[str] = None
    benefits: Optional[str] = None
    contact_url: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobPostingList(BaseModel):
    items: List[JobPostingOut]
    total: int


class JobPostingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    skills: Optional[list[str]] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    education: Optional[str] = None
    benefits: Optional[str] = None
    contact_url: Optional[str] = None
    status: Optional[str] = None
