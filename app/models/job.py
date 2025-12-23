import enum
from typing import Optional, Sequence

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    Numeric,
    String,
    Text,
    Index,
    Integer,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

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


class Job(Base):
    """
    Unified Job model - consolidates old 'jobs' and 'job_postings' tables
    Uses Integer ID for performance and compatibility
    """

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # === Step 1: Informasi Dasar Pekerjaan ===
    industry = Column(String(100), nullable=True)
    major = Column(String(100), nullable=True)
    working_type = Column(
        Enum(WorkingType, name="working_type"),
        nullable=True,
        server_default=WorkingType.onsite.value,
    )
    gender_requirement = Column(
        Enum(GenderRequirement, name="gender_requirement"),
        nullable=True,
        server_default=GenderRequirement.any.value,
    )
    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)

    # Salary fields (Numeric for precision)
    salary_min = Column(Numeric(12, 2), nullable=True)
    salary_max = Column(Numeric(12, 2), nullable=True)
    salary_currency = Column(String(8), nullable=True, server_default="IDR")
    salary_interval = Column(
        Enum(SalaryInterval, name="salary_interval"),
        nullable=True,
        server_default=SalaryInterval.monthly.value,
    )

    skills = Column(JSON, nullable=True)  # List of strings
    location = Column(String(255), nullable=True)
    employment_type = Column(String(50), nullable=True)
    experience_level = Column(String(50), nullable=True)
    education = Column(String(100), nullable=True)

    # === Step 2: Persyaratan ===
    responsibilities = Column(Text, nullable=True)
    qualifications = Column(Text, nullable=True)
    benefits = Column(Text, nullable=True)

    # === Step 3: AI Interview Settings ===
    ai_interview_enabled = Column(Boolean, nullable=False, server_default="false")
    ai_interview_questions_count = Column(Integer, nullable=True)
    ai_interview_duration_seconds = Column(Integer, nullable=True)
    ai_interview_deadline_days = Column(Integer, nullable=True)
    ai_interview_questions = Column(Text, nullable=True)

    # Other fields
    contact_url = Column(String(512), nullable=True)
    # Using String instead of Enum for compatibility with existing VARCHAR column in DB
    status = Column(
        String(20),
        nullable=False,
        server_default=JobStatus.draft.value,
    )

    # Legacy fields (for backward compatibility)
    job_code = Column(String(50), nullable=True)
    department = Column(String(100), nullable=True)
    requirements = Column(Text, nullable=True)  # Alias to qualifications
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Company relation (BigInteger after migration 0009)
    company_id = Column(BigInteger, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Indexes
    __table_args__ = (
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_employer_id", "employer_id"),
        Index("ix_jobs_company_id", "company_id"),
        Index("ix_jobs_created_at", "created_at"),
    )

    # Relationships - only for columns with actual FK constraints
    # Note: company relationship removed since no FK constraint exists on company_id
    employer = relationship("User", foreign_keys=[employer_id])
    creator = relationship("User", foreign_keys=[created_by])

    @property
    def skills_list(self) -> Sequence[str]:
        """Return skills as list even if null."""
        return self.skills or []

    @property
    def salary_range_display(self) -> Optional[str]:
        """Return formatted salary range for display."""
        if self.salary_min and self.salary_max:
            currency = self.salary_currency or "IDR"
            return f"{currency} {self.salary_min:,.0f} - {self.salary_max:,.0f}"
        return None
