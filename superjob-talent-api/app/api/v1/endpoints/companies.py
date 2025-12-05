from fastapi import APIRouter, Depends, Query, status
from app.schemas.company_schema import CompanyResponse
from app.schemas.company_review_schema import CompanyReviewsResponse
from app.schemas.response_schema import APIResponse
from app.db.session import get_db
from sqlalchemy.orm import Session

from app.services import company_service
from app.utils.response import success_response
import uuid

router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("/{company_id}", response_model=APIResponse[CompanyResponse], status_code=status.HTTP_200_OK)
async def get_company(company_id: str, db: Session = Depends(get_db)):
    company = company_service.get_company_by_id(db, company_id)
    return success_response(company)

@router.get("/{company_id}/reviews", response_model=APIResponse[CompanyReviewsResponse], status_code=status.HTTP_200_OK)
async def get_company_reviews(
    company_id: str,
    sort: str = Query("recent", description="recent|oldest|rating_desc|rating_asc"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    company_reviews = company_service.get_company_reviews_by_company_id(
        db=db,
        company_id=company_id,
        sort=sort,
        page=page,
        limit=limit,
    )
    return success_response(company_reviews)