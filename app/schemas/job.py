from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Optional
from datetime import datetime
from enum import Enum

import uuid

class JobStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    DRAFT = "draft"

class JobBase(BaseModel):
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    education_requirement: Optional[str] = None
    salary_range: Optional[str] = None
    status: JobStatus = JobStatus.OPEN
    description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None

class JobCreate(JobBase):
    job_code: Optional[str] = None

class JobResponse(JobBase):
    id: int
    job_code: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int



class JobQualityResponse(BaseModel):
    job_id: uuid.UUID
    score: Optional[float] = Field(None, ge=0, le=100)
    grade: Optional[str] = None
    optimal: Optional[bool] = None
    details: Optional[Dict[str, float]] = None
    message: Optional[str] = None
    suggestions: Optional[list[str]] = None

    model_config = ConfigDict(from_attributes=True)


class JobUpdate(BaseModel):
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
    status: Optional[str] = None
