from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class JobOut(BaseModel):
    """Output schema for Job - uses Integer ID"""

    id: int
    employer_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    major: Optional[str] = None
    working_type: Optional[str] = None
    gender_requirement: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_interval: Optional[str] = None
    skills: Optional[list[str]] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    education: Optional[str] = None
    responsibilities: Optional[str] = None
    qualifications: Optional[str] = None
    benefits: Optional[str] = None
    ai_interview_enabled: Optional[bool] = None
    ai_interview_questions_count: Optional[int] = None
    ai_interview_duration_seconds: Optional[int] = None
    ai_interview_deadline_days: Optional[int] = None
    ai_interview_questions: Optional[str] = None
    contact_url: Optional[str] = None
    status: str
    job_code: Optional[str] = None
    department: Optional[str] = None
    requirements: Optional[str] = None
    created_by: Optional[int] = None
    company_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobList(BaseModel):
    """List of jobs with pagination"""

    items: List[JobOut]
    total: int


class JobCreate(BaseModel):
    """Schema for creating a new job"""

    title: str
    description: Optional[str] = None
    industry: Optional[str] = None
    major: Optional[str] = None
    working_type: Optional[str] = None
    gender_requirement: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_interval: Optional[str] = None
    skills: Optional[list[str]] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    education: Optional[str] = None
    responsibilities: Optional[str] = None
    qualifications: Optional[str] = None
    benefits: Optional[str] = None
    ai_interview_enabled: Optional[bool] = False
    ai_interview_questions_count: Optional[int] = None
    ai_interview_duration_seconds: Optional[int] = None
    ai_interview_deadline_days: Optional[int] = None
    ai_interview_questions: Optional[str] = None
    contact_url: Optional[str] = None
    status: Optional[str] = None


# Backward compatibility aliases
JobPostingOut = JobOut
JobPostingList = JobList
JobPostingCreate = JobCreate
