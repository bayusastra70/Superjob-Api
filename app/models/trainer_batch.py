from sqlalchemy import Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base import Base


class TrainerBatch(Base):
    __tablename__ = "trainer_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"),
        nullable=False
    )

    batch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    batch_code: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    trainer = relationship("Trainer", back_populates="batches")