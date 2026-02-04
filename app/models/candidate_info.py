from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    TEXT,
    TIMESTAMP,
    ForeignKey,
    JSON,
    ARRAY,
    String,
    Numeric,
    Boolean,
)
from sqlalchemy.sql import func
from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column


class CandidateInfo(Base):
    """
    Model for storing additional candidate information.
    Includes CV extraction data from AI processing.
    """

    __tablename__ = "candidate_info"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    cv_url: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    cv_extracted_profile: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    cv_extracted_experience: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    cv_extracted_education: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    cv_extracted_skills: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )
    cv_extracted_languages: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )
    cv_extracted_certifications: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )
    cv_extracted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    cv_extraction_status: Mapped[str] = mapped_column(
        String(20), server_default="pending", nullable=False
    )
    cv_extraction_error: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)

    preferred_locations: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)), nullable=True
    )
    preferred_work_modes: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(20)), nullable=True
    )
    preferred_job_types: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(50)), nullable=True
    )
    expected_salary_min: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    expected_salary_max: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    salary_currency: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, server_default="IDR"
    )
    preferred_industries: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)), nullable=True
    )
    preferred_divisions: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)), nullable=True
    )
    auto_apply_enabled: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, server_default="false"
    )
