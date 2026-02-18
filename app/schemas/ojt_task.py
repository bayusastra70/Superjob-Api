from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SubmissionStatus(str, Enum):
    SUBMITTED = "submitted"
    GRADED = "graded"
    LATE = "late"

# --- Submission Schemas ---
class OjtTaskSubmissionBase(BaseModel):
    content: Optional[str] = None
    file_url: Optional[str] = None

class OjtTaskSubmissionCreate(OjtTaskSubmissionBase):
    pass

class OjtTaskSubmissionScore(BaseModel):
    score: float
    feedback: Optional[str] = None

class OjtTaskSubmissionResponse(OjtTaskSubmissionBase):
    id: int
    task_id: int
    talent_id: int
    status: str
    score: Optional[float] = None
    feedback: Optional[str] = None
    submitted_at: datetime
    graded_at: Optional[datetime] = None
    
    talent_name: Optional[str] = None # For trainer view

    model_config = {"from_attributes": True}

# --- Task Schemas ---
class OjtTaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    max_score: Optional[int] = 100
    order_number: Optional[int] = 0

class OjtTaskCreate(OjtTaskBase):
    pass

class OjtTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    max_score: Optional[int] = None
    order_number: Optional[int] = None

class OjtTaskResponse(OjtTaskBase):
    id: int
    program_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # For talent view: status of their submission
    submission_status: Optional[str] = None # submitted/graded/late/none
    my_score: Optional[float] = None

    model_config = {"from_attributes": True}

class OjtTaskList(BaseModel):
    tasks: List[OjtTaskResponse]
    total: int
