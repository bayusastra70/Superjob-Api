from sqlalchemy import Integer, String, Text, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from typing import Optional, List

from app.db.base import Base


class Trainer(Base):
    __tablename__ = "trainers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(String(255))
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)

    work_history: Mapped[Optional[str]] = mapped_column(Text)
    relevant_skills: Mapped[Optional[str]] = mapped_column(Text)
    certifications: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    batches: Mapped[List["TrainerBatch"]] = relationship(
        "TrainerBatch",
        back_populates="trainer",
        cascade="all, delete-orphan"
    )