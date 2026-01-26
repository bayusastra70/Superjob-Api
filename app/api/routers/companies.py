from fastapi import APIRouter, Depends, Query, status, HTTPException, Request, Path, Form, File, UploadFile
from app.schemas.company_schema import (
    CompanyResponse, 
    CompanyUsersListResponse,
    CreateCompanyUser,
    CreateCompanyUserResponse,
    UpdateCompanyUser,
    UpdateCompanyUserResponse
)
from app.schemas.company_review_schema import (
    CompanyReviewsResponse,
    CompanyRatingSummaryResponse,
)
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import company_service
from app.services.activity_log_service import activity_log_service
from loguru import logger
from app.core.security import get_current_user
from app.schemas.user import UserResponse
from typing import Optional
from app.schemas.response import BaseResponse
from app.utils.response import success_response
from app.services.role_base_access_control_service import RoleBaseAccessControlService


router = APIRouter(prefix="/companies", tags=["companies"])


@router.get(
    "/{company_id}",
    response_model=BaseResponse[CompanyResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Company Profile",
    description="""
    Mendapatkan detail profil perusahaan berdasarkan ID.
    """,
    responses={
        200: {"description": "Detail profil perusahaan berhasil diambil"},
        404: {"description": "Perusahaan tidak ditemukan"},
    },
)
async def get_company(
    company_id: int = Path(..., gt=0),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Mendapatkan detail profil perusahaan berdasarkan ID.

    Args:
        company_id: ID perusahaan yang ingin diambil.
        current_user: Current authenticated user.

    Returns:
        CompanyResponse: Detail profil perusahaan.

    Raises:
        HTTPException: 403 jika user tidak berwenang, 404 jika perusahaan tidak ditemukan.
    """
    # Authorization Check: User can only view their own company (unless superuser)
    if not current_user.is_superuser:
        if current_user.company_id != company_id:
            logger.warning(f"Unauthorized access attempt for company {company_id} by user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this company's profile."
            )

    company = company_service.get_company_by_id(company_id)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    return success_response(
        data=company,
        message="Detail profil perusahaan berhasil diambil"
    )


@router.get(
    "/{company_id}/reviews",
    response_model=CompanyReviewsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Company Reviews",
    description="""
    Mendapatkan daftar review perusahaan dengan filter dan pagination.
    
    **Format company_id:** Integer ID (contoh: `123`)
    
    **Query Parameters:**
    
    | Parameter | Values | Description |
    |-----------|--------|-------------|
    | `sort` | recent, oldest, highest, lowest | Urutan sorting |
    | `department` | all, hr, sales, marketing, finance, accounting, ui-ux, engineering | Filter departemen |
    | `employment_duration` | all, 0, 1-2, 3-5, 5-10, 5+ | Filter lama bekerja (tahun) |
    | `employment_status` | all, full-time, part-time, contract, freelance, intern, former | Filter status karyawan |
    | `page` | ≥1 | Nomor halaman |
    | `limit` | 1-100 | Jumlah item per halaman |
    
    **Data yang Dikembalikan:**
    - `reviews`: Array review dari karyawan
    - `total`: Total jumlah review
    - `page`, `limit`: Info pagination
    
    **Response:**
    - `200 OK`: Daftar review berhasil diambil
    """,
    responses={
        200: {"description": "Daftar review berhasil diambil"},
    },
)
async def get_company_reviews(
    company_id: int = Path(..., gt=0),
    sort: str = Query(
        "recent",
        description="Urutan sorting: recent, oldest, highest, lowest",
    ),
    department: str = Query(
        None,
        description="Filter departemen: all, hr, sales, marketing, finance, accounting, ui-ux, engineering",
    ),
    employment_duration: str = Query(
        None,
        description="Filter lama bekerja: all, 0, 1-2, 3-5, 5-10, 5+ (tahun)",
    ),
    employment_status: str = Query(
        None,
        description="Filter status: all, full-time, part-time, contract, freelance, intern, former",
    ),
    page: int = Query(1, ge=1, description="Nomor halaman"),
    limit: int = Query(10, ge=1, le=100, description="Jumlah item per halaman"),
    db: AsyncSession = Depends(get_db),
):
    """
    Mendapatkan daftar review perusahaan dengan filter.

    Args:
        company_id: ID perusahaan.
        sort: Urutan sorting.
        department: Filter departemen.
        employment_duration: Filter lama bekerja.
        employment_status: Filter status karyawan.
        page: Nomor halaman.
        limit: Jumlah item per halaman.
        db: Database session.

    Returns:
        CompanyReviewsResponse: Daftar review dengan pagination.
    """
    company_reviews = await company_service.get_company_reviews_by_company_id(
        db=db,
        company_id=company_id,
        sort=sort,
        department=department,
        employment_duration=employment_duration,
        employment_status=employment_status,
        page=page,
        limit=limit,
    )
    return company_reviews


@router.get(
    "/{company_id}/rating-summary",
    response_model=CompanyRatingSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Company Rating Summary",
    description="""
    Mendapatkan ringkasan rating perusahaan.
    
    **Format company_id:** Integer ID (contoh: `123`)
    
    **Data yang Dikembalikan:**
    - `average_rating`: Rating rata-rata (1-5)
    - `total_reviews`: Total jumlah review
    - `rating_distribution`: Distribusi rating (1-5 star)
    - `category_ratings`: Rating per kategori
      - `work_life_balance`
      - `salary_benefits`
      - `career_growth`
      - `management`
      - `culture`
    
    **Contoh Response:**
    ```json
    {
        "average_rating": 4.2,
        "total_reviews": 150,
        "rating_distribution": {
            "5": 50,
            "4": 60,
            "3": 25,
            "2": 10,
            "1": 5
        },
        "category_ratings": {
            "work_life_balance": 4.0,
            "salary_benefits": 3.8,
            "career_growth": 4.3,
            "management": 4.1,
            "culture": 4.5
        }
    }
    ```
    
    **Response:**
    - `200 OK`: Rating summary berhasil diambil
    """,
    responses={
        200: {"description": "Rating summary berhasil diambil"},
    },
)
async def get_company_rating_summary(
    company_id: int = Path(..., gt=0), db: AsyncSession = Depends(get_db)
):
    """
    Mendapatkan ringkasan rating perusahaan.

    Args:
        company_id: ID perusahaan.
        db: Database session.

    Returns:
        CompanyRatingSummaryResponse: Ringkasan rating dengan breakdown.
    """
    rating_summary = await company_service.get_company_rating_summary(db, company_id)
    return rating_summary


@router.put(
    "/{company_id}",
    response_model=BaseResponse[CompanyResponse],
    status_code=status.HTTP_200_OK,
    summary="Update Company Profile",
    description="""
    Update profil perusahaan.
    
    **Mendukung File Upload:**
    - `logo`: File gambar logo (optional)
    - `nib_document`: File PDF NIB (optional)
    
    **Fields lainnya (partial update):**
    - `name`, `industry`, `description`, `website`, `location`, `founded_year`, `employee_size`, `linkedin_url`, `twitter_url`, `instagram_url`
    
    **Catatan:**
    - Jika mengupload file baru, file lama di Solvera Storage akan dihapus otomatis.
    - NIB harus berformat PDF dan maksimal 10MB.
    """,
    responses={
        200: {"description": "Profil perusahaan berhasil diupdate"},
        404: {"description": "Perusahaan tidak ditemukan"},
    },
)
async def update_company(
    request: Request,
    company_id: int = Path(..., gt=0),
    name: Optional[str] = Form(None),
    industry: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    founded_year: Optional[int] = Form(None),
    employee_size: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    twitter_url: Optional[str] = Form(None),
    instagram_url: Optional[str] = Form(None),
    facebook_url: Optional[str] = Form(None),
    tiktok_url: Optional[str] = Form(None),
    youtube_url: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    logo: Optional[UploadFile] = File(None),
    nib_document: Optional[UploadFile] = File(None),
    npwp_document: Optional[UploadFile] = File(None),
    proposal_document: Optional[UploadFile] = File(None),
    portfolio_document: Optional[UploadFile] = File(None),
    current_user: UserResponse = Depends(get_current_user),
):
    """Update profil perusahaan dengan dukungan file upload."""
    logger.info(f"Received update request for company {company_id} from user {current_user.id}")
    
    # 0. Security check: Only Admin role can update company profile
    if not RoleBaseAccessControlService.user_has_role(current_user.id, "admin"):
        logger.warning(f"Unauthorized update attempt for company {company_id} by user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can edit the company profile."
        )
    
    # 1. Collect text updates
    text_updates = {
        "name": name,
        "industry": industry,
        "description": description,
        "website": website,
        "location": location,
        "founded_year": founded_year,
        "employee_size": employee_size,
        "linkedin_url": linkedin_url,
        "twitter_url": twitter_url,
        "instagram_url": instagram_url,
        "facebook_url": facebook_url,
        "tiktok_url": tiktok_url,
        "youtube_url": youtube_url,
        "phone": phone,
        "email": email,
    }

    # 2. Call Service to handle full update (files + text)
    company = await company_service.update_company_profile(
        company_id=company_id,
        updates=text_updates,
        logo=logo,
        nib_document=nib_document,
        npwp_document=npwp_document,
        proposal_document=proposal_document,
        portfolio_document=portfolio_document,
        current_user_id=current_user.id
    )

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )

    # 3. Log activity if anything changed
    changed_fields = company.get("_changed_fields", [])
    if changed_fields:
        activity_log_service.log_company_profile_updated(
            employer_id=current_user.id,
            company_name=company["name"],
            updated_fields=changed_fields,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            role="employer",
        )
    else:
        logger.info(f"No changes detected for company {company_id}")

    return success_response(
        data=company,
        message="Profil perusahaan berhasil diupdate"
    )


@router.get(
    "/{company_id}/users",
    response_model=CompanyUsersListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Company Users",
    description="""
    Get all users associated with a specific company.
    
    **Format company_id:** Integer ID
    
    **Query Parameters:**
    - `page`: Page number (≥1)
    - `limit`: Items per page (1-100)
    - `search`: Search in email, username, or full_name
    - `role_id`: Filter by role ID from endpoint "/v1/roles"
    - `is_active`: Filter by active status
    - `sort_by`: Field to sort by (default: created_at)
    - `sort_order`: Sort order: asc or desc (default: desc)
    
    **Features:**
    - Pagination support
    - Search and filtering
    - Returns: id, full_name, phone, email, default_role_id, role_name
    
    **Response:**
    - `200 OK`: List of users retrieved successfully
    - `403 Forbidden`: User does not belong to the company
    - `404 Not Found`: Company not found
    """,
    responses={
        200: {"description": "List of users retrieved successfully"},
        403: {"description": "Not authorized to access this company's data"},
        404: {"description": "Company not found"},
    },
)
async def get_company_users(
    company_id: int = Path(..., title="ID Perusahaan", gt=0),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in email, username, full_name"),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get all users associated with a company.
    
    **Authentication Required:** User must be logged in and belong to the requested company.
    
    Args:
        company_id: ID of the company
        page: Page number
        limit: Items per page
        search: Search query
        role_id: Role filter
        is_active: Active status filter
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        CompanyUsersListResponse: List of users with pagination
    
    Raises:
        HTTPException: 401 if not authenticated, 403 if not authorized, 404 if company not found
    """
    return await company_service.get_company_users(
        company_id=company_id,
        current_user_id=current_user.id,
        page=page,
        limit=limit,
        search=search,
        role_id=role_id,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.post(
    "/{company_id}/users",
    response_model=CreateCompanyUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add User to Company",
    description="""
    Create a new user and add them to the company team.
    
    **Authorization Required:**
    - User must be logged in and belong to the company.
    
    **Validation:**
    - Validates email and username uniqueness globally.
    - Automatically links the new user to the specified company.
    
    **Response:**
    - `201 Created`: User created and linked to company.
    - `400 Bad Request`: Email/Username/Phone already exists, or attempt to assign Admin role.
    - `403 Forbidden`: Permission denied or doesn't belong to company.
    """,
)
async def create_company_user(
    user_data: CreateCompanyUser,
    company_id: int = Path(..., title="ID Perusahaan", gt=0),
    current_user: UserResponse = Depends(get_current_user),
):
    # RBAC Permission Check
    if not current_user.is_superuser:
        if not RoleBaseAccessControlService.user_has_permission(current_user.id, 'user.create'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied. Required: 'user.create'"
            )

    new_user = await company_service.create_company_user(
        company_id=company_id,
        user_data=user_data,
        current_user_id=current_user.id
    )
    
    return CreateCompanyUserResponse(
        success=True,
        message="User created and added to company successfully",
        user=new_user
    )


@router.put(
    "/{company_id}/users/{user_id}",
    response_model=UpdateCompanyUserResponse,
    summary="Update Company User",
    description="""
    Update an existing user's details within a company.
    
    **Authorization Required:**
    - User must be logged in and belong to the company.
    
    **Updatable Fields:**
    - full_name
    - phone (optional)
    - role_id (except 1)
    - is_active
    """,
)
async def update_company_user(
    user_data: UpdateCompanyUser,
    company_id: int = Path(..., title="ID Perusahaan", gt=0),
    user_id: int = Path(..., title="ID User", gt=0),
    current_user: UserResponse = Depends(get_current_user),
):
    # RBAC Permission Check
    if not current_user.is_superuser:
        if not RoleBaseAccessControlService.user_has_permission(current_user.id, 'user.update'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied. Required: 'user.update'"
            )

    updated_user = await company_service.update_company_user(
        company_id=company_id,
        user_id=user_id,
        user_data=user_data,
        current_user_id=current_user.id
    )
    
    return UpdateCompanyUserResponse(
        success=True,
        message="User updated successfully",
        user=updated_user
    )


@router.delete(
    "/{company_id}/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove User from Company",
    description="""
    Permanently delete a user account from the system.
    This is a **hard delete** and irreversible; it removes the user globally from the 'users' table and all company associations.
    
    **Authorization Required:**
    - User must be logged in and belong to the company.
    - Requires 'user.delete' permission.
    - Users cannot delete their own accounts via this endpoint.
    """,
)
async def delete_company_user(
    company_id: int = Path(..., title="ID Perusahaan", gt=0),
    user_id: int = Path(..., title="ID User", gt=0),
    current_user: UserResponse = Depends(get_current_user),
):
    # RBAC Permission Check
    if not current_user.is_superuser:
        if not RoleBaseAccessControlService.user_has_permission(current_user.id, 'user.delete'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied. Required: 'user.delete'"
            )

    await company_service.delete_company_user(
        company_id=company_id,
        user_id=user_id,
        current_user_id=current_user.id
    )
    return None


