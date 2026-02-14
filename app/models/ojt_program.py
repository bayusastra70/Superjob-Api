import enum

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Index,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class OjtProgramStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    ongoing = "ongoing"
    completed = "completed"
    archived = "archived"


class OjtProgram(Base):
    """
    Model untuk tabel ojt_programs.
    Menyimpan informasi program OJT yang tersedia.
    Mirip seperti Job, tapi untuk pelatihan.
    """

    __tablename__ = "ojt_programs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    role = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    duration_days = Column(Integer, nullable=True)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    max_participants = Column(Integer, nullable=True)
    requirements = Column(Text, nullable=True)
    skills = Column(JSON, nullable=True)
    status = Column(
        String(20),
        nullable=False,
        server_default=OjtProgramStatus.draft.value,
    )
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
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
        Index("ix_ojt_programs_status", "status"),
        Index("ix_ojt_programs_role", "role"),
        Index("ix_ojt_programs_location", "location"),
    )

    # Relationships
    trainer = relationship("User", foreign_keys=[trainer_id])
