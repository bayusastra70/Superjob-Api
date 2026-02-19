from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OjtApplicationStatus(str, Enum):
    PENDING = "pending"
    SCREENING = "screening"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REGISTERED = "registered"
    WITHDRAWN = "withdrawn"


class OjtApplicationCreate(BaseModel):
    """Schema untuk mendaftar ke program OJT (request body)"""

    program_id: int = Field(..., description="ID program OJT yang didaftar")
    cover_letter: Optional[str] = Field(
        None, description="Cover Letter (opsional)"
    )


class OjtApplicationResponse(BaseModel):
    """Data aplikasi OJT yang dikembalikan ke frontend"""

    id: int
    talent_id: int
    program_id: int
    status: str
    cover_letter: Optional[str] = None
    ai_fit_score: Optional[float] = None
    applied_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    registered_at: Optional[datetime] = None

    # New fields
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    domicile: Optional[str] = None
    cv_url: Optional[str] = None
    portfolio_url: Optional[str] = None

    # Info program (dari JOIN)
    program_title: Optional[str] = None
    program_role: Optional[str] = None
    program_location: Optional[str] = None
    program_status: Optional[str] = None

    model_config = {"from_attributes": True}


class OjtApplicationListData(BaseModel):
    """Wrapper untuk list aplikasi + total"""

    applications: List[OjtApplicationResponse] = []
    total: int = 0
