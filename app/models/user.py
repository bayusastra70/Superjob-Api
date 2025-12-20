from sqlalchemy import Integer, String, DateTime, Boolean, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import enum

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.company_review import CompanyReview


class UserRole(str, enum.Enum):
    admin = "admin"
    employer = "employer"
    candidate = "candidate"


class User(Base):
    """User model - matches the database schema from initial migration."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=False),
        nullable=False,
        server_default="candidate",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    reviews: Mapped[List["CompanyReview"]] = relationship(
        "CompanyReview", back_populates="user"
    )
