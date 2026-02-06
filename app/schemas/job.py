from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal


class JobStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class WorkingType(str, Enum):
    ONSITE = "onsite"
    REMOTE = "remote"
    HYBRID = "hybrid"


class GenderRequirement(str, Enum):
    ANY = "any"
    MALE = "male"
    FEMALE = "female"


class SalaryInterval(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class JobBase(BaseModel):
    """Base schema untuk Job dengan semua field sesuai UI flow"""

    # === Step 1: Informasi Dasar Pekerjaan ===
    title: str = Field(..., description="Job Position / Jabatan")
    industry: Optional[str] = Field(None, description="Industri")
    education_requirement: Optional[str] = Field(
        None, description="Pendidikan Terakhir"
    )
    major: Optional[str] = Field(None, description="Jurusan")
    employment_type: Optional[str] = Field(
        None,
        description="Contract Type / Jenis Kontrak (Full-Time, Part-Time, Contract)",
    )
    experience_level: Optional[str] = Field(None, description="Experience / Pengalaman")
    working_type: Optional[WorkingType] = Field(
        WorkingType.ONSITE,
        description="Working Type / Jenis Kerja (On-site, Remote, Hybrid)",
    )
    location: Optional[str] = Field(None, description="Lokasi")
    gender_requirement: Optional[GenderRequirement] = Field(
        GenderRequirement.ANY, description="Gender / Jenis Kelamin"
    )

    # Salary fields
    salary_min: Optional[Decimal] = Field(None, description="Gaji minimum")
    salary_max: Optional[Decimal] = Field(None, description="Gaji maksimum")
    salary_currency: Optional[str] = Field("IDR", description="Mata uang gaji")
    salary_interval: Optional[SalaryInterval] = Field(
        SalaryInterval.MONTHLY, description="Interval gaji (per bulan, tahun, dll)"
    )

    # Age range
    min_age: Optional[int] = Field(None, ge=17, le=65, description="Usia minimal")
    max_age: Optional[int] = Field(None, ge=17, le=65, description="Usia maksimal")

    # Other basic fields
    department: Optional[str] = Field(None, description="Department")
    salary_range: Optional[str] = Field(None, description="Salary range display text")
    status: JobStatus = Field(JobStatus.DRAFT, description="Status lowongan")

    company_id: Optional[int] = Field(None, description="ID Perusahaan")

    # === Step 2: Persyaratan ===
    description: Optional[str] = Field(None, description="Deskripsi Pekerjaan")
    responsibilities: Optional[str] = Field(None, description="Tanggung Jawab")
    qualifications: Optional[str] = Field(None, description="Kualifikasi")
    requirements: Optional[str] = Field(None, description="Requirements (legacy field)")
    benefits: Optional[str] = Field(None, description="Keuntungan")

    # === Step 3: AI Interview Settings ===
    ai_interview_enabled: Optional[bool] = Field(
        False, description="Aktifkan AI Interview untuk posisi ini"
    )
    ai_interview_questions_count: Optional[int] = Field(
        None, ge=1, le=20, description="Jumlah Pertanyaan"
    )
    ai_interview_duration_seconds: Optional[int] = Field(
        None, ge=30, le=600, description="Durasi Menjawab (detik)"
    )
    ai_interview_deadline_days: Optional[int] = Field(
        None, ge=1, le=30, description="Batas Waktu Interview (hari)"
    )
    ai_interview_questions: Optional[str] = Field(
        None, description="Daftar Pertanyaan (rich text)"
    )

    class Config:
        json_encoders = {
            Decimal: lambda v: float(f"{v:.2f}")  # Format dengan 2 decimal
        }


class JobCreate(JobBase):
    """Schema untuk membuat job baru"""

    job_code: Optional[str] = Field(None, description="Kode job unik")


class CompanyResponse(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None

    class Config:
        from_attributes = True


class SimilarJob(BaseModel):
    id: int
    title: Optional[str] = None
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_banner_url: Optional[str] = None
    experience_level: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    description: Optional[str] = None
    is_bookmark: Optional[bool] = None
    employment_type: Optional[str] = None
    working_type: Optional[str] = None
    is_scam: Optional[bool] = None
    last_recruiter_active_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobResponse(JobBase):
    """Schema untuk response job"""

    id: int
    job_code: Optional[str] = None
    is_bookmark: Optional[bool] = None
    company_id: Optional[int] = None
    company: Optional[CompanyResponse] = None
    is_scam: Optional[bool] = None
    last_recruiter_active_at: Optional[datetime] = None
    similar_jobs: Optional[List[SimilarJob]] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    expired_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    count_views: int = 0
    count_applications: int = 0

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        if v == "" or v is None:
            return JobStatus.DRAFT
        return v

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Schema untuk list job response"""

    jobs: List[JobResponse]
    total: Optional[int] = None
    page: Optional[int] = None
    limit: Optional[int] = None
    total_pages: Optional[int] = None


class JobQualityResponse(BaseModel):
    """Schema untuk job quality score"""

    job_id: int  # Integer primary key after consolidation
    score: Optional[float] = Field(None, ge=0, le=100)
    grade: Optional[str] = None
    optimal: Optional[bool] = None
    details: Optional[Dict[str, float]] = None
    message: Optional[str] = None
    suggestions: Optional[list[str]] = None

    model_config = ConfigDict(from_attributes=True)


class JobUpdate(BaseModel):
    """Schema untuk update job - semua field optional"""

    # === Step 1: Informasi Dasar ===
    title: Optional[str] = None
    industry: Optional[str] = None
    education: Optional[str] = None
    major: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    working_type: Optional[WorkingType] = None
    location: Optional[str] = None
    gender_requirement: Optional[GenderRequirement] = None

    # Salary fields
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    salary_currency: Optional[str] = None
    salary_interval: Optional[SalaryInterval] = None

    # Age range
    min_age: Optional[int] = Field(None, ge=17, le=65)
    max_age: Optional[int] = Field(None, ge=17, le=65)

    # === Step 2: Persyaratan ===
    description: Optional[str] = None
    responsibilities: Optional[str] = None
    qualifications: Optional[str] = None
    benefits: Optional[str] = None

    # === Step 3: AI Interview ===
    ai_interview_enabled: Optional[bool] = None
    ai_interview_questions_count: Optional[int] = Field(None, ge=1, le=20)
    ai_interview_duration_seconds: Optional[int] = Field(None, ge=30, le=600)
    ai_interview_deadline_days: Optional[int] = Field(None, ge=1, le=30)
    ai_interview_questions: Optional[str] = None

    # Other fields
    skills: Optional[list[str]] = None
    contact_url: Optional[str] = None
    status: Optional[str] = None


class PublicJobResponse(BaseModel):
    """Restricted job data for public landing page"""

    id: int
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    working_type: Optional[WorkingType] = None
    experience_level: Optional[str] = None
    description: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = "IDR"
    salary_interval: Optional[SalaryInterval] = SalaryInterval.MONTHLY
    created_at: datetime
    company_name: Optional[str] = None
    company_logo: Optional[str] = None

    class Config:
        from_attributes = True


class PublicJobListData(BaseModel):
    """Data content for public jobs list"""

    jobs: List[PublicJobResponse]
    total: int


class JobRecommendationItem(BaseModel):
    """Item job untuk recommendation response"""

    id: int
    title: str
    company_name: Optional[str] = None
    company_logo: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    working_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    salary_currency: Optional[str] = "IDR"
    salary_interval: Optional[str] = "monthly"
    match_score: float = Field(..., ge=0.0, le=100.0)
    match_reasons: List[str] = Field(default_factory=list)
    is_bookmarked: bool = Field(default=False)
    created_at: datetime

    class Config:
        from_attributes = True


class JobRecommendationResponse(BaseModel):
    """Response untuk job recommendations dengan pagination"""

    jobs: List[JobRecommendationItem]
    match_criteria: Dict[str, Any] = Field(default_factory=dict)
    user_id: int
    total: int
    page: Optional[int] = None
    limit: Optional[int] = None
    total_pages: Optional[int] = None
    has_next: Optional[bool] = None
    has_previous: Optional[bool] = None

    class Config:
        from_attributes = True


class AIInterviewRequest(BaseModel):
    """Schema untuk generate interview questions"""
    title: str
    department: Optional[str] = None
    experience_level: Optional[str] = None
    num_questions: int = 5
    question_type: str = "mixed"

class AIInterviewResponse(BaseModel):
    """Schema untuk response interview questions"""
    success: bool
    questions: List[str]
    provider: str
    model: Optional[str] = None
    error: Optional[str] = None
