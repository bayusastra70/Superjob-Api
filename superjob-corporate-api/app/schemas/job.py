import uuid
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class JobQualityResponse(BaseModel):
    job_id: uuid.UUID
    score: Optional[float] = Field(None, ge=0, le=100)
    grade: Optional[str] = None
    optimal: Optional[bool] = None
    details: Optional[Dict[str, float]] = None
    message: Optional[str] = None
    suggestions: Optional[list[str]] = None

    model_config = ConfigDict(from_attributes=True)


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    skills: Optional[list[str]] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    education: Optional[str] = None
    benefits: Optional[str] = None
    contact_url: Optional[str] = None
    status: Optional[str] = None
