from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Activity(BaseModel):
    id: int
    employer_id: str
    type: str
    title: str
    subtitle: Optional[str] = None
    meta_data: Dict[str, Any] = Field(default_factory=dict)
    job_id: Optional[str] = None
    applicant_id: Optional[int] = None
    message_id: Optional[str] = None
    timestamp: datetime
    is_read: bool
    redirect_url: Optional[str] = None
    user_name: Optional[str] = None  # Nama user pemilik aktivitas


class ActivityListResponse(BaseModel):
    items: List[Activity]
    page: int
    limit: int
    total: int
