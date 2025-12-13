import enum
import uuid
from typing import Optional, Sequence

from sqlalchemy import Column, DateTime, Enum, JSON, Numeric, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class JobStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    salary_min = Column(Numeric(12, 2), nullable=True)
    salary_max = Column(Numeric(12, 2), nullable=True)
    salary_currency = Column(String(8), nullable=True)
    skills = Column(JSON, nullable=True)  # list of strings
    location = Column(String(255), nullable=True)
    employment_type = Column(String(50), nullable=True)
    experience_level = Column(String(50), nullable=True)
    education = Column(String(100), nullable=True)
    benefits = Column(Text, nullable=True)
    contact_url = Column(String(512), nullable=True)
    status = Column(
        Enum(JobStatus, name="job_status"),
        nullable=False,
        server_default=JobStatus.draft.value,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
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
