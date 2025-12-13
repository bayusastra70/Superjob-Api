from pydantic import BaseModel
from typing import Optional

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

class OdooUser(BaseModel):
    id: int
    name: str
    email: str
    partner_id: int

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TimesheetCreate(BaseModel):
    project_id: int
    task_id: int
    name: str
    unit_amount: float
    date: str