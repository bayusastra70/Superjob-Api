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

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/token", response_model=Token)
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
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")




@router.post("/register")
async def register_user(user_data: UserCreate):
    """Register new user"""
    logger.info(f"Registration attempt for: {user_data.email} with role: {user_data.role}")
    
    result = auth.create_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        full_name=user_data.full_name,
        role=user_data.role  # Tambahkan role
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User registration failed. Email or username may already exist."
        )
    
    return {
        "message": "User created successfully",
        "user": {
            "id": result["id"],
            "email": result["email"],
            "username": result["username"],
            "full_name": result["full_name"],
            "role": result["role"],  # Tambahkan role di response
            "is_active": result["is_active"]
        }
    }


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user