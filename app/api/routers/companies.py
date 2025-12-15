from fastapi import APIRouter, Depends, Query, status, HTTPException
from app.schemas.company_schema import CompanyResponse
from app.schemas.company_review_schema import CompanyReviewsResponse, CompanyRatingSummaryResponse
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import company_service

router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("/{company_id}", response_model=CompanyResponse, status_code=status.HTTP_200_OK)
async def get_company(company_id: str, db: AsyncSession = Depends(get_db)):
    company = await company_service.get_company_by_id(db, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company

@router.get("/{company_id}/reviews", response_model=CompanyReviewsResponse, status_code=status.HTTP_200_OK)
async def get_company_reviews(
    company_id: str,
    sort: str = Query("recent", description="recent|oldest|highest|lowest"),
    department: str = Query(None, description="all|hr|sales|marketing|finance|accounting|ui-ux|engineering"),
    employment_duration: str = Query(None, description="all|0|1-2|3-5|5-10|5+"),
    employment_status: str = Query(None, description="all|full-time|part-time|contract|freelance|intern|former"),
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

@router.get("/{company_id}/rating-summary", response_model=CompanyRatingSummaryResponse, status_code=status.HTTP_200_OK)
async def get_company_rating_summary(company_id: str, db: AsyncSession = Depends(get_db)):
    rating_summary = await company_service.get_company_rating_summary(db, company_id)
    return rating_summary