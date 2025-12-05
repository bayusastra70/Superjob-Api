from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
from app.models.company import Company
from app.models.company_review import CompanyReview
from fastapi import HTTPException, status

def get_company_by_id(db: Session, company_id: str) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Company not found"
        )
    return company

def get_company_reviews_by_company_id(
    db: Session,
    company_id: str,
    sort: str = "recent",
    page: int = 1,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Fetch company reviews with simple pagination and sorting.

    sort options:
    - recent: created_at desc
    - oldest: created_at asc
    - rating_desc: rating desc
    - rating_asc: rating asc
    """
    company = get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Company not found"
        )

    sort_map = {
        "recent": CompanyReview.created_at.desc(),
        "oldest": CompanyReview.created_at.asc(),
        "rating_desc": CompanyReview.rating.desc(),
        "rating_asc": CompanyReview.rating.asc(),
    }
    order_clause = sort_map.get(sort, sort_map["recent"])

    offset = (page - 1) * limit

    base_query = db.query(CompanyReview).filter(CompanyReview.company_id == company_id)

    total_reviews = base_query.count()
    total_pages = (total_reviews + limit - 1) // limit if total_reviews > 0 else 0

    avg_rating = db.query(func.avg(CompanyReview.rating)).filter(CompanyReview.company_id == company_id).scalar()
    average_rating = float(avg_rating) if avg_rating is not None else 0.0

    breakdown_rows = (
        db.query(CompanyReview.rating, func.count(CompanyReview.id))
        .filter(CompanyReview.company_id == company_id)
        .group_by(CompanyReview.rating)
        .all()
    )

    rating_breakdown: Dict[str, int] = {str(i): 0 for i in range(5, 0, -1)}
    rating_breakdown.update({str(rating): count for rating, count in breakdown_rows})

    reviews = (
        base_query.order_by(order_clause)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "company_id": company_id,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        },
        "summary": {
            "average_rating": average_rating,
            "total_reviews": total_reviews,
            "rating_breakdown": rating_breakdown,
        },
        "reviews": reviews,
    }