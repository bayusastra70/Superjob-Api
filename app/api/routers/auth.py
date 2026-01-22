from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
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
from pydantic import EmailStr
from app.schemas.models import UserLogin, Token
from app.schemas.user import UserCreate, UserResponse
from app.core.config import settings
from app.core.security import get_current_user

from app.schemas.response import BaseResponse

from app.utils.response import (
    success_response,
    unauthorized_response,
)

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["Authentication"])

from app.utils.storage import delete_vercel_blob
from app.utils.solvera_storage import solvera_storage, StorageFolder, UploaderName


@router.post(
    "/token",
    response_model=BaseResponse[Token], 
    summary="Login - Get JWT Token",
    
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
    
)
async def register_company(
    company_name: str = Form(..., min_length=2, max_length=200),
    email: EmailStr = Form(...),
    username: str = Form(..., min_length=3, max_length=50),
    password: str = Form(..., min_length=8, max_length=72),
    full_name: str = Form(..., min_length=2, max_length=100),
    phone: str = Form(..., min_length=10, max_length=20),
    nib_document: UploadFile = File(...)
):
    """
    Register a new company and its admin user with NIB document file upload.
    
    **File Requirements:**
    - Format: PDF only
    - Max size: 10MB
    - Required field
    
    The NIB document will be uploaded to Solvera Storage API.
    """
    uploaded_file_id = None
    uploaded_file_url = None
    
    try:
        # Pre-validate NIB document (Must be PDF and < 10MB)
        # 1. Magic byte check (Signature)
        header = await nib_document.read(5)
        await nib_document.seek(0)
        
        if not header.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"NIB document is not a valid PDF file (Signature mismatch)."
            )

        # 2. Content Type check
        if nib_document.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"NIB document metadata must be a PDF file. Got: {nib_document.content_type}"
            )
        
        nib_document.file.seek(0, 2)
        n_size = nib_document.file.tell()
        nib_document.file.seek(0)
        
        if n_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"NIB document exceeds 10MB limit (Size: {n_size / (1024*1024):.2f}MB)"
            )

        # 1. Upload NIB document to Solvera Storage
        logger.info(f"Uploading NIB document for company: {company_name}")
        upload_result = await solvera_storage.upload_file(
            file=nib_document,
            folder=StorageFolder.COMPANY_DOCUMENT,
            allowed_types=["application/pdf"],
            max_size_mb=10,
            uploader_name=UploaderName.SUPERJOB_SERVICE
        )
        
        uploaded_file_id = upload_result["id"]
        uploaded_file_url = upload_result["url"]
        logger.info(f"NIB document uploaded successfully: {uploaded_file_id} with url {uploaded_file_url}")
        
        # 2. Prepare Data for Atomic Service
        company_data = {
            "name": company_name,
            "industry": "-",            # Default, can be expanded later
            "description": "-",         # Default
            "website": "-",             # Default
            "location": "-",            # Default
            "logo_url": "",             # Empty for now, will be set via update endpoint
            "nib_document_url": uploaded_file_url,
            "nib_document_storage_id": uploaded_file_id,
            "founded_year": None,
            "employee_size": None,
            "is_verified": True,        # Bypass verification for now
            "email": email,             # Decoupled company email
            "phone": phone,             # Decoupled company phone
        }

        user_data = {
            "email": email,
            "username": username,
            "password": password,
            "full_name": full_name,
            "phone": phone,
        }

        # TODO: add email verification using OTP
        # 3. Call Atomic Service
        result = auth.create_company_with_admin(company_data, user_data)

        if not result.get("success"):
            # Cleanup: Delete the uploaded file from Solvera Storage if registration failed
            if uploaded_file_id:
                logger.info(f"Registration failed, cleaning up uploaded file: {uploaded_file_id}")
                await solvera_storage.delete_file(uploaded_file_id)

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Registration failed"),
            )
        
        # Map dictionary result to response schema
        response_data = CorporateRegisterResponse(
            message="Registrasi berhasil. Silakan verifikasi akun.",
            user_id=result["user_id"],
            email=email,
            company_name=company_name,
            role="employer", 
            is_verified=True,  # Bypass verification for now
            nib_document_url=uploaded_file_url,
        )

        return success_response(
            data=response_data,
            message="Success"
        )
        
    except HTTPException:
        # If it's already an HTTPException, re-raise it
        # But first cleanup the uploaded file if it exists
        if uploaded_file_id:
            logger.info(f"Exception occurred, cleaning up uploaded file: {uploaded_file_id}")
            await solvera_storage.delete_file(uploaded_file_id)
        raise
    except Exception as e:
        # Cleanup uploaded file on any error
        if uploaded_file_id:
            logger.error(f"Unexpected error, cleaning up uploaded file: {uploaded_file_id}")
            await solvera_storage.delete_file(uploaded_file_id)
        logger.error(f"Company registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to server error"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User",
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
