from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class OjtTask(Base):
    __tablename__ = "ojt_tasks"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("ojt_programs.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)
    max_score = Column(Integer, default=100)
    order_number = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    program = relationship("OjtProgram", backref="tasks")
    submissions = relationship("OjtTaskSubmission", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_ojt_tasks_program_id", "program_id"),
    )
