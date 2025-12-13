import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class ApplicantOut(BaseModel):
    id: uuid.UUID
    employer_id: uuid.UUID
    job_id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None


class ApplicantList(BaseModel):
    items: List[ApplicantOut]
    total: int
