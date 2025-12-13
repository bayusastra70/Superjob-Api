from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

class CandidateScoreBase(BaseModel):
    application_id: int
    fit_score: float = Field(..., ge=0, le=100)
    skill_score: Optional[float] = None
    experience_score: Optional[float] = None
    education_score: Optional[float] = None
    reasons: Optional[Dict[str, Any]] = None

class CandidateScoreCreate(CandidateScoreBase):
    pass

class CandidateScoreUpdate(BaseModel):
    fit_score: Optional[float] = Field(None, ge=0, le=100)
    skill_score: Optional[float] = None
    experience_score: Optional[float] = None
    education_score: Optional[float] = None
    reasons: Optional[Dict[str, Any]] = None

class CandidateScoreResponse(CandidateScoreBase):
    id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True

class CandidateRankingResponse(BaseModel):
    candidate_name: str
    application_id: int
    fit_score: float
    skill_score: Optional[float] = None
    experience_score: Optional[float] = None
    education_score: Optional[float] = None
    reasons: Optional[Dict[str, Any]] = None
    email: Optional[str] = None
    phone: Optional[str] = None