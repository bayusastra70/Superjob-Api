from fastapi import APIRouter, Depends, Query, status, HTTPException, Request
from app.schemas.company_schema import CompanyResponse, CompanyUpdate
from app.schemas.company_review_schema import (
    CompanyReviewsResponse,
    CompanyRatingSummaryResponse,
)
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import company_service
from app.services.activity_log_service import activity_log_service
from app.core.security import get_current_user
from app.schemas.user import UserResponse


router = APIRouter(prefix="/companies", tags=["companies"])


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Company Details",
    description="""
    Mendapatkan detail profil perusahaan berdasarkan ID.
    
    **Format company_id:** String UUID (contoh: `comp-123`)
    
    **Data yang Dikembalikan:**
    - `id`: ID perusahaan
    - `name`: Nama perusahaan
    - `industry`: Industri perusahaan
    - `description`: Deskripsi perusahaan
    - `website`: URL website
    - `location`: Lokasi kantor
    - `logo_url`: URL logo perusahaan
    - `founded_year`: Tahun didirikan
    - `employee_size`: Jumlah karyawan
    - `linkedin_url`, `twitter_url`, `instagram_url`: Social media links
    
    **Response:**
    - `200 OK`: Detail perusahaan berhasil diambil
    - `404 Not Found`: Perusahaan tidak ditemukan
    """,
    responses={
        200: {"description": "Detail perusahaan berhasil diambil"},
        404: {"description": "Perusahaan tidak ditemukan"},
    },
)
async def get_company(company_id: str, db: AsyncSession = Depends(get_db)):
    """
    Mendapatkan detail profil perusahaan berdasarkan ID.

    Args:
        company_id: ID perusahaan yang ingin diambil.
        db: Database session.

    Returns:
        CompanyResponse: Detail profil perusahaan.

    Raises:
        HTTPException: 404 jika perusahaan tidak ditemukan.
    """
    company = await company_service.get_company_by_id(db, company_id)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    return company


@router.get(
    "/{company_id}/reviews",
    response_model=CompanyReviewsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Company Reviews",
    description="""
    Mendapatkan daftar review perusahaan dengan filter dan pagination.
    
    **Format company_id:** String UUID (contoh: `comp-123`)
    
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
    company_id: str,
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
    
    **Format company_id:** String UUID (contoh: `comp-123`)
    
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
    company_id: str, db: AsyncSession = Depends(get_db)
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
    response_model=CompanyResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Company Profile",
    description="""
    Update profil perusahaan.
    
    **Format company_id:** String UUID (contoh: `comp-123`)
    
    **Fields yang bisa diupdate (partial update):**
    - `name`: Nama perusahaan
    - `industry`: Industri
    - `description`: Deskripsi perusahaan
    - `website`: URL website
    - `location`: Lokasi kantor
    - `logo_url`: URL logo
    - `founded_year`: Tahun didirikan
    - `employee_size`: Ukuran perusahaan
    - `linkedin_url`, `twitter_url`, `instagram_url`: Social media
    
    **Contoh Request Body:**
    ```json
    {
        "name": "PT Superjob Indonesia",
        "industry": "Technology",
        "description": "Platform rekrutmen terbaik di Indonesia",
        "website": "https://superjob.id",
        "employee_size": "50-100"
    }
    ```
    
    **Response:**
    - `200 OK`: Profil berhasil diupdate
    - `404 Not Found`: Perusahaan tidak ditemukan
    
    **⚠️ Membutuhkan Authorization Token!**
    
    **Catatan:**
    - Hanya field yang dikirim yang akan diupdate.
    - Activity log akan dicatat untuk setiap perubahan.
    """,
    responses={
        200: {"description": "Profil perusahaan berhasil diupdate"},
        404: {"description": "Perusahaan tidak ditemukan"},
    },
)
async def update_company(
    request: Request,
    company_id: str,
    company_data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Update profil perusahaan.

    Args:
        request: Request object untuk logging.
        company_id: ID perusahaan yang akan diupdate.
        company_data: Data yang akan diupdate.
        db: Database session.
        current_user: User yang melakukan update.

    Returns:
        CompanyResponse: Data perusahaan yang sudah diupdate.

    Raises:
        HTTPException: 404 jika perusahaan tidak ditemukan.
    """
    # Get existing company
    company = await company_service.get_company_by_id(db, company_id)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )

    # Get old company name for logging
    old_company_name = company.name

    # Track which fields are being updated
    updated_fields = []
    update_data = company_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None and hasattr(company, field):
            old_value = getattr(company, field)
            if old_value != value:
                setattr(company, field, value)
                updated_fields.append(field)

    if updated_fields:
        await db.commit()
        await db.refresh(company)

        # Log activity
        activity_log_service.log_company_profile_updated(
            employer_id=current_user.id,
            company_name=company.name or old_company_name,
            updated_fields=updated_fields,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            role="employer",
        )

    return company
