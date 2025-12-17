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
    "/{company_id}", response_model=CompanyResponse, status_code=status.HTTP_200_OK
)
async def get_company(company_id: str, db: AsyncSession = Depends(get_db)):
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
)
async def get_company_reviews(
    company_id: str,
    sort: str = Query("recent", description="recent|oldest|highest|lowest"),
    department: str = Query(
        None, description="all|hr|sales|marketing|finance|accounting|ui-ux|engineering"
    ),
    employment_duration: str = Query(None, description="all|0|1-2|3-5|5-10|5+"),
    employment_status: str = Query(
        None, description="all|full-time|part-time|contract|freelance|intern|former"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
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
)
async def get_company_rating_summary(
    company_id: str, db: AsyncSession = Depends(get_db)
):
    rating_summary = await company_service.get_company_rating_summary(db, company_id)
    return rating_summary


@router.put(
    "/{company_id}",
    response_model=CompanyResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Company Profile",
    description="""
    Update profil perusahaan. 
    
    **Fields yang bisa diupdate:**
    - `name`, `industry`, `description`
    - `website`, `location`, `logo_url`
    - `founded_year`, `employee_size`
    - `linkedin_url`, `twitter_url`, `instagram_url`
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
)
async def update_company(
    request: Request,
    company_id: str,
    company_data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Update company profile"""
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
