from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    IN_REVIEW = "in_review"
    QUALIFIED = "qualified"
    NOT_QUALIFIED = "not_qualified"
    CONTRACT_SIGNED = "contract_signed"

class InterviewStage(str, Enum):
    FIRST_INTERVIEW = "first_interview"
    SECOND_INTERVIEW = "second_interview"
    CONTRACT_PROPOSAL = "contract_proposal"
    CONTRACT_SIGNED = "contract_signed"

class ApplicationBase(BaseModel):
    job_id: int
    candidate_name: str
    candidate_email: EmailStr
    candidate_phone: Optional[str] = None
    candidate_linkedin: Optional[str] = None
    candidate_cv_url: Optional[str] = None
    candidate_education: Optional[str] = None
    candidate_experience_years: Optional[int] = None
    current_company: Optional[str] = None
    current_position: Optional[str] = None
    expected_salary: Optional[str] = None
    notice_period: Optional[str] = None
    application_status: ApplicationStatus = ApplicationStatus.APPLIED
    interview_stage: Optional[InterviewStage] = None
    interview_scheduled_by: Optional[str] = None
    interview_date: Optional[datetime] = None
    source: Optional[str] = None
    notes: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationResponse(ApplicationBase):
    id: int
    candidate_id: int
    fit_score: Optional[float] = None
    skill_score: Optional[float] = None
    experience_score: Optional[float] = None
    overall_score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    applied_date: datetime
    
    class Config:
        from_attributes = True

class ApplicationListResponse(BaseModel):
    applications: List[ApplicationResponse]
    total: int
    filters: Optional[dict] = None
