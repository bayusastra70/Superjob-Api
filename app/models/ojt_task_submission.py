from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, UniqueConstraint, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class SubmissionStatus(str, enum.Enum):
    submitted = "submitted"
    graded = "graded"
    late = "late"

class OjtTaskSubmission(Base):
    __tablename__ = "ojt_task_submissions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("ojt_tasks.id", ondelete="CASCADE"), nullable=False)
    talent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)
    status = Column(String(20), server_default=SubmissionStatus.submitted.value)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    graded_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    task = relationship("OjtTask", back_populates="submissions")
    talent = relationship("User", foreign_keys=[talent_id])

    __table_args__ = (
        Index("ix_ojt_task_submissions_task_id", "task_id"),
        Index("ix_ojt_task_submissions_talent_id", "talent_id"),
        UniqueConstraint("task_id", "talent_id", name="uq_task_talent_submission"),
    )
