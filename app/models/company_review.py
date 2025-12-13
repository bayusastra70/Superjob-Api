from sqlalchemy import Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime
from typing import TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User
class CompanyReview(Base):
    __tablename__ = "company_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()), server_default=func.gen_random_uuid())
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    rating: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(255))
    pros: Mapped[str] = mapped_column(Text())
    cons: Mapped[str] = mapped_column(Text())
    position: Mapped[str] = mapped_column(String(255))
    employment_status: Mapped[str] = mapped_column(
        String(255)
    )
    employment_duration: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, server_default=func.now())

    company: Mapped["Company"] = relationship("Company", back_populates="reviews")
    user: Mapped["User"] = relationship("User", back_populates="reviews")