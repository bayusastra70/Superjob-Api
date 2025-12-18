from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class TeamMemberRole(str, Enum):
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"
    VIEWER = "viewer"


class TeamMemberCreate(BaseModel):
    """Schema untuk menambah team member baru"""

    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    role: TeamMemberRole = TeamMemberRole.VIEWER
    user_id: Optional[int] = None  # Optional, bisa di-link ke existing user


class TeamMemberUpdate(BaseModel):
    """Schema untuk update team member"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    role: Optional[TeamMemberRole] = None
    is_active: Optional[bool] = None


class TeamMemberResponse(BaseModel):
    id: int
    employer_id: int
    user_id: int
    role: str
    is_active: bool

    # Ambil dari relasi User
    name: str
    email: str

    class Config:
        from_attributes = True

    @classmethod
    def model_validate(cls, obj, **kwargs):
        # Helper untuk memetakan user.full_name ke name
        instance = super().model_validate(obj, **kwargs)
        if hasattr(obj, "user") and obj.user:
            instance.name = obj.user.full_name or obj.user.username
            instance.email = obj.user.email
        return instance


class TeamMemberListResponse(BaseModel):
    """Response untuk list team members"""

    items: List[TeamMemberResponse]
    total: int
