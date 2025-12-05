from sqlalchemy.orm import Session
from typing import Tuple, List
from app.models.company import Company
from app.schemas.company_schema import CompanyCreate, CompanyUpdate
from fastapi import HTTPException, status
import uuid

def get_company_by_id(db: Session, company_id: str) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Company not found"
        )
    return company

# def get_companies(db: Session, skip: int = 0, limit: int = 10) -> List[Company]:
#     return db.query(Company).offset(skip).limit(limit).all()

# def create_company(db: Session, company: CompanyCreate) -> Company:
#     company = Company(**company.model_dump())
#     db.add(company)
#     db.commit()
#     db.refresh(company)
#     return company