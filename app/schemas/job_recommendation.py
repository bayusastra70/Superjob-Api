# File: app/schemas/job_recommendation.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime


class JobRecommendationItem(BaseModel):
    """Item job untuk recommendation response"""
    id: int
    title: str
    company_name: Optional[str] = None
    company_logo: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    working_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    salary_currency: Optional[str] = "IDR"
    salary_interval: Optional[str] = "monthly"
    match_score: float = Field(..., ge=0.0, le=100.0)
    match_reasons: List[str] = Field(default_factory=list)
    is_bookmarked: bool = Field(default=False)
    created_at: datetime
    
    class Config:
        from_attributes = True


class JobRecommendationResponse(BaseModel):
    """Response untuk job recommendations"""
    jobs: List[JobRecommendationItem]
    total: int
    user_id: int
    match_criteria: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True