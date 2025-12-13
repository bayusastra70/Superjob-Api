from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class RejectionReason(Base):
    """
    Model SQLAlchemy untuk tabel rejection_reasons
    """
    __tablename__ = "rejection_reasons"
    
    id = Column(Integer, primary_key=True, index=True)
    reason_code = Column(String(50), unique=True, nullable=False, index=True)
    reason_text = Column(Text, nullable=False)
    is_custom = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relasi balik ke candidate_application
    applications = relationship(
        "CandidateApplication",
        back_populates="rejection_reason"
    )

