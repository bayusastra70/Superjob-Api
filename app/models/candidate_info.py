from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, TEXT, TIMESTAMP, ForeignKey, JSON, ARRAY, String
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
