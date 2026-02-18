from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class OjtAgenda(Base):
    __tablename__ = "ojt_agendas"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("ojt_programs.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    session_date = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    location = Column(String(255), nullable=True)
    meeting_link = Column(Text, nullable=True)
    trainer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    order_number = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    program = relationship("OjtProgram", backref="agendas")
    trainer = relationship("User", foreign_keys=[trainer_id])
    attendances = relationship("OjtAttendance", back_populates="agenda", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_ojt_agendas_program_id", "program_id"),
    )
