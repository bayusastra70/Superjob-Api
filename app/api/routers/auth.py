from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
import logging

from app.services.auth import auth, create_access_token
from app.schemas.models import UserLogin, Token
from app.schemas.user import UserCreate, UserResponse
from app.core.config import settings
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/token",
    response_model=Token,
    summary="Login - Get JWT Token",
    description="""
    Login dengan email dan password untuk mendapatkan JWT access token.
    
    **Test Credentials:**
    
    | Email | Password | Role |
    |-------|----------|------|
    | `admin@superjob.com` | `password123` | admin |
    | `employer@superjob.com` | `password123` | employer |
    | `tanaka@gmail.com` | `password123` | employer |
    | `candidate@superjob.com` | `password123` | candidate |
    
    **Cara menggunakan token:**
    1. Copy `access_token` dari response
    2. Klik tombol **Authorize** di kanan atas Swagger
    3. Paste token dan klik **Authorize**
    """,
)
async def login_for_access_token(user_data: UserLogin):
    """Login and get JWT token"""
    # Authenticate user against standalone database
    user = auth.authenticate_user(user_data.email, user_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"]},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


# @router.post(
#     "/register",
#     summary="Register New User",
#     description="""
#     Registrasi user baru.
    
#     **Role yang tersedia:**
#     - `candidate` - Pencari kerja
#     - `employer` - Pemberi kerja / HR
#     - `admin` - Administrator sistem
#     """,
# )
# async def register_user(user_data: UserCreate):
#     """Register new user"""
#     logger.info(
#         f"Registration attempt for: {user_data.email} with role: {user_data.role}"
#     )

#     result = auth.create_user(
#         email=user_data.email,
#         username=user_data.username,
#         password=user_data.password,
#         full_name=user_data.full_name,
#         role=user_data.role,  # Tambahkan role
#     )

#     if not result:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="User registration failed. Email or username may already exist.",
#         )

#     return {
#         "message": "User created successfully",
#         "user": {
#             "id": result["id"],
#             "email": result["email"],
#             "username": result["username"],
#             "full_name": result["full_name"],
#             "role": result["role"],  # Tambahkan role di response
#             "is_active": result["is_active"],
#         },
#     }

@router.post(
    "/register",
    summary="Register New User",
    description="""
    Registrasi user baru.
    
    **Role yang tersedia:**
    - `candidate` - Pencari kerja
    - `employer` - Pemberi kerja / HR
    - `admin` - Administrator sistem
    
    **Note:** Nomor telepon harus unik dan dalam format Indonesia (contoh: 081234567890)
    """,
)
async def register_user(user_data: UserCreate):
    """Register new user"""
    logger.info(
        f"Registration attempt for: {user_data.email} with role: {user_data.role}"
    )

    result = auth.create_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        full_name=user_data.full_name,
        phone=user_data.phone,  # Tambahkan phone
        role=user_data.role,
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
            "phone": result["phone"],  # Tambahkan phone di response
            "role": result["role"],
            "is_active": result["is_active"],
        },
    }


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
