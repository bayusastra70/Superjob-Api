import enum
import uuid
from typing import Optional, Sequence

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    JSON,
    Numeric,
    String,
    Text,
    Index,
    Integer,
)
from sqlalchemy.sql import func

from app.db.base import Base


class JobStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class WorkingType(str, enum.Enum):
    onsite = "onsite"
    remote = "remote"
    hybrid = "hybrid"


class GenderRequirement(str, enum.Enum):
    any = "any"
    male = "male"
    female = "female"


class SalaryInterval(str, enum.Enum):
    hourly = "hourly"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employer_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # === Step 1: Informasi Dasar Pekerjaan ===
    industry = Column(String(100), nullable=True)  # Industri
    major = Column(String(100), nullable=True)  # Jurusan
    working_type = Column(
        Enum(WorkingType, name="working_type"),
        nullable=True,
        server_default=WorkingType.onsite.value,
    )  # On-site / Remote / Hybrid
    gender_requirement = Column(
        Enum(GenderRequirement, name="gender_requirement"),
        nullable=True,
        server_default=GenderRequirement.any.value,
    )  # Jenis Kelamin
    min_age = Column(Integer, nullable=True)  # Usia minimal
    max_age = Column(Integer, nullable=True)  # Usia maksimal

    # Salary fields
    salary_min = Column(Numeric(12, 2), nullable=True)
    salary_max = Column(Numeric(12, 2), nullable=True)
    salary_currency = Column(String(8), nullable=True, server_default="IDR")
    salary_interval = Column(
        Enum(SalaryInterval, name="salary_interval"),
        nullable=True,
        server_default=SalaryInterval.monthly.value,
    )  # Per bulan / tahun / dll

    skills = Column(JSON, nullable=True)  # list of strings
    location = Column(String(255), nullable=True)
    employment_type = Column(
        String(50), nullable=True
    )  # Full-time, Part-time, Contract, dll
    experience_level = Column(String(50), nullable=True)  # Pengalaman
    education = Column(String(100), nullable=True)  # Pendidikan Terakhir

    # === Step 2: Persyaratan ===
    responsibilities = Column(Text, nullable=True)  # Tanggung Jawab
    qualifications = Column(Text, nullable=True)  # Kualifikasi
    benefits = Column(Text, nullable=True)  # Keuntungan

    # === Step 3: AI Interview Settings ===
    ai_interview_enabled = Column(Boolean, nullable=False, server_default="false")
    ai_interview_questions_count = Column(Integer, nullable=True)  # Jumlah Pertanyaan
    ai_interview_duration_seconds = Column(
        Integer, nullable=True
    )  # Durasi Menjawab (detik)
    ai_interview_deadline_days = Column(
        Integer, nullable=True
    )  # Batas Waktu Interview (hari)
    ai_interview_questions = Column(
        Text, nullable=True
    )  # Daftar Pertanyaan (rich text)

    # Other fields
    contact_url = Column(String(512), nullable=True)
    status = Column(
        Enum(JobStatus, name="job_status"),
        nullable=False,
        server_default=JobStatus.draft.value,
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (Index("ix_job_postings_status", "status"),)

    @property
    def skills_list(self) -> Sequence[str]:
        """Return skills as list even if null."""
        return self.skills or []
