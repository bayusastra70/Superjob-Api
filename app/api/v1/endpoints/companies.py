from fastapi import APIRouter, Depends, Query, status, HTTPException
from app.schemas.company_schema import CompanyResponse
from app.schemas.response_schema import APIResponse
from app.models.company import Company
from app.db.session import get_db
from sqlalchemy.orm import Session
from typing import List

from app.services import company_service
from app.utils.response import success_response
import uuid

router = APIRouter(prefix="/companies", tags=["companies"])

# @router.get("/", response_model=APIResponse[List[CompanyResponse]], status_code=status.HTTP_200_OK)
# async def get_companies(db: Session = Depends(get_db), skip: int = 0, limit: int = 10):
#     companies = db.query(Company).offset(skip).limit(limit).all()
#     return success_response(companies)

@router.get("/{company_id}", response_model=APIResponse[CompanyResponse], status_code=status.HTTP_200_OK)
async def get_company(company_id: str, db: Session = Depends(get_db)):
    company = company_service.get_company_by_id(db, company_id)
    return success_response(company)