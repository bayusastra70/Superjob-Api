from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class CandidateApplication(Base):
    """
    Model SQLAlchemy untuk tabel candidate_application
    """
    __tablename__ = "candidate_application"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    applied_position = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)
    applied_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    # Foreign key ke tabel rejection_reasons
    rejection_reason_id = Column(
        Integer, 
        ForeignKey("rejection_reasons.id"), 
        nullable=True
    )
    
    # Relasi SQLAlchemy
    rejection_reason = relationship(
        "RejectionReason", 
        back_populates="applications"
    )

