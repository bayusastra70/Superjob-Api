import logging
from typing import Any, Dict
from fastapi import HTTPException, status
from sqlalchemy import Float, case, cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.company_review import CompanyReview
from app.schemas.company_review_schema import CompanyRatingSummaryResponse
from app.schemas.company_schema import CreateCompanyUser, CompanyUserResponse
from app.services.database import get_db_connection
from app.services.auth import get_password_hash


logger = logging.getLogger(__name__)


async def get_company_by_id(db: AsyncSession, company_id: str) -> Company:
    company = await db.execute(select(Company).filter(Company.id == company_id))
    return company.scalar_one_or_none()

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
        return query.where(duration_years < 1)  # < 1 year
    if duration_filter == "1-2":
        return query.where(duration_years >= 1, duration_years < 3)  # 1-2 yrs
    if duration_filter == "3-5":
        return query.where(duration_years >= 3, duration_years < 5)  # 3-5 yrs
    if duration_filter == "5-10":
        return query.where(duration_years >= 5, duration_years < 10)  # 5-10 yrs
    if duration_filter == "5+":
        return query.where(duration_years >= 10)  # 10+ yrs

    return query


async def get_company_reviews_by_company_id(
    db: AsyncSession,
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

    company = await get_company_by_id(db, company_id)
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

    base_query = select(CompanyReview).where(CompanyReview.company_id == company_id)

    if department_clause is not None:
        base_query = base_query.where(CompanyReview.position == department_clause)

    if employment_duration_clause is not None:
        base_query = _apply_employment_duration_filter(base_query, employment_duration_clause)

    if employment_status_clause is not None:
        base_query = base_query.where(func.lower(CompanyReview.employment_status) == employment_status_clause)

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total_reviews = (await db.execute(count_stmt)).scalar_one()

    total_all_stmt = select(func.count()).select_from(CompanyReview).where(CompanyReview.company_id == company_id)
    total_all_reviews = (await db.execute(total_all_stmt)).scalar_one()
    total_pages = (total_reviews + limit - 1) // limit if total_reviews > 0 else 0

    avg_rating_stmt = select(func.avg(CompanyReview.rating)).where(CompanyReview.company_id == company_id)
    avg_rating = (await db.execute(avg_rating_stmt)).scalar_one()
    average_rating = float(avg_rating) if avg_rating is not None else 0.0

    breakdown_stmt = (
        select(CompanyReview.rating, func.count(CompanyReview.id))
        .where(CompanyReview.company_id == company_id)
        .group_by(CompanyReview.rating)
    )
    breakdown_rows = (await db.execute(breakdown_stmt)).all()

    rating_breakdown: Dict[str, int] = {str(i): 0 for i in range(5, 0, -1)}
    rating_breakdown.update({str(rating): count for rating, count in breakdown_rows})

    reviews_stmt = base_query.order_by(order_clause).offset(offset).limit(limit)
    reviews_result = await db.execute(reviews_stmt)
    reviews = reviews_result.scalars().all()

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

async def get_company_rating_summary(db: AsyncSession, company_id: str) -> CompanyRatingSummaryResponse:
    company = await get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Company not found"
        )
    
    avg_rating_stmt = select(func.avg(CompanyReview.rating)).where(CompanyReview.company_id == company_id)
    avg_rating = (await db.execute(avg_rating_stmt)).scalar_one()
    average_rating = float(avg_rating) if avg_rating is not None else 0.0

    total_reviews_stmt = select(func.count()).select_from(CompanyReview).where(CompanyReview.company_id == company_id)
    total_reviews = (await db.execute(total_reviews_stmt)).scalar_one()
    
    return CompanyRatingSummaryResponse(
        rating=average_rating,
        total_reviews=total_reviews,
    )


async def get_company_users(
    db: AsyncSession,
    company_id: int,
    current_user_id: int,
    page: int = 1,
    limit: int = 10,
    search: str = None,
    role_id: int = None,
    is_active: bool = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    """
    Get all users associated with a company with pagination and filtering.
    
    Args:
        db: Database session
        company_id: ID of the company
        current_user_id: ID of the current authenticated user
        page: Page number
        limit: Items per page
        search: Search query for email, username, or full_name
        role_id: Filter by role ID (default_role_id)
        is_active: Filter by active status
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
    
    Returns:
        Dict with success, data, pagination, and filters
    
    Raises:
        HTTPException: 403 if user not authorized, 404 if company not found
    """
    
    # Verify company exists using text query to avoid model loading
    company_check = text("SELECT id FROM companies WHERE id = :company_id")
    company_result = await db.execute(company_check, {"company_id": company_id})
    if not company_result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check if current user belongs to this company
    user_company_check = text("""
        SELECT 1 FROM users_companies 
        WHERE user_id = :user_id AND company_id = :company_id
    """)
    user_company_result = await db.execute(user_company_check, {
        "user_id": current_user_id,
        "company_id": company_id
    })
    if not user_company_result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view users from this company"
        )
    
    # Validate sort order
    if sort_order.lower() not in ["asc", "desc"]:
        sort_order = "desc"
    
    # Validate sort field
    valid_sort_fields = ["id", "email", "username", "full_name", "phone", "role", "is_active", "created_at", "updated_at", "default_role_id"]
    if sort_by not in valid_sort_fields:
        sort_by = "created_at"
    
    # Calculate offset
    offset = (page - 1) * limit
    
    # Build WHERE clause
    where_conditions = ["uc.company_id = :company_id"]
    params = {"company_id": company_id, "limit": limit, "offset": offset}
    
    if search:
        where_conditions.append("(u.email ILIKE :search OR u.username ILIKE :search OR u.full_name ILIKE :search)")
        params["search"] = f"%{search}%"
    
    if role_id is not None:
        where_conditions.append("u.default_role_id = :role_id")
        params["role_id"] = role_id
    
    if is_active is not None:
        where_conditions.append("u.is_active = :is_active")
        params["is_active"] = is_active
    
    where_clause = " AND ".join(where_conditions)
    
    # Count query
    count_query = text(f"""
        SELECT COUNT(*) as total
        FROM users u
        INNER JOIN users_companies uc ON u.id = uc.user_id
        WHERE {where_clause}
    """)
    
    count_result = await db.execute(count_query, params)
    total_count = count_result.scalar()
    
    # Data query
    data_query = text(f"""
        SELECT 
            u.id,
            u.full_name,
            u.phone,
            u.email,
            u.default_role_id,
            r.name as role_name
        FROM users u
        INNER JOIN users_companies uc ON u.id = uc.user_id
        LEFT JOIN roles r ON u.default_role_id = r.id
        WHERE {where_clause}
        ORDER BY u.{sort_by} {sort_order.upper()}
        LIMIT :limit OFFSET :offset
    """)
    
    result = await db.execute(data_query, params)
    users = result.fetchall()
    
    # Format results
    users_list = [
        {
            "id": user.id,
            "full_name": user.full_name,
            "phone": user.phone,
            "email": user.email,
            "default_role_id": user.default_role_id,
            "role_name": user.role_name
        }
        for user in users
    ]
    
    # Calculate total pages
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
    
    return {
        "success": True,
        "data": users_list,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "filters": {
            "search": search,
            "role_id": role_id,
            "is_active": is_active,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
    }


async def create_company_user(
    db: AsyncSession,
    company_id: int,
    user_data: CreateCompanyUser,
    current_user_id: int,
) -> CompanyUserResponse:
    """
    Add a new user to a company.
    
    Authorization:
    - Current user must belong to the company
    - Current user must have 'admin' or 'employer' role
    """
    
    # 1. Verify company exists
    company_check = text("SELECT id FROM companies WHERE id = :company_id")
    if not (await db.execute(company_check, {"company_id": company_id})).fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # 2. Authorization Check
    # Check if current user belongs to company AND (is superuser OR has permission)
    # 1. Check strict company membership first
    membership_check = text("""
        SELECT 1 
        FROM users_companies 
        WHERE user_id = :user_id AND company_id = :company_id
    """)
    if not (await db.execute(membership_check, {
        "user_id": current_user_id,
        "company_id": company_id
    })).fetchone():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to manage users for this company"
        )

    # 2. RBAC Permission Check
    # Check is_superuser OR has permission 'company.user.create'
    user_status = (await db.execute(
        text("SELECT is_superuser FROM users WHERE id = :uid"), 
        {"uid": current_user_id}
    )).fetchone()
    
    is_superuser = user_status[0] if user_status else False
    
    if not is_superuser:
        permission_check = text("""
            WITH user_all_roles AS (
                SELECT role_id FROM user_roles WHERE user_id = :uid
                UNION
                SELECT default_role_id FROM users WHERE id = :uid AND default_role_id IS NOT NULL
            )
            SELECT 1 
            FROM user_all_roles uar
            JOIN role_permissions rp ON uar.role_id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE p.code = 'user.create'
        """)
        has_permission = (await db.execute(permission_check, {"uid": current_user_id})).fetchone()
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied. Required: 'user.create'"
            )

    # 3. Request Validation
    # Check if role_id exists
    role_check = text("SELECT name FROM roles WHERE id = :role_id")
    role_result = (await db.execute(role_check, {"role_id": user_data.role_id})).fetchone()
    if not role_result:
        raise HTTPException(status_code=400, detail=f"Role ID {user_data.role_id} not found")
    
    new_user_role_name = role_result[0]

    # Check if email/username/phone already exists globally
    duplicate_check = text("""
        SELECT 1 FROM users 
        WHERE email = :email OR username = :username OR phone = :phone
    """)
    if (await db.execute(duplicate_check, {
        "email": user_data.email,
        "username": user_data.username,
        "phone": user_data.phone
    })).fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email, username, or phone already exists"
        )

    # 4. Create User and Link to Company
    try:
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Determine internal role name for the 'role' column (enum-like string)
        # We rely on the role_id for permission, but 'role' column is legacy/string?
        # app/services/auth.py update_user_simple uses ['admin', 'employer', 'candidate']
        # We map role_id to this string if possible, or just default to 'employer' or 'candidate'
        # Let's use the role name from the DB query above
        internal_role_name = new_user_role_name if new_user_role_name in ['admin', 'employer', 'candidate'] else 'candidate'

        # Insert User
        # Note: 'role' column is separate from 'default_role_id'
        insert_user = text("""
            INSERT INTO users (email, full_name, username, phone, password_hash, default_role_id, role, is_active, created_at, updated_at)
            VALUES (:email, :full_name, :username, :phone, :password_hash, :role_id, :role_name, true, NOW(), NOW())
            RETURNING id, email, full_name, phone, default_role_id
        """)
        
        user_result = (await db.execute(insert_user, {
            "email": user_data.email,
            "full_name": user_data.full_name,
            "username": user_data.username,
            "phone": user_data.phone,
            "password_hash": hashed_password,
            "role_id": user_data.role_id,
            "role_name": internal_role_name 
        })).fetchone()
        
        new_user_id = user_result[0]
        
        # Link to Company
        insert_link = text("""
            INSERT INTO users_companies (user_id, company_id)
            VALUES (:user_id, :company_id)
        """)
        await db.execute(insert_link, {"user_id": new_user_id, "company_id": company_id})
        
        await db.commit()
        
        return CompanyUserResponse(
            id=new_user_id,
            email=user_result.email,
            full_name=user_result.full_name,
            phone=user_result.phone,
            default_role_id=user_result.default_role_id,
            role_name=new_user_role_name
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating company user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user"
        )