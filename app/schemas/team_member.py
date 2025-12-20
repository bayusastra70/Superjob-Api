from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class TeamMemberRole(str, Enum):
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"
    TRAINER = "trainer"


class TeamMemberCreate(BaseModel):
    """Schema untuk menambah team member baru.

    Bisa dengan user_id yang sudah ada ATAU membuat user baru dengan data lengkap.
    Jika user_id tidak diberikan, maka username, email, dan password wajib diisi.
    """

    # Jika user sudah ada
    user_id: Optional[int] = Field(
        None, description="ID user yang sudah ada (optional jika membuat user baru)"
    )

    # Data untuk membuat user baru
    username: Optional[str] = Field(
        None, max_length=100, description="Username (wajib jika user baru)"
    )
    full_name: Optional[str] = Field(None, max_length=255, description="Nama lengkap")
    email: Optional[EmailStr] = Field(None, description="Email (wajib jika user baru)")
    password: Optional[str] = Field(
        None, min_length=6, description="Password (wajib jika user baru)"
    )

    # Role untuk team member
    role: TeamMemberRole = TeamMemberRole.TRAINER


class TeamMemberUpdate(BaseModel):
    """Schema untuk update team member.

    Bisa update role, status aktif, dan juga data user (username, full_name, email, password).
    """

    # Team member fields
    role: Optional[TeamMemberRole] = None
    is_active: Optional[bool] = None

    # User fields (akan update user yang terkait)
    username: Optional[str] = Field(None, max_length=100, description="Username")
    full_name: Optional[str] = Field(None, max_length=255, description="Nama lengkap")
    email: Optional[EmailStr] = Field(None, description="Email")
    password: Optional[str] = Field(
        None, min_length=6, description="Password baru (jika ingin ganti)"
    )


class TeamMemberResponse(BaseModel):
    """Response schema untuk team member dengan data user yang di-populate."""

    id: int
    employer_id: int
    user_id: int
    role: str
    is_active: bool

    # Diambil dari relasi User
    username: str = ""
    full_name: Optional[str] = None
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
            "username": "",
            "full_name": None,
            "email": "",
        }

        # Populate data dari relasi User jika tersedia
        if hasattr(obj, "user") and obj.user:
            data["username"] = obj.user.username
            data["full_name"] = getattr(obj.user, "full_name", None)
            data["email"] = obj.user.email

        return cls(**data)


class TeamMemberListResponse(BaseModel):
    """Response untuk list team members"""

    items: List[TeamMemberResponse]
    total: int
