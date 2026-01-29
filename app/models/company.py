from sqlalchemy import String, DateTime, Text, ForeignKey, UUID, Integer, func, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime
from typing import List, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from app.models.company_review import CompanyReview
    from app.models.user import User
    from app.models.company_attachment import CompanyAttachment

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    industry: Mapped[str] = mapped_column(String(100))
    website: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(Text)
    logo_url: Mapped[str] = mapped_column(String(255))
    banner_url: Mapped[str] = mapped_column(String(255), nullable=True)
    banner_storage_id: Mapped[str] = mapped_column(String(255), nullable=True)
    founded_year: Mapped[int] = mapped_column(Integer, nullable=True)
    employee_size: Mapped[str] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str] = mapped_column(String(255))
    twitter_url: Mapped[str] = mapped_column(String(255))
    instagram_url: Mapped[str] = mapped_column(String(255))
    facebook_url: Mapped[str] = mapped_column(String(255), nullable=True)
    tiktok_url: Mapped[str] = mapped_column(String(255), nullable=True)
    youtube_url: Mapped[str] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(255), nullable=True)
    logo_storage_id: Mapped[str] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, server_default=func.now())

    reviews: Mapped[List["CompanyReview"]] = relationship("CompanyReview", back_populates="company")
    users: Mapped[List["User"]] = relationship("User", secondary="users_companies", back_populates="companies")
    attachments: Mapped["CompanyAttachment"] = relationship("CompanyAttachment", back_populates="company", uselist=False)