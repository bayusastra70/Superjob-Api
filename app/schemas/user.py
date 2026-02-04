# from pydantic import BaseModel
# from typing import Optional

# from pydantic import BaseModel, EmailStr, validator
# from datetime import datetime

# class UserLogin(BaseModel):
#     email: str
#     password: str

# class Token(BaseModel):
#     access_token: str
#     token_type: str

# class TokenData(BaseModel):
#     email: Optional[str] = None
#     user_id: Optional[int] = None

# class UserCreate(BaseModel):
#     email: str
#     username: str
#     password: str
#     full_name: Optional[str] = None
#     phone: Optional[str] = None
#     role: Optional[str] = "candidate"

#     @validator('role')
#     def validate_role(cls, v):
#         if v is None or v == "":
#             return "candidate"

#         if v not in ['admin', 'employer', 'candidate']:
#             raise ValueError('Role must be one of: admin, employer, candidate')
#         return v

#     @validator('email')
#     def validate_email(cls, v):
#         if '@' not in v:
#             raise ValueError('Invalid email format')
#         return v.lower()

# class UserResponse(BaseModel):
#     id: int
#     email: str
#     username: str
#     full_name: Optional[str] = None
#     is_active: bool
#     is_superuser: Optional[bool] = False

#     role: Optional[str] = ""

#     class Config:
#         from_attributes = True


from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, ClassVar, Set
from datetime import datetime
from enum import Enum
import re


class UserRole(str, Enum):
    CANDIDATE = "candidate"
    EMPLOYER = "employer"
    ADMIN = "admin"


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    role: UserRole = UserRole.CANDIDATE
    role_id: Optional[int] = Field(None, description="Optional Role ID for RBAC")

    @validator("phone")
    def validate_phone(cls, v):
        if v is None:
            return v

        # Hapus spasi dan karakter khusus
        phone_digits = re.sub(r"\D", "", v)

        # Validasi panjang
        if len(phone_digits) < 10 or len(phone_digits) > 15:
            raise ValueError("Nomor telepon harus 10-15 digit")

        # Validasi format Indonesia
        if not phone_digits.startswith(("08", "62", "+62")):
            raise ValueError(
                "Format nomor telepon tidak valid. Gunakan format Indonesia (08xx atau 62xx)"
            )

        # Konversi ke format standar 62
        if phone_digits.startswith("0"):
            phone_digits = "62" + phone_digits[1:]
        elif phone_digits.startswith("+62"):
            phone_digits = phone_digits[1:]

        return phone_digits

    @validator("password")
    def validate_password(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password harus mengandung minimal 1 huruf besar")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password harus mengandung minimal 1 huruf kecil")
        if not re.search(r"\d", v):
            raise ValueError("Password harus mengandung minimal 1 angka")
        return v

    @validator("role")
    def validate_role(cls, v):
        if isinstance(v, str):
            if v not in ["admin", "employer", "candidate"]:
                raise ValueError("Role must be one of: admin, employer, candidate")
        return v


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = ""
    cv_url: Optional[str] = None
    role_id: Optional[int] = Field(None, alias="default_role_id")
    company_id: Optional[int] = None
    is_active: bool
    is_superuser: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class JobPreferencesResponse(BaseModel):
    """Job preferences response schema"""

    preferred_locations: Optional[List[str]] = None
    preferred_work_modes: Optional[List[str]] = None
    preferred_job_types: Optional[List[str]] = None
    expected_salary_min: Optional[float] = None
    expected_salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    preferred_industries: Optional[List[str]] = None
    preferred_divisions: Optional[List[str]] = None
    auto_apply_enabled: Optional[bool] = False

    class Config:
        from_attributes = True


class JobPreferencesUpdate(BaseModel):
    """Job preferences update schema"""

    model_config = {"ignored_types": (set,)}

    VALID_WORK_MODES: ClassVar[Set[str]] = {"onsite", "remote", "hybrid"}
    VALID_JOB_TYPES: ClassVar[Set[str]] = {
        "full-time",
        "part-time",
        "contract",
        "freelance",
        "internship",
    }

    preferred_locations: Optional[List[str]] = Field(None, max_length=5)
    preferred_work_modes: Optional[List[str]] = Field(None, max_length=3)
    preferred_job_types: Optional[List[str]] = Field(None, max_length=3)
    expected_salary_min: Optional[float] = Field(None, ge=0)
    expected_salary_max: Optional[float] = Field(None, ge=0)
    salary_currency: Optional[str] = Field(None, max_length=8)
    preferred_industries: Optional[List[str]] = Field(None, max_length=5)
    preferred_divisions: Optional[List[str]] = Field(None, max_length=5)
    auto_apply_enabled: Optional[bool] = None

    @validator("preferred_work_modes", each_item=True)
    def validate_work_modes(cls, v):
        if v and v.lower() not in cls.VALID_WORK_MODES:
            raise ValueError(
                f"'{v}' is not valid. Allowed values: {', '.join(sorted(cls.VALID_WORK_MODES))}"
            )
        return v.lower() if v else None

    @validator("preferred_job_types", each_item=True)
    def validate_job_types(cls, v):
        if v and v.lower().strip() not in cls.VALID_JOB_TYPES:
            raise ValueError(
                f"'{v}' is not valid. Allowed values: {', '.join(sorted(cls.VALID_JOB_TYPES))}"
            )
        return v.title() if v else None

    @validator("expected_salary_min", "expected_salary_max")
    def validate_salary_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError("salary cannot be negative")
        return v

    @validator(
        "preferred_locations",
        "preferred_industries",
        "preferred_divisions",
        each_item=True,
    )
    def validate_not_empty_string(cls, v):
        if v is not None and isinstance(v, str) and v.strip() == "":
            raise ValueError("cannot be empty")
        return v.strip() if isinstance(v, str) else v


class UserProfileResponse(BaseModel):
    """Response schema for user profile with CV extracted data"""

    id: int
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    role: str
    cv_url: Optional[str] = None

    # CV extracted fields (flattened)
    summary: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = []
    languages: List[str] = []
    experience: List[dict] = []
    education: List[dict] = []
    certifications: List[dict] = []

    # Job preferences
    job_preferences: Optional[JobPreferencesResponse] = None

    class Config:
        from_attributes = True


# Schema untuk list users dengan pagination
class PaginationInfo(BaseModel):
    page: int
    limit: int
    total_count: int
    total_pages: int
    has_next: bool
    has_prev: bool


class FilterInfo(BaseModel):
    search: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


class UserListResponse(BaseModel):
    success: bool = True
    data: List[UserResponse]
    pagination: PaginationInfo
    filters: FilterInfo


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    cv_url: Optional[str] = None

    # CV data (from scan endpoint)
    summary: Optional[str] = None
    skills: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    experience: Optional[List[dict]] = None
    education: Optional[List[dict]] = None
    certifications: Optional[List[dict]] = None

    # Job preferences
    job_preferences: Optional[JobPreferencesUpdate] = None


class UserPasswordUpdate(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

    @validator("new_password")
    def validate_password_strength(cls, v):
        """Validate password has minimum requirements"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


# Schema untuk statistics
class UserStatsResponse(BaseModel):
    role: str
    total: int
    active: int
    inactive: int


class UserUpdateSimple(BaseModel):
    """Schema untuk update semua data user tanpa auth"""

    email: Optional[EmailStr] = Field(None, description="Email user")
    username: Optional[str] = Field(
        None, min_length=3, max_length=100, description="Username"
    )
    full_name: Optional[str] = Field(
        None, min_length=2, max_length=255, description="Nama lengkap"
    )
    phone: Optional[str] = Field(
        None, min_length=10, max_length=20, description="Nomor telepon"
    )
    role: Optional[str] = Field(
        None, description="Role user: admin, employer, candidate"
    )
    is_active: Optional[bool] = Field(None, description="Status aktif")

    @validator("phone")
    def validate_phone(cls, v):
        if v is None:
            return v

        # Hapus spasi dan karakter khusus
        phone_digits = re.sub(r"\D", "", v)

        # Validasi panjang
        if len(phone_digits) < 10 or len(phone_digits) > 20:
            raise ValueError("Nomor telepon harus 10-20 digit")

        # Validasi format Indonesia
        if not phone_digits.startswith(("08", "62", "+62")):
            raise ValueError(
                "Format nomor telepon tidak valid. Gunakan format Indonesia (08xx atau 62xx)"
            )

        # Konversi ke format standar 62
        if phone_digits.startswith("0"):
            phone_digits = "62" + phone_digits[1:]
        elif phone_digits.startswith("+62"):
            phone_digits = phone_digits[1:]

        return phone_digits

    @validator("role")
    def validate_role(cls, v):
        if v is None:
            return v

        if v not in ["admin", "employer", "candidate"]:
            raise ValueError("Role must be one of: admin, employer, candidate")
        return v


class UserUpdateResponseSimple(BaseModel):
    """Response sederhana untuk update user"""

    success: bool = True
    message: str
    user: UserResponse
