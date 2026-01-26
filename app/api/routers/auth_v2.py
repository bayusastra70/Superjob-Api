"""
Authentication Router for SuperJob API

Separate authentication endpoints for:
- Corporate (Employer/Admin/Recruiter)
- Talent (Candidate/Job Seeker)

Design Reference:
- Corporate Login: Image 1 - "Welcome, Partner!"
- Corporate Register: Image 2 - "Welcome to Superjob" with company details
- Talent Login: Image 3 - "Welcome Back!" with Google OAuth
- Talent Register: Image 4 - "Welcome to SuperJob" with CV upload
"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Depends
from fastapi.security import HTTPBearer
from typing import Optional
from loguru import logger
import os
import uuid
from pathlib import Path

from app.services.auth import (
    auth,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.schemas.auth import (
    # Corporate
    CorporateLoginRequest,
    # Talent
    TalentLoginRequest,
    TalentRegisterRequest,
    TalentRegisterResponse,
    # Google OAuth
    GoogleAuthRequest,
    GoogleAuthResponse,
    # Forgot Password
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    # Token Response
    Token,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from app.schemas.user import UserResponse
from app.core.config import settings
from app.core.security import get_current_user


security = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Directory for file uploads
UPLOAD_DIR = Path("uploads")
NIB_UPLOAD_DIR = UPLOAD_DIR / "nib_documents"
CV_UPLOAD_DIR = UPLOAD_DIR / "cv"

# Ensure directories exist
NIB_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CV_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# =====================================================
# CORPORATE AUTHENTICATION (Employer/Admin)
# =====================================================


@router.post(
    "/corporate/login",
    response_model=LoginResponse,
    summary="Corporate Login",
    description="""
    Login untuk Employer, Recruiter, atau Admin.
    
    **Design Reference:** "Welcome, Partner!" login form
    
    **Test Credentials:**
    | Email | Password | Role |
    |-------|----------|------|
    | `employer@superjob.com` | `employer123` | employer |
    | `tanaka@gmail.com` | `password123` | employer |
    | `admin@superjob.com` | `admin123` | admin |
    """,
    tags=["Authentication - Corporate"],
)
async def corporate_login(request: CorporateLoginRequest):
    """
    Login for employers/recruiters/admins
    """
    # Authenticate user
    user = auth.authenticate_user(request.email, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user details including role
    user_details = auth.get_user_by_email(request.email)

    if not user_details:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User tidak ditemukan",
        )

    # Check if user is employer or admin
    if user_details.get("role") not in ["employer", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses hanya untuk Employer atau Admin. Silakan gunakan login Talent.",
        )

    # Token payload
    token_data = {
        "sub": user["email"],
        "user_id": user["id"],
        "role": user_details.get("role"),
    }

    # Create access token (short-lived)
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires,
    )

    # Create refresh token (long-lived - 7 days)
    refresh_token = create_refresh_token(data=token_data)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        refresh_expires_in=7 * 24 * 60 * 60,  # 7 days in seconds
        user={
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "role": user_details.get("role"),
            "is_superuser": user.get("is_superuser", False),
        },
    )


# Helper for Vercel Blob deletion
async def delete_vercel_blob(url: Optional[str]):
    """Delete file from Vercel Blob"""
    token = os.getenv("BLOB_READ_WRITE_TOKEN")
    if not token:
        logger.warning("BLOB_READ_WRITE_TOKEN not set, cannot delete blob")
        return

    # Try using vercel_blob SDK first
    try:
        from vercel_blob import del_
        await del_(url, options={"token": token})
        logger.info(f"Deleted blob using SDK: {url}")
        return
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"Error deleting blob using SDK: {e}")
        # Valid attempt failed, return
        return

    # Fallback to HTTP request if SDK not installed (basic implementation)
    # Note: This is an approximation. Vercel Blob API might differ.
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            # Assuming Vercel Blob API endpoint structure
            # DELETE current URL with token?
            response = await client.delete(
                url, 
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code in [200, 204]:
                logger.info(f"Deleted blob using httpx: {url}")
            else:
                logger.warning(f"Failed to delete blob ({response.status_code}): {response.text}")
    except Exception as e:
        logger.error(f"Error deleting blob using httpx: {e}")




# =====================================================
# TALENT AUTHENTICATION (Candidate)
# =====================================================


@router.post(
    "/talent/login",
    response_model=LoginResponse,
    summary="Talent Login",
    description="""
    Login untuk Candidate/Job Seeker.
    
    **Design Reference:** "Welcome Back!" login form
    
    **Test Credentials:**
    | Email | Password |
    |-------|----------|
    | `candidate@superjob.com` | `candidate123` |
    | `john.doe@example.com` | `password123` |
    
    **Note:** Untuk login dengan Google, gunakan endpoint `/auth/talent/google`
    """,
    tags=["Authentication - Talent"],
)
async def talent_login(request: TalentLoginRequest):
    """
    Login for candidates/job seekers
    """
    # Authenticate user
    user = auth.authenticate_user(request.email, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user details including role
    user_details = auth.get_user_by_email(request.email)

    if not user_details:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User tidak ditemukan",
        )

    # Check if user is candidate
    if user_details.get("role") != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses hanya untuk Candidate. Silakan gunakan login Corporate.",
        )

    # Token payload
    token_data = {
        "sub": user["email"],
        "user_id": user["id"],
        "role": "candidate",
    }

    # Create access token (short-lived)
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires,
    )

    # Create refresh token (long-lived - 7 days)
    refresh_token = create_refresh_token(data=token_data)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        refresh_expires_in=7 * 24 * 60 * 60,  # 7 days in seconds
        user={
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "role": "candidate",
        },
    )


@router.post(
    "/talent/register",
    response_model=TalentRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Talent Registration",
    description="""
    Registrasi akun Candidate/Job Seeker baru.
    
    **Fields:**
    - Name* (nama lengkap)
    - Email* (email)
    - Password* (minimal 8 karakter)
    - cv_url (PDF URL dari Vercel Blob, opsional)
    
    **Note:** Endpoint ini sekarang menyimpan cv_url ke tabel candidate_info.
    """,
    tags=["Authentication - Talent"],
)
async def talent_register(
    request: TalentRegisterRequest,
):
    """
    Register new candidate/job seeker with optional CV URL
    """
    logger.info(f"Talent registration attempt for: {request.email}")

    # Convert HttpUrl to string for service layer
    cv_url_str = str(request.cv_url) if request.cv_url else None

    # Use the new centralized service method for transactional registration
    result = auth.register_talent(
        email=request.email,
        password=request.password,
        full_name=request.name,
        cv_url=cv_url_str
    )

    if not result:
        # Clean up uploaded blob if registration failed
        if request.cv_url:
            await delete_vercel_blob(cv_url_str)
            logger.info(f"Cleaned up blob after failed registration: {cv_url_str}")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registrasi gagal. Email mungkin sudah terdaftar.",
        )

    logger.info(f"Talent registration successful: {request.email}")

    return TalentRegisterResponse(
        message="Registrasi berhasil. Selamat datang di SuperJob!",
        user_id=result["id"],
        email=result["email"],
        name=request.name,
        role="candidate",
    )


@router.post(
    "/talent/google",
    response_model=LoginResponse,
    summary="Google OAuth for Talent",
    description="""
    Login atau Register menggunakan akun Google.
    
    **Flow:**
    1. Frontend melakukan Google OAuth dan mendapatkan `id_token`
    2. Kirim `id_token` ke endpoint ini
    3. Backend akan memverifikasi token dengan Google
    4. Jika user belum terdaftar, akan otomatis membuat akun baru dengan role `candidate`
    """,
    tags=["Authentication - Talent"],
)
async def google_auth_talent(request: GoogleAuthRequest):
    """
    Authenticate or register user via Google OAuth
    """
    # 1. Delegate verification and user management to service layer
    result = auth.google_authenticate_talent(request.id_token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gagal memproses login Google atau token tidak valid",
        )
    
    if "error" in result and result["error"] == "ROLE_MISMATCH":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email ini terdaftar sebagai Corporate. Silakan gunakan login Corporate.",
        )

    user = result["user"]
    is_new_user = result["is_new_user"]

    # 2. Generate tokens
    token_data = {
        "sub": user["email"],
        "user_id": user["id"],
        "role": "candidate",
    }

    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires,
    )
    refresh_token = create_refresh_token(data=token_data)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        refresh_expires_in=7 * 24 * 60 * 60,
        user={
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "role": "candidate",
        },
    )


# =====================================================
# FORGOT PASSWORD (Both Corporate & Talent)
# =====================================================


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Forgot Password",
    description="""
    Request reset password link.
    
    **Design Reference:** "Forgot Password?" link on login forms
    
    **Flow:**
    1. User memasukkan email
    2. Sistem mengirim email dengan link reset password
    3. User klik link dan memasukkan password baru
    
    **Note:** Untuk keamanan, response selalu sama baik email terdaftar atau tidak.
    """,
    tags=["Authentication - Password Reset"],
)
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request password reset email
    """
    logger.info(f"Forgot password request for: {request.email}")

    # Check if user exists
    user = auth.get_user_by_email(request.email)

    if user:
        # TODO: Generate reset token and send email
        # TODO: Store token in database with expiration
        logger.info(f"Password reset email would be sent to: {request.email}")
    else:
        logger.info(f"Forgot password for non-existent email: {request.email}")

    # Always return same message for security
    return ForgotPasswordResponse(
        message="Jika email terdaftar, link reset password telah dikirim."
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    summary="Reset Password",
    description="""
    Reset password dengan token dari email.
    
    **Flow:**
    1. User mendapat email dengan link reset
    2. Link berisi token reset
    3. User memasukkan password baru dengan token
    """,
    tags=["Authentication - Password Reset"],
)
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password with token
    """
    # TODO: Verify reset token
    # TODO: Update password in database
    # TODO: Invalidate token after use

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Reset password belum diimplementasikan. Akan segera tersedia.",
    )


# =====================================================
# REFRESH TOKEN
# =====================================================


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh Access Token",
    description="""
    Mendapatkan access token baru menggunakan refresh token.
    
    **Gunakan endpoint ini ketika:**
    - Access token sudah expired
    - Access token akan segera expired (preemptive refresh)
    
    **Flow:**
    1. Login dan simpan `refresh_token` dari response
    2. Ketika access token expired, kirim refresh token ke endpoint ini
    3. Gunakan access token baru untuk API requests
    
    **Note:** Refresh token valid selama 7 hari. Setelah itu user harus login ulang.
    """,
    tags=["Authentication - Token"],
)
async def refresh_access_token(request: RefreshTokenRequest):
    """
    Get new access token using refresh token
    """
    try:
        # Verify refresh token
        token_data = verify_refresh_token(request.refresh_token)

        # Get fresh user data
        user = auth.get_user_by_email(token_data["email"])

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User tidak ditemukan",
            )

        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Akun dinonaktifkan",
            )

        # Create new access token
        new_token_data = {
            "sub": user["email"],
            "user_id": user["id"],
            "role": user.get("role"),
        }

        access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data=new_token_data,
            expires_delta=access_token_expires,
        )

        logger.info(f"Access token refreshed for user: {user['email']}")

        return RefreshTokenResponse(
            access_token=new_access_token,
            refresh_token=None,  # Don't rotate refresh token by default
            token_type="bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


# =====================================================
# LEGACY ENDPOINTS (for backward compatibility)
# =====================================================


@router.post(
    "/token",
    response_model=Token,
    summary="[Legacy] Login - Get JWT Token",
    description="""
    **⚠️ DEPRECATED:** Gunakan `/auth/corporate/login` atau `/auth/talent/login`
    
    Login dengan email dan password untuk mendapatkan JWT access token.
    Endpoint ini tetap berfungsi untuk backward compatibility.
    """,
    tags=["Authentication - Legacy"],
)
async def login_for_access_token(email: str = Form(...), password: str = Form(...)):
    """Legacy login endpoint - for backward compatibility"""
    user = auth.authenticate_user(email, password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"]},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User",
    description="""
    Mendapatkan informasi user yang sedang login.
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    tags=["Authentication"],
)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user
