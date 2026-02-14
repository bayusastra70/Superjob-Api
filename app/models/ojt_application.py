import enum

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class OjtApplicationStatus(str, enum.Enum):
    pending = "pending"
    screening = "screening"
    accepted = "accepted"
    rejected = "rejected"
    registered = "registered"
    withdrawn = "withdrawn"


class OjtApplication(Base):
    """
    Model untuk tabel ojt_applications.
    Menyimpan pendaftaran talent ke program OJT.
    Mirip seperti CandidateApplication, tapi untuk OJT.
    """

    __tablename__ = "ojt_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    talent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    program_id = Column(Integer, ForeignKey("ojt_programs.id"), nullable=False)
    status = Column(
        String(20),
        nullable=False,
        server_default=OjtApplicationStatus.pending.value,
    )
    motivation_letter = Column(Text, nullable=True)
    ai_fit_score = Column(Numeric(5, 2), nullable=True)
    applied_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    registered_at = Column(DateTime(timezone=True), nullable=True)

    # Constraints & Indexes
    __table_args__ = (
        UniqueConstraint(
            "talent_id", "program_id", name="uq_ojt_app_talent_program"
        ),
        Index("ix_ojt_applications_talent_id", "talent_id"),
        Index("ix_ojt_applications_program_id", "program_id"),
        Index("ix_ojt_applications_status", "status"),
    )

    # Relationships
    talent = relationship("User", foreign_keys=[talent_id])
    program = relationship("OjtProgram", foreign_keys=[program_id])
