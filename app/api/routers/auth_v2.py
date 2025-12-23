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
import logging
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
    CorporateRegisterResponse,
    # Talent
    TalentLoginRequest,
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

logger = logging.getLogger(__name__)
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


@router.post(
    "/corporate/register",
    response_model=CorporateRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Corporate Registration",
    description="""
    Registrasi akun Employer/Corporate baru.
    
    **Design Reference:** "Welcome to Superjob" registration form
    
    **Fields:**
    - Contact Name (nama lengkap contact person)
    - Company Name (nama perusahaan)
    - Email Address (email bisnis)
    - Phone Number (nomor telepon dengan format +62)
    - Password (minimal 8 karakter)
    
    **Note:** NIB Document upload dilakukan terpisah setelah registrasi berhasil.
    """,
    tags=["Authentication - Corporate"],
)
async def corporate_register(
    contact_name: str = Form(
        ..., description="Nama contact person", example="John Doe"
    ),
    company_name: str = Form(
        ..., description="Nama perusahaan", example="PT Teknologi Maju"
    ),
    email: str = Form(..., description="Email bisnis", example="hr@teknologimaju.com"),
    phone_number: str = Form(
        ..., description="Nomor telepon", example="+6281234567890"
    ),
    password: str = Form(..., min_length=8, description="Password minimal 8 karakter"),
    nib_document: Optional[UploadFile] = File(
        None, description="NIB Document (PDF only)"
    ),
):
    """
    Register new employer/corporate account with optional NIB document upload
    """
    logger.info(f"Corporate registration attempt for: {email}")

    # Validate NIB document if provided
    nib_file_path = None
    if nib_document:
        # Check file type
        if not nib_document.content_type == "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="NIB Document harus berformat PDF",
            )

        # Check file size (max 5MB)
        content = await nib_document.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ukuran file NIB maksimal 5MB",
            )

        # Save file
        file_extension = ".pdf"
        file_name = f"{uuid.uuid4()}{file_extension}"
        nib_file_path = NIB_UPLOAD_DIR / file_name

        with open(nib_file_path, "wb") as f:
            f.write(content)

        logger.info(f"NIB document saved: {nib_file_path}")

    # Generate username from email
    username = email.split("@")[0] + "_" + str(uuid.uuid4())[:8]

    # Create user with employer role
    result = auth.create_user(
        email=email,
        username=username,
        password=password,
        full_name=contact_name,
        role="employer",
    )

    if not result:
        # Clean up uploaded file if registration failed
        if nib_file_path and os.path.exists(nib_file_path):
            os.remove(nib_file_path)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registrasi gagal. Email mungkin sudah terdaftar.",
        )

    # TODO: Save company_name and phone_number to a separate corporate_profiles table
    # TODO: Save nib_file_path reference to database
    # TODO: Implement email verification

    logger.info(f"Corporate registration successful: {email}")

    return CorporateRegisterResponse(
        message="Registrasi berhasil. Silakan tunggu verifikasi akun.",
        user_id=result["id"],
        email=result["email"],
        company_name=company_name,
        role="employer",
        is_verified=False,
    )


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
    
    **Design Reference:** "Welcome to SuperJob" registration form
    
    **Fields:**
    - Name* (nama lengkap)
    - Email* (email)
    - Password* (minimal 8 karakter)
    - CV Upload (PDF, opsional)
    
    **Note:** Untuk registrasi dengan Google, gunakan endpoint `/auth/talent/google`
    """,
    tags=["Authentication - Talent"],
)
async def talent_register(
    name: str = Form(..., description="Nama lengkap", example="Jane Smith"),
    email: str = Form(..., description="Email", example="jane.smith@gmail.com"),
    password: str = Form(..., min_length=8, description="Password minimal 8 karakter"),
    cv_file: Optional[UploadFile] = File(None, description="CV (PDF only)"),
):
    """
    Register new candidate/job seeker with optional CV upload
    """
    logger.info(f"Talent registration attempt for: {email}")

    # Validate CV if provided
    cv_file_path = None
    if cv_file:
        # Check file type
        if not cv_file.content_type == "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CV harus berformat PDF",
            )

        # Check file size (max 10MB)
        content = await cv_file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ukuran file CV maksimal 10MB",
            )

        # Save file
        file_extension = ".pdf"
        file_name = f"{uuid.uuid4()}{file_extension}"
        cv_file_path = CV_UPLOAD_DIR / file_name

        with open(cv_file_path, "wb") as f:
            f.write(content)

        logger.info(f"CV saved: {cv_file_path}")

    # Generate username from email
    username = email.split("@")[0] + "_" + str(uuid.uuid4())[:8]

    # Create user with candidate role
    result = auth.create_user(
        email=email,
        username=username,
        password=password,
        full_name=name,
        role="candidate",
    )

    if not result:
        # Clean up uploaded file if registration failed
        if cv_file_path and os.path.exists(cv_file_path):
            os.remove(cv_file_path)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registrasi gagal. Email mungkin sudah terdaftar.",
        )

    # TODO: Save cv_file_path reference to candidate_profiles table

    logger.info(f"Talent registration successful: {email}")

    return TalentRegisterResponse(
        message="Registrasi berhasil. Selamat datang di SuperJob!",
        user_id=result["id"],
        email=result["email"],
        name=name,
        role="candidate",
    )


@router.post(
    "/talent/google",
    response_model=GoogleAuthResponse,
    summary="Google OAuth for Talent",
    description="""
    Login atau Register menggunakan akun Google.
    
    **Design Reference:** 
    - Image 3: "Continue with Google" button
    - Image 4: "Sign up with Google" button
    
    **Flow:**
    1. Frontend melakukan Google OAuth dan mendapatkan `id_token`
    2. Kirim `id_token` ke endpoint ini
    3. Backend akan memverifikasi token dan login/register user
    
    **Note:** Jika user belum terdaftar, akan otomatis membuat akun baru dengan role `candidate`
    """,
    tags=["Authentication - Talent"],
)
async def google_auth_talent(request: GoogleAuthRequest):
    """
    Authenticate or register user via Google OAuth
    """
    # TODO: Implement Google OAuth verification
    # 1. Verify the id_token with Google
    # 2. Extract user info (email, name, picture)
    # 3. Check if user exists, if not create new account
    # 4. Return access token

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth belum diimplementasikan. Akan segera tersedia.",
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
