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
    """
    Schema untuk menambah team member baru.

    Design Reference: "Add New Member" dialog
    Fields:
    - Name (full_name)
    - Phone
    - Email
    - Role (dropdown)
    - Password

    Bisa dengan user_id yang sudah ada ATAU membuat user baru dengan data lengkap.
    Jika user_id tidak diberikan, maka name, email, dan password wajib diisi.
    """

    # Jika user sudah ada
    user_id: Optional[int] = Field(
        None, description="ID user yang sudah ada (optional jika membuat user baru)"
    )

    # Data untuk membuat user baru - sesuai design
    name: Optional[str] = Field(
        None,
        max_length=255,
        description="Nama lengkap (wajib jika user baru)",
        json_schema_extra={"example": "Budi Santoso"},
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Nomor telepon",
        json_schema_extra={"example": "082345678901"},
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Email (wajib jika user baru)",
        json_schema_extra={"example": "budi@mail.com"},
    )
    password: Optional[str] = Field(
        None, min_length=6, description="Password (wajib jika user baru)"
    )

    # Role untuk team member
    role: TeamMemberRole = Field(
        default=TeamMemberRole.TRAINER, description="Role anggota tim"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Budi Santoso",
                "phone": "082345678901",
                "email": "budi@mail.com",
                "role": "recruiter",
                "password": "password123",
            }
        }


class TeamMemberUpdate(BaseModel):
    """
    Schema untuk update team member.

    Design Reference: "Update Member" dialog
    Fields:
    - Name (nama lengkap)
    - Phone (nomor telepon)
    - Email
    - Role (dropdown)
    - Member active? (toggle)
    - Password (optional)

    Semua field optional - hanya update field yang dikirim.
    """

    # User data fields - sesuai design
    name: Optional[str] = Field(
        None,
        max_length=255,
        description="Nama lengkap",
        json_schema_extra={"example": "Budi Santoso"},
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Nomor telepon",
        json_schema_extra={"example": "082345678901"},
    )
    email: Optional[EmailStr] = Field(
        None, description="Email", json_schema_extra={"example": "budi@mail.com"}
    )

    # Team member fields
    role: Optional[TeamMemberRole] = Field(None, description="Role anggota tim")
    is_active: Optional[bool] = Field(None, description="Member active?")

    # Password - optional untuk update
    password: Optional[str] = Field(
        None, min_length=6, description="Password baru (optional)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Budi Santoso",
                "phone": "082345678901",
                "email": "budi@mail.com",
                "role": "recruiter",
                "is_active": True,
                "password": None,
            }
        }


class TeamMemberResponse(BaseModel):
    """Response schema untuk team member dengan data user yang di-populate."""

    id: int
    employer_id: int
    user_id: int
    role: str
    is_active: bool

    # Diambil dari relasi User - sesuai design
    name: Optional[str] = None  # full_name dari user
    phone: Optional[str] = None  # phone dari user
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
            "name": None,
            "phone": None,
            "email": "",
        }

        # Populate data dari relasi User jika tersedia
        if hasattr(obj, "user") and obj.user:
            data["name"] = getattr(obj.user, "full_name", None)
            data["phone"] = getattr(obj.user, "phone", None)
            data["email"] = obj.user.email

        return cls(**data)


class TeamMemberListResponse(BaseModel):
    """Response untuk list team members"""

    items: List[TeamMemberResponse]
    total: int
