from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class ApplicantOut(BaseModel):
    id: str
    employer_id: int
    job_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None


class ApplicantList(BaseModel):
    items: List[ApplicantOut]
    total: int
