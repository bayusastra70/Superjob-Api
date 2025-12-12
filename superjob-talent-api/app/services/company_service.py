from sqlalchemy.orm import Session
from sqlalchemy import func, case, cast, Float
from typing import Dict, Any
from app.models.company import Company
from app.models.company_review import CompanyReview
from app.schemas.company_review_schema import CompanyRatingSummaryResponse
from fastapi import HTTPException, status

def get_company_by_id(db: Session, company_id: str) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Company not found"
        )
    return company

def _employment_duration_in_years_expr():
    """
    Normalize free-form employment_duration strings (e.g. '3 years', '18 months')
    into a comparable float value in years using SQL so we can filter in the DB.
    """
    duration_lower = func.lower(CompanyReview.employment_duration)
    numeric_part = func.nullif(
        func.regexp_replace(duration_lower, r"[^0-9\.]", "", "g"),
        "",
    )
    numeric_value = cast(numeric_part, Float)
    is_month_value = func.strpos(duration_lower, "month") > 0
    return case(
        (is_month_value, numeric_value / 12.0),
        else_=numeric_value,
    )


def _apply_employment_duration_filter(query, duration_filter: str):
    duration_years = _employment_duration_in_years_expr()

    if duration_filter == "0":
        return query.filter(duration_years < 1)  # < 1 year
    if duration_filter == "1-2":
        return query.filter(duration_years >= 1, duration_years < 3)  # 1-2 yrs
    if duration_filter == "3-5":
        return query.filter(duration_years >= 3, duration_years < 5)  # 3-5 yrs
    if duration_filter == "5-10":
        return query.filter(duration_years >= 5, duration_years < 10)  # 5-10 yrs
    if duration_filter == "5+":
        return query.filter(duration_years >= 10)  # 10+ yrs

    return query


def get_company_reviews_by_company_id(
    db: Session,
    company_id: str,
    sort: str = "recent",
    page: int = 1,
    limit: int = 10,
    department: str = "all",
    employment_duration: str = "all",
    employment_status: str = "all",
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
        "highest": CompanyReview.rating.desc(),
        "lowest": CompanyReview.rating.asc(),
    }
    order_clause = sort_map.get(sort, sort_map["recent"])

    department_map = {
        "all": None,
        "hr": "hr",
        "sales": "sales",
        "marketing": "marketing",
        "finance": "finance",
        "accounting": "accounting",
        "ui-ux": "ui-ux",
        "engineering": "engineering",
    }

    department_clause = department_map.get(department, None)

    employment_duration_map = {
        "all": None,
        "0": "0",
        "1-2": "1-2",
        "3-5": "3-5",
        "5-10": "5-10",
        "5+": "5+",
    }
    employment_duration_clause = employment_duration_map.get(employment_duration, None)

    employment_status_map = {
        "all": None,
        "full-time": "full-time",
        "part-time": "part-time",
        "contract": "contract",
        "freelance": "freelance",
        "intern": "intern",
        "former": "former",
    }
    employment_status_clause = employment_status_map.get(employment_status, None)

    offset = (page - 1) * limit

    base_query = db.query(CompanyReview).filter(CompanyReview.company_id == company_id)

    if department_clause is not None:
        base_query = base_query.filter(CompanyReview.position == department_clause)

    if employment_duration_clause is not None:
        base_query = _apply_employment_duration_filter(base_query, employment_duration_clause)

    if employment_status_clause is not None:
        base_query = base_query.filter(func.lower(CompanyReview.employment_status) == employment_status_clause)

    total_reviews = base_query.count()
    total_all_reviews = db.query(CompanyReview).filter(CompanyReview.company_id == company_id).count()
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
            "total_reviews": total_all_reviews,
            "rating_breakdown": rating_breakdown,
        },
        "reviews": reviews,
    }

def get_company_rating_summary(db: Session, company_id: str) -> CompanyRatingSummaryResponse:
    company = get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Company not found"
        )
    
    avg_rating = db.query(func.avg(CompanyReview.rating)).filter(CompanyReview.company_id == company_id).scalar()
    average_rating = float(avg_rating) if avg_rating is not None else 0.0
    total_reviews = db.query(CompanyReview).filter(CompanyReview.company_id == company_id).count()
    
    return CompanyRatingSummaryResponse(
        rating=average_rating,
        total_reviews=total_reviews,
    )