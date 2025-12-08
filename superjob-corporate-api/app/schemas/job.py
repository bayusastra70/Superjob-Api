from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

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