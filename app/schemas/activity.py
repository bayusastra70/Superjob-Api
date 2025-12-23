from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field


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

    @computed_field
    @property
    def summary(self) -> str:
        """Generate summary based on activity type"""
        type_to_summary = {
            "new_applicant": "New Applicant",
            "status_update": "Application status changed",
            "job_published": "Job published",
            "new_message": "New message",
            "job_performance_alert": "Performance alert",
            "team_member_updated": "Team member updated",
            "system_event": "System event",
        }
        return type_to_summary.get(self.type, self.title)


class ActivityDashboardStats(BaseModel):
    """Stats untuk dashboard Last 24 Hour"""

    job_published: int = 0
    new_applicant: int = 0
    application_status_changed: int = 0
    team_member_updated: int = 0


class ActivityDashboardResponse(BaseModel):
    """Response untuk Activity Log Dashboard"""

    stats: ActivityDashboardStats
    recent_activities: List[Activity]
    total: int


class ActivityAssociatedData(BaseModel):
    """Associated Data untuk detail activity"""

    activity_id: str
    source: Optional[str] = None
    ip_address: Optional[str] = None
    browser_os: Optional[str] = None
    job_id: Optional[str] = None
    applicant_id: Optional[int] = None
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class ActivityUserInvolved(BaseModel):
    """User yang terlibat dalam activity"""

    user_id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    avatar_url: Optional[str] = None


class ActivityDetailResponse(BaseModel):
    """Response untuk detail activity (Gambar 3)"""

    id: int
    employer_id: str
    type: str
    title: str
    status: str = "Successful"  # Default status
    timestamp: datetime
    description: Optional[str] = None
    associated_data: ActivityAssociatedData
    user_involved: Optional[ActivityUserInvolved] = None
    redirect_url: Optional[str] = None
    is_read: bool


class TimelineListResponse(BaseModel):
    """Response untuk Timeline tab - full list dengan pagination"""

    items: List[Activity]
    page: int
    limit: int
    total: int
    total_pages: int
