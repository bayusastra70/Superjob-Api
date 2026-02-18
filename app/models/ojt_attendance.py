from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    excused = "excused"

class OjtAttendance(Base):
    __tablename__ = "ojt_attendance"

    id = Column(Integer, primary_key=True, index=True)
    agenda_id = Column(Integer, ForeignKey("ojt_agendas.id", ondelete="CASCADE"), nullable=False)
    talent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, server_default=AttendanceStatus.present.value)
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    agenda = relationship("OjtAgenda", back_populates="attendances")
    talent = relationship("User", foreign_keys=[talent_id])

    __table_args__ = (
        Index("ix_ojt_attendance_agenda_id", "agenda_id"),
        Index("ix_ojt_attendance_talent_id", "talent_id"),
        UniqueConstraint("agenda_id", "talent_id", name="uq_agenda_talent_attendance"),
    )
