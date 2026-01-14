from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, TEXT, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column

class CandidateInfo(Base):
    """
    Model for storing additional candidate information.
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
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
