import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, Index, String, Integer
from sqlalchemy.sql import func

from app.db.base import Base


class ReminderStatus(str, enum.Enum):
    pending = "pending"
    done = "done"
    ignored = "ignored"


class ReminderTaskType(str, enum.Enum):
    message = "message"
    candidate = "candidate"
    job_update = "job_update"
    interview = "interview"
    other = "other"


class ReminderTask(Base):
    __tablename__ = "reminder_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employer_id = Column(Integer, nullable=False, index=True)
    job_id = Column(
        Integer, nullable=True
    )  # FK to jobs.id (Integer after consolidation)
    candidate_id = Column(Integer, nullable=True)
    task_title = Column(String(255), nullable=False)
    task_type = Column(
        Enum(ReminderTaskType, name="reminder_task_type"), nullable=False
    )
    redirect_url = Column(String(1024), nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        Enum(ReminderStatus, name="reminder_task_status"),
        nullable=False,
        server_default=ReminderStatus.pending.value,
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_reminder_tasks_employer_status", "employer_id", "status"),
        Index("ix_reminder_tasks_due_at", "due_at"),
    )
