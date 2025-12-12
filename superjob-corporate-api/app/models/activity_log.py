import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text

from app.db.base import Base


class ActivityType(str, enum.Enum):
    NEW_APPLICANT = "new_applicant"
    STATUS_UPDATE = "status_update"
    NEW_MESSAGE = "new_message"
    JOB_PERFORMANCE_ALERT = "job_performance_alert"
    SYSTEM_EVENT = "system_event"


class ActivityLog(Base):
    """SQLAlchemy model for activity_logs (notification feed)."""

    __tablename__ = "activity_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    employer_id = Column(String(64), nullable=False, index=True)
    type = Column(Enum(ActivityType, name="activity_type", create_constraint=False), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    subtitle = Column(Text, nullable=True)
    meta_data = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    job_id = Column(String(64), nullable=True, index=True)
    applicant_id = Column(BigInteger, nullable=True, index=True)
    message_id = Column(String(64), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    is_read = Column(Boolean, nullable=False, server_default=text("false"), index=True)

    def redirect_url(self) -> str | None:
        """Helper: extract redirect/CTA from meta_data."""
        if isinstance(self.meta_data, dict):
            return self.meta_data.get("cta") or self.meta_data.get("redirect_url")
        return None
