from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class TeamMemberRole(str, Enum):
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"
    VIEWER = "viewer"


class TeamMemberCreate(BaseModel):
    """Schema untuk menambah team member baru.

    user_id wajib diisi karena name dan email diambil dari tabel users.
    """

    user_id: int = Field(
        ..., description="ID user yang akan ditambahkan sebagai team member"
    )
    role: TeamMemberRole = TeamMemberRole.VIEWER


class TeamMemberUpdate(BaseModel):
    """Schema untuk update team member"""

    role: Optional[TeamMemberRole] = None
    is_active: Optional[bool] = None


class TeamMemberResponse(BaseModel):
    """Response schema untuk team member dengan data user yang di-populate."""

    id: int
    employer_id: int
    user_id: int
    role: str
    is_active: bool

    # Diambil dari relasi User
    name: str = ""
    email: str = ""

    class Config:
        from_attributes = True

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Custom validator untuk memetakan data user ke response."""
        # Buat instance dasar terlebih dahulu dengan nilai default
        data = {
            "id": obj.id,
            "employer_id": obj.employer_id,
            "user_id": obj.user_id,
            "role": obj.role.value if hasattr(obj.role, "value") else obj.role,
            "is_active": obj.is_active,
            "name": "",
            "email": "",
        }

        # Populate name dan email dari relasi User jika tersedia
        if hasattr(obj, "user") and obj.user:
            data["name"] = obj.user.username  # User model hanya punya username
            data["email"] = obj.user.email

        return cls(**data)


class TeamMemberListResponse(BaseModel):
    """Response untuk list team members"""

    items: List[TeamMemberResponse]
    total: int
