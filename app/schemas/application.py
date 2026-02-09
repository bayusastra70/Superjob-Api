
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
    rank: Optional[int] = None
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
    page: int = 0
    total_pages: Optional[int] = None
    


class ApplicationCreate(BaseModel):
    job_id: int
    coverletter: Optional[str] = None
    portfolio: Optional[str] = None  # Untuk link portfolio

    candidate_name: Optional[str] = None  # Untuk backward compatibility
    candidate_email: Optional[EmailStr] = None  # Untuk backward compatibility
    candidate_phone: Optional[str] = None  # Untuk backward compatibility

class ApplicationCreateForm(BaseModel):
    # Hanya untuk response/validation, bukan untuk request
    job_id: int
    coverletter: Optional[str] = None
    portfolio: Optional[str] = None

class JobPreferencesResponse(BaseModel):
    """Job preferences response schema"""

    preferred_locations: Optional[List[str]] = None
    preferred_work_modes: Optional[List[str]] = None
    preferred_job_types: Optional[List[str]] = None
    expected_salary_min: Optional[float] = None
    expected_salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    preferred_industries: Optional[List[str]] = None
    preferred_divisions: Optional[List[str]] = None
    auto_apply_enabled: Optional[bool] = False

    class Config:
        from_attributes = True

class ApplicationDetailResponse(BaseModel):
    """Detailed application response matching user profile structure"""
    id: int
    user_id: Optional[int] = None
    email: str
    full_name: str
    phone: Optional[str] = None
    user_profile: Optional[str] = None
    linkedin_url: Optional[str] = None
    role: str = "candidate"  # Default role untuk kandidat
    cv_url: Optional[str] = None
    
    # CV extracted fields
    summary: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = []
    languages: List[str] = []
    experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    certifications: List[Dict[str, Any]] = []
    
    # Job preferences
    job_preferences: Optional[JobPreferencesResponse] = None
    
    # Application specific fields (tambahan)
    application_id: int = Field(alias="id", exclude=True)  # Untuk backward compatibility
    job_id: Optional[int] = None
    position: Optional[str] = None
    application_status: Optional[str] = None
    fit_score: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Additional application data
    files: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True
        populate_by_name = True


class ApplicationStatusUpdateItem(BaseModel):
    application_id: int
    status: str
    notes: Optional[str] = None

class BulkUpdateStatusRequest(BaseModel):
    list_data: List[ApplicationStatusUpdateItem] = Field(
        ...,
        min_items=1,
        description="List of applications to update with their new status and notes"
    )


class ApplicationActiveItem(BaseModel):
    """Active application item schema - matches active UI fields"""
    id: int
    job_id: int
    title: str
    company_name: str
    company_logo: Optional[str]
    location: str
    applied_at: datetime
    status: str


class ApplicationHistoryItem(BaseModel):
    """History application item schema - matches history UI fields"""
    id: int
    job_id: int
    title: str
    company_name: str
    company_logo: Optional[str]
    status: str


class ApplicationActiveHistoryListResponse(BaseModel):
    """Response for active/history application list"""
    applications: List[Any]  # Will be ApplicationActiveItem or ApplicationHistoryItem
    total: int
    limit: int
    page: int
    total_pages: int