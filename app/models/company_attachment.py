from sqlalchemy import String, DateTime, Text, ForeignKey, BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.company import Company

class CompanyAttachment(Base):
    __tablename__ = "company_attachments"

    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
    
    # NIB
    nib_url: Mapped[str] = mapped_column(Text, nullable=True)
    nib_storage_id: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # NPWP
    npwp_url: Mapped[str] = mapped_column(Text, nullable=True)
    npwp_storage_id: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Proposal
    proposal_url: Mapped[str] = mapped_column(Text, nullable=True)
    proposal_storage_id: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Portfolio
    portfolio_url: Mapped[str] = mapped_column(Text, nullable=True)
    portfolio_storage_id: Mapped[str] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, server_default=func.now())

    company: Mapped["Company"] = relationship("Company", back_populates="attachments")
