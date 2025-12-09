from pydantic import BaseModel
from typing import Optional


class CandidateRejectionRequest(BaseModel):
    """Schema untuk request submit candidate rejection reason"""
    candidate_id: int
    stage: str
    rejection_reason_id: Optional[int] = None
    custom_reason: Optional[str] = None


class CandidateRejectionResponse(BaseModel):
    """Schema untuk response submit candidate rejection"""
    message: str
    candidate_id: int
    stage: str

