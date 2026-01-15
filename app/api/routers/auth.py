from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
import logging

from app.services.auth import (
    auth, 
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.schemas.auth import (
    CorporateRegisterRequest, 
    CorporateRegisterResponse,
    TalentRegisterRequest,
    TalentRegisterResponse,
    GoogleAuthRequest,
    LoginResponse,
)
from app.schemas.models import UserLogin, Token
from app.schemas.user import UserCreate, UserResponse
from app.core.config import settings
from app.core.security import get_current_user

from app.schemas.response import BaseResponse

from app.utils.response import (
    success_response,
    unauthorized_response,
)
from urllib.parse import urlparse
from pathlib import Path

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["Authentication"])

from app.utils.storage import delete_vercel_blob




# @router.post(
#     "/token",
#     response_model=Token,
#     summary="Login - Get JWT Token",
    
# )
# async def login_for_access_token(user_data: UserLogin):
#     """Login and get JWT token"""
#     # Authenticate user against standalone database
#     user = auth.authenticate_user(user_data.email, user_data.password)

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     # Create access token
#     access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user["email"], "user_id": user["id"]},
#         expires_delta=access_token_expires,
#     )

#     return Token(access_token=access_token, token_type="bearer")

@router.post(
    "/token",
    response_model=BaseResponse[Token], 
    summary="Login - Get JWT Token",
    responses={
        200: {
            "description": "Success",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "is_success": True,
                        "message": "Success",
                        "data": {
                            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "token_type": "bearer"
                        }
                    }
                }
            }
        },
        422: { 
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "code": 422,
                        "is_success": False,
                        "message": "Validation Error",
                        "data": {}
                    }
                }
            }
        }
    }
)
async def login_for_access_token(user_data: UserLogin) -> BaseResponse:
    """Login and get JWT token"""
    try:
        # Authenticate user
        user = auth.authenticate_user(user_data.email, user_data.password)
        
        if not user:
            return unauthorized_response(
                message="Incorrect email or password",
                raise_exception=True
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"], "user_id": user["id"]},
            expires_delta=access_token_expires,
        )
        
        token_data = Token(access_token=access_token, token_type="bearer")
        
        return success_response(
            data=token_data,
            message="Success"
        )
        
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        raise

@router.post(
    "/register",
    summary="Register New User",
)
async def register_user(user_data: UserCreate):
    """Register new user"""
    logger.info(
        f"Registration attempt for: {user_data.email} with role: {user_data.role} and role_id: {user_data.role_id}"
    )

    # Validate role_id if provided
    if user_data.role_id is not None:
        if not auth.role_exists(user_data.role_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role ID {user_data.role_id} does not exist or is inactive."
            )

    result = auth.create_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=user_data.role,
        role_id=user_data.role_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User registration failed. Email, username, or phone may already exist.",
        )

    return {
        "message": "User created successfully",
        "user": {
            "id": result["id"],
            "email": result["email"],
            "username": result["username"],
            "full_name": result["full_name"],
            "phone": result["phone"],
            "role": result["role"],
            "role_id": result.get("default_role_id"),
            "is_active": result["is_active"],
        },
    }


@router.post(
    "/register/company",
    summary="Register New Company and Admin User",
    description="""
    Registers a new company and its associated admin user in a single request. 
    Accepts `nib_document_url` passed from frontend (Vercel Blob).
    If registration fails, the backend attempts to delete the NIB file.
    """,
    response_model=BaseResponse[CorporateRegisterResponse],
    responses={
        200: {
            "description": "Registration successful",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "is_success": True,
                        "message": "Registration successful",
                        "data": {
                             "message": "Registrasi berhasil...",
                             "user_id": 45,
                             "email": "user@example.com",
                             "company_name": "PT Example",
                             "role": "employer",
                             "is_verified": False
                        }
                    }
                }
            }
        },
        400: {
            "description": "Registration failed",
            "content": {
                "application/json": {
                    "example": {
                        "code": 400,
                        "is_success": False,
                        "message": "Company already exists",
                        "data": None
                    }
                }
            }
        }
    }
)
async def register_company(request: CorporateRegisterRequest):
    """Register a new company and its admin user with Vercel Blob URL."""
    # 1. Prepare Data for Atomic Service
    company_data = {
        "name": request.company_name,
        "industry": "-",            # Default, can be expanded later
        "description": "-",         # Default
        "website": "-",             # Default
        "location": "-",            # Default
        "logo_url": "",             # Default
        "nib_document_url": str(request.nib_document_url),
        "founded_year": None,
        "employee_size": None,
    }

    user_data = {
        "email": request.email,
        "username": request.username,
        "password": request.password,
        "full_name": request.full_name,
        "phone": request.phone,
    }

    # TODO: add email verification using OTP
    # 2. Call Atomic Service
    result = auth.create_company_with_admin(company_data, user_data)

    if not result.get("success"):
        # Cleanup: Delete the uploaded file from Vercel Blob if registration failed
        if request.nib_document_url:
            await delete_vercel_blob(str(request.nib_document_url))

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Registration failed"),
        )
    
    # Map dictionary result to response schema
    response_data = CorporateRegisterResponse(
        message="Registrasi berhasil. Silakan tunggu verifikasi akun.",
        user_id=result["user_id"],
        email=request.email,
        company_name=request.company_name,
        role="employer", 
        is_verified=False,
        nib_document_url=str(request.nib_document_url),
    )

    return success_response(
        data=response_data,
        message="Success"
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User",
    description="""
    Mendapatkan informasi user yang sedang login.
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user


@router.post(
    "/talent/register",
    response_model=TalentRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Talent Registration",
)
async def talent_register(request: TalentRegisterRequest):
    """
    Register new candidate/job seeker with optional CV URL
    """
    cv_url_str = str(request.cv_url) if request.cv_url else None

    # Use centralized service method for transactional registration
    result = auth.register_talent(
        email=request.email,
        password=request.password,
        full_name=request.name,
        cv_url=cv_url_str
    )

    if not result:
        # Note: No Vercel Blob cleanup here as per user request
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registrasi gagal. Email mungkin sudah terdaftar.",
        )

    return TalentRegisterResponse(
        message="Registrasi berhasil. Selamat datang di SuperJob!",
        user_id=result["id"],
        email=result["email"],
        name=request.name,
        role="candidate",
    )


@router.post(
    "/talent/google",
    summary="Google OAuth for Talent",
)
async def google_auth_talent(request: GoogleAuthRequest):
    """
    Authenticate or register user via Google OAuth
    """
    try:
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

        # 2. Generate tokens
        token_data = {
            "sub": user["email"],
            "user_id": user["id"],
        }

        access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires,
        )

        token_data = Token(access_token=access_token, token_type="bearer")
        return success_response(
            data=token_data,
            message="Success"
        )
        
    except Exception as e:
        logging.error(f"Google Auth error: {str(e)}")
        raise
