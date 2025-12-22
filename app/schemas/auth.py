"""
Authentication Schemas for SuperJob API

Separate schemas for Corporate (Employer) and Talent (Candidate) authentication flows.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from enum import Enum


# =====================================================
# ENUMS
# =====================================================


class AuthProvider(str, Enum):
    """Authentication provider types"""

    email = "email"
    google = "google"


# =====================================================
# TOKEN SCHEMAS
# =====================================================


class Token(BaseModel):
    """JWT Token response"""

    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None  # seconds until expiration


class TokenData(BaseModel):
    """Token payload data"""

    email: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None


# =====================================================
# CORPORATE (EMPLOYER) AUTHENTICATION
# =====================================================


class CorporateLoginRequest(BaseModel):
    """
    Corporate Login Request - for Employers/Recruiters/Admins

    Design Reference: Image 1 - "Welcome, Partner!" login form
    """

    email: EmailStr = Field(
        ..., description="Email address", example="employer@superjob.com"
    )
    password: str = Field(..., min_length=6, max_length=72, description="Password")

    class Config:
        json_schema_extra = {
            "example": {"email": "employer@superjob.com", "password": "employer123"}
        }


class CorporateRegisterRequest(BaseModel):
    """
    Corporate Registration Request - for new Employers

    Design Reference: Image 2 - "Welcome to Superjob" registration form
    Fields:
    - Contact Name
    - Company Name
    - Email Address
    - Phone Number (+62)
    - Password
    - NIB Document (handled separately via file upload)
    """

    contact_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Contact person name (full name)",
        example="John Doe",
    )
    company_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Company/Organization name",
        example="PT Teknologi Maju",
    )
    email: EmailStr = Field(
        ..., description="Business email address", example="hr@teknologimaju.com"
    )
    phone_number: str = Field(
        ...,
        min_length=10,
        max_length=20,
        description="Phone number with country code",
        example="+6281234567890",
    )
    password: str = Field(
        ..., min_length=8, max_length=72, description="Password (min 8 characters)"
    )

    @validator("phone_number")
    def validate_phone_number(cls, v):
        """Validate Indonesian phone number format"""
        # Remove spaces and dashes
        cleaned = v.replace(" ", "").replace("-", "")

        # Check if starts with valid prefix
        if not (
            cleaned.startswith("+62")
            or cleaned.startswith("62")
            or cleaned.startswith("0")
        ):
            raise ValueError("Phone number must start with +62, 62, or 0")

        # Normalize to +62 format
        if cleaned.startswith("0"):
            cleaned = "+62" + cleaned[1:]
        elif cleaned.startswith("62"):
            cleaned = "+" + cleaned

        return cleaned

    @validator("password")
    def validate_password_strength(cls, v):
        """Validate password has minimum requirements"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        # Could add more requirements here (uppercase, number, etc.)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "contact_name": "John Doe",
                "company_name": "PT Teknologi Maju",
                "email": "hr@teknologimaju.com",
                "phone_number": "+6281234567890",
                "password": "SecurePassword123",
            }
        }


class CorporateRegisterResponse(BaseModel):
    """Response after successful corporate registration"""

    message: str = "Registration successful"
    user_id: int
    email: str
    company_name: str
    role: str = "employer"
    is_verified: bool = False  # Will be verified after NIB document review

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Registration successful. Please wait for account verification.",
                "user_id": 100,
                "email": "hr@teknologimaju.com",
                "company_name": "PT Teknologi Maju",
                "role": "employer",
                "is_verified": False,
            }
        }


# =====================================================
# TALENT (CANDIDATE) AUTHENTICATION
# =====================================================


class TalentLoginRequest(BaseModel):
    """
    Talent Login Request - for Candidates/Job Seekers

    Design Reference: Image 3 - "Welcome Back!" login form
    """

    email: EmailStr = Field(
        ..., description="Email address", example="candidate@superjob.com"
    )
    password: str = Field(..., min_length=6, max_length=72, description="Password")

    class Config:
        json_schema_extra = {
            "example": {"email": "candidate@superjob.com", "password": "candidate123"}
        }


class TalentRegisterRequest(BaseModel):
    """
    Talent Registration Request - for new Job Seekers

    Design Reference: Image 4 - "Welcome to SuperJob" registration form
    Fields:
    - Name*
    - Email*
    - Password*
    - CV Upload (handled separately via file upload)
    """

    name: str = Field(
        ..., min_length=2, max_length=100, description="Full name", example="Jane Smith"
    )
    email: EmailStr = Field(
        ..., description="Email address", example="jane.smith@gmail.com"
    )
    password: str = Field(
        ..., min_length=8, max_length=72, description="Password (min 8 characters)"
    )

    @validator("password")
    def validate_password_strength(cls, v):
        """Validate password has minimum requirements"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Jane Smith",
                "email": "jane.smith@gmail.com",
                "password": "SecurePassword123",
            }
        }


class TalentRegisterResponse(BaseModel):
    """Response after successful talent registration"""

    message: str = "Registration successful"
    user_id: int
    email: str
    name: str
    role: str = "candidate"

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Registration successful. Welcome to SuperJob!",
                "user_id": 101,
                "email": "jane.smith@gmail.com",
                "name": "Jane Smith",
                "role": "candidate",
            }
        }


# =====================================================
# GOOGLE OAUTH
# =====================================================


class GoogleAuthRequest(BaseModel):
    """
    Google OAuth Request - for Talent login/register

    Design Reference: Image 3 & 4 - "Continue with Google" / "Sign up with Google"
    """

    id_token: str = Field(..., description="Google ID token from frontend OAuth")

    class Config:
        json_schema_extra = {
            "example": {"id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."}
        }


class GoogleAuthResponse(BaseModel):
    """Response after successful Google OAuth"""

    access_token: str
    token_type: str = "bearer"
    user: dict
    is_new_user: bool = False  # True if this was a new registration

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": 101,
                    "email": "jane.smith@gmail.com",
                    "name": "Jane Smith",
                    "role": "candidate",
                },
                "is_new_user": False,
            }
        }


# =====================================================
# FORGOT PASSWORD
# =====================================================


class ForgotPasswordRequest(BaseModel):
    """
    Forgot Password Request

    Design Reference: Image 1 & 3 - "Forgot Password?" link
    """

    email: EmailStr = Field(
        ..., description="Email address associated with the account"
    )

    class Config:
        json_schema_extra = {"example": {"email": "user@example.com"}}


class ForgotPasswordResponse(BaseModel):
    """Response after forgot password request"""

    message: str = "If the email exists, a password reset link has been sent."

    class Config:
        json_schema_extra = {
            "example": {
                "message": "If the email exists, a password reset link has been sent."
            }
        }


class ResetPasswordRequest(BaseModel):
    """Reset password with token"""

    token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(
        ..., min_length=8, max_length=72, description="New password"
    )

    @validator("new_password")
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    class Config:
        json_schema_extra = {
            "example": {"token": "abc123...", "new_password": "NewSecurePassword123"}
        }


class ResetPasswordResponse(BaseModel):
    """Response after password reset"""

    message: str = "Password has been reset successfully."

    class Config:
        json_schema_extra = {
            "example": {"message": "Password has been reset successfully."}
        }


# =====================================================
# LOGIN RESPONSE (Unified)
# =====================================================


class LoginResponse(BaseModel):
    """
    Unified Login Response for both Corporate and Talent

    Includes both access_token and refresh_token.
    - access_token: Short-lived token (default 30 min) for API requests
    - refresh_token: Long-lived token (default 7 days) for getting new access tokens
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(
        default=1800, description="Access token expiration in seconds"
    )
    refresh_expires_in: int = Field(
        default=604800, description="Refresh token expiration in seconds (7 days)"
    )
    user: dict = Field(..., description="User information")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "refresh_expires_in": 604800,
                "user": {
                    "id": 8,
                    "email": "employer@superjob.com",
                    "full_name": "Employer 1",
                    "role": "employer",
                    "is_active": True,
                },
            }
        }


# =====================================================
# REFRESH TOKEN
# =====================================================


class RefreshTokenRequest(BaseModel):
    """
    Request to get new access token using refresh token
    """

    refresh_token: str = Field(..., description="Refresh token from login response")

    class Config:
        json_schema_extra = {
            "example": {"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        }


class RefreshTokenResponse(BaseModel):
    """
    Response with new access token (and optionally new refresh token)
    """

    access_token: str
    refresh_token: Optional[str] = Field(
        None, description="New refresh token (if rotated)"
    )
    token_type: str = "bearer"
    expires_in: int = Field(default=1800, description="Token expiration in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": None,
                "token_type": "bearer",
                "expires_in": 1800,
            }
        }
