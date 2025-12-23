
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    SHORTLISTED = "shortlisted"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    HIRED = "hired"

class InterviewStage(str, Enum):
    SCREENING = "screening"
    TECHNICAL = "technical"
    HR = "hr"
    FINAL = "final"

class ApplicationBase(BaseModel):
    # Data dari tabel applications
    job_id: int
    candidate_id: int  # Diperlukan untuk join dengan users
    
    # Data dari tabel users
    name: str  # Dari u.full_name
    email: EmailStr  # Dari u.email
    phone: Optional[str] = None  # Dari u.phone
    
    # Data dari tabel jobs
    position: str  # Dari j.title
    
    # Data dari tabel applications
    candidate_linkedin: Optional[str] = None
    candidate_cv_url: Optional[str] = None
    candidate_education: Optional[str] = None
    candidate_experience_years: Optional[int] = None
    current_company: Optional[str] = None
    current_position: Optional[str] = None
    expected_salary: Optional[str] = None
    notice_period: Optional[str] = None
    
    # Status dan scoring
    application_status: ApplicationStatus = ApplicationStatus.APPLIED
    fit_score: Optional[float] = None  # Kolom baru dari query
    
    # Interview info
    interview_stage: Optional[InterviewStage] = None
    interview_scheduled_by: Optional[str] = None
    interview_date: Optional[datetime] = None
    
    # Additional info
    source: Optional[str] = None
    notes: Optional[str] = None
    
    # Timestamps dari query
    created_at: datetime
    updated_at: datetime
    
    # Additional fields dari query
    linkedin: Optional[str] = None  # Alias untuk candidate_linkedin
    cv: Optional[str] = None  # Alias untuk candidate_cv_url
    education: Optional[str] = None  # Alias untuk candidate_education
    message: Optional[str] = None  # Field placeholder dari query

class ApplicationCreate(ApplicationBase):
    # Untuk create operation, beberapa field mungkin optional
    candidate_name: Optional[str] = None  # Untuk backward compatibility
    candidate_email: Optional[EmailStr] = None  # Untuk backward compatibility
    candidate_phone: Optional[str] = None  # Untuk backward compatibility

class ApplicationResponse(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    job_id: Optional[int] = None
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    education: Optional[str] = None
    linkedin: Optional[str] = None
    cv: Optional[str] = None
    status: Optional[str] = None
    fit_score: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ApplicationFilter(BaseModel):
    # Model untuk filtering
    job_id: Optional[int] = None
    status: Optional[str] = None
    search: Optional[str] = None
    limit: int = 50
    offset: int = 0
    sort_by: str = "created_at"
    sort_order: str = "desc"

class ApplicationListResponse(BaseModel):
    # Response untuk list applications
    applications: List[ApplicationResponse]
    total: int
    limit: int = 50
    offset: int = 0
    filters: Optional[Dict[str, Any]] = None