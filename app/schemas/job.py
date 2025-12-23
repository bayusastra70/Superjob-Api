from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
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


class JobCreate(JobBase):
    """Schema untuk membuat job baru"""

    job_code: Optional[str] = Field(None, description="Kode job unik")


class JobResponse(JobBase):
    """Schema untuk response job"""

    id: int
    job_code: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Schema untuk list job response"""

    jobs: List[JobResponse]
    total: int


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
