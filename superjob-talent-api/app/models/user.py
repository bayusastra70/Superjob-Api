from sqlalchemy import Integer, String, DateTime, UUID, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime
import uuid
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.company import Company

if TYPE_CHECKING:
    from app.models.company_review import CompanyReview

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False,
        server_default=func.now(),
        default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False,
        server_default=func.now(),
        default=datetime.now,
        onupdate=datetime.now
    )

    # companies: Mapped[List["Company"]] = relationship("Company", back_populates="created_by_user")
    reviews: Mapped[List["CompanyReview"]] = relationship("CompanyReview", back_populates="user")

