from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
import logging


from app.services.auth import auth, create_access_token
from app.schemas.models import UserLogin, Token
from app.schemas.user import UserCreate, UserResponse
from app.core.config import settings
from app.core.security import get_current_user

from app.schemas.response import BaseResponse

from app.utils.response import (
    success_response,
    unauthorized_response,
    internal_server_error_response
)

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["Authentication"])

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
