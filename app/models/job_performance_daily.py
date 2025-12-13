import uuid
from datetime import date

from sqlalchemy import Column, Date, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class JobPerformanceDaily(Base):
    __tablename__ = "job_performance_daily"

    job_id = Column(UUID(as_uuid=True), primary_key=True)
    as_of_date = Column(Date, primary_key=True)
    employer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    job_title = Column(String(255), nullable=True)
    views_count = Column(Integer, nullable=False, default=0)
    applicants_count = Column(Integer, nullable=False, default=0)
    apply_rate = Column(Numeric(6, 2), nullable=False, default=0)
    status = Column(String(20), nullable=False)
