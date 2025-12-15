from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class QuickActionsMetrics(BaseModel):
    activeJobPosts: int = 0
    totalApplicants: int = 0
    newApplicants: int = 0
    newMessages: int = 0
    newJobPosts: int = 0


class QuickActionsBadges(BaseModel):
    newApplicants: bool = False
    newMessages: bool = False
    newJobPosts: bool = False


class QuickActionsResponse(BaseModel):
    employer_id: int
    metrics: QuickActionsMetrics
    badges: QuickActionsBadges
    lookback_start_applicants: Optional[datetime] = None
    lookback_start_job_posts: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class MarkSeenRequest(BaseModel):
    items: list[str] = Field(..., min_length=1)
