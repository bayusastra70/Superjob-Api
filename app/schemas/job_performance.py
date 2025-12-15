from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class JobPerformanceItem(BaseModel):
    job_id: str
    job_title: str
    views_count: int = 0
    applicants_count: int = 0
    apply_rate: float = Field(0, ge=0)
    status: str
    updated_at: datetime


class JobPerformanceResponse(BaseModel):
    items: List[JobPerformanceItem]
    page: int
    limit: int
    total: int
    sort_by: str
    order: str
    status_filter: Optional[str] = None
    message: Optional[str] = None
    meta: Optional[dict] = None
