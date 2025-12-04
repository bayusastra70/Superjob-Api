from sqlalchemy import String, DateTime, Text, ForeignKey, UUID, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime
from typing import List, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from app.models.company_review import CompanyReview
    from app.models.user import User

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()), server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    industry: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    website_url: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(Text)
    logo_url: Mapped[str] = mapped_column(String(255))
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, server_default=func.now())

    created_by_user: Mapped["User"] = relationship("User", back_populates="companies")
    reviews: Mapped[List["CompanyReview"]] = relationship("CompanyReview", back_populates="company")