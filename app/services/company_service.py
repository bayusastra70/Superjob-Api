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


async def get_company_by_id(db: AsyncSession, company_id: int) -> Company:
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
    company_id: int,
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

async def get_company_rating_summary(db: AsyncSession, company_id: int) -> CompanyRatingSummaryResponse:
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
    Using sync psycopg2 connection to avoid SSL issues on Render.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify company exists
        cursor.execute("SELECT id FROM companies WHERE id = %s", (company_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        # Check if current user belongs to this company
        cursor.execute("""
            SELECT 1 FROM users_companies 
            WHERE user_id = %s AND company_id = %s
        """, (current_user_id, company_id))
        if not cursor.fetchone():
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
        where_conditions = ["uc.company_id = %s"]
        params = [company_id]
        
        if search:
            where_conditions.append("(u.email ILIKE %s OR u.username ILIKE %s OR u.full_name ILIKE %s)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        
        if role_id is not None:
            where_conditions.append("u.default_role_id = %s")
            params.append(role_id)
        
        if is_active is not None:
            where_conditions.append("u.is_active = %s")
            params.append(is_active)
        
        where_clause = " AND ".join(where_conditions)
        
        # Count query
        count_query = f"""
            SELECT COUNT(*)
            FROM users u
            INNER JOIN users_companies uc ON u.id = uc.user_id
            WHERE {where_clause}
        """
        cursor.execute(count_query, params)
        total_count_result = cursor.fetchone()
        
        # Handle RealDictCursor or tuple
        if hasattr(total_count_result, 'keys'):
            total_count = total_count_result['count'] if 'count' in total_count_result else list(total_count_result.values())[0]
        else:
            total_count = total_count_result[0]
        
        # Data query
        data_params = params + [limit, offset]
        data_query = f"""
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
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, data_params)
        users = cursor.fetchall()
        
        # Format results
        users_list = []
        for user in users:
            if hasattr(user, 'keys'):
                users_list.append({
                    "id": user.get("id"),
                    "full_name": user.get("full_name"),
                    "phone": user.get("phone"),
                    "email": user.get("email"),
                    "default_role_id": user.get("default_role_id"),
                    "role_name": user.get("role_name")
                })
            else:
                users_list.append({
                    "id": user[0],
                    "full_name": user[1],
                    "phone": user[2],
                    "email": user[3],
                    "default_role_id": user[4],
                    "role_name": user[5]
                })
        
        # Calculate total pages
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        
        return {
            "code": 200,
            "is_success": True,
            "message": "Success",
            "data": {
                "items": users_list,
                "page": page,
                "total": total_count,
                "limit": limit
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_company_users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve company users: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


async def create_company_user(
    company_id: int,
    user_data: CreateCompanyUser,
    current_user_id: int,
) -> CompanyUserResponse:
    """
    Add a new user to a company.
    Using sync psycopg2 connection to avoid SSL issues on Render.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        conn.autocommit = False # Use transaction
        cursor = conn.cursor()
        
        # 1. Verify company exists
        cursor.execute("SELECT id FROM companies WHERE id = %s", (company_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )

        # 2. Authorization Check
        # Check strict company membership first
        cursor.execute("""
            SELECT 1 
            FROM users_companies 
            WHERE user_id = %s AND company_id = %s
        """, (current_user_id, company_id))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to manage users for this company"
            )

        # 3. RBAC Permission Check
        cursor.execute("SELECT is_superuser FROM users WHERE id = %s", (current_user_id,))
        user_status = cursor.fetchone()
        
        is_superuser = False
        if user_status:
            is_superuser = user_status['is_superuser'] if hasattr(user_status, 'keys') else user_status[0]
        
        if not is_superuser:
            permission_query = """
                WITH user_all_roles AS (
                    SELECT role_id FROM user_roles WHERE user_id = %s
                    UNION
                    SELECT default_role_id FROM users WHERE id = %s AND default_role_id IS NOT NULL
                )
                SELECT 1 
                FROM user_all_roles uar
                JOIN role_permissions rp ON uar.role_id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE p.code = 'user.create'
            """
            cursor.execute(permission_query, (current_user_id, current_user_id))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied. Required: 'user.create'"
                )

        # 4. Request Validation
        cursor.execute("SELECT name FROM roles WHERE id = %s", (user_data.role_id,))
        role_result = cursor.fetchone()
        if not role_result:
            raise HTTPException(status_code=400, detail=f"Role ID {user_data.role_id} not found")
        
        new_user_role_name = role_result['name'] if hasattr(role_result, 'keys') else role_result[0]

        # Check if email/username/phone already exists globally
        cursor.execute("""
            SELECT 1 FROM users 
            WHERE email = %s OR username = %s OR phone = %s
        """, (user_data.email, user_data.username, user_data.phone))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email, username, or phone already exists"
            )

        # 5. Create User and Link to Company
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        internal_role_name = new_user_role_name if new_user_role_name in ['admin', 'employer', 'candidate'] else 'candidate'

        # Insert User
        cursor.execute("""
            INSERT INTO users (email, full_name, username, phone, password_hash, default_role_id, role, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, true, NOW(), NOW())
            RETURNING id, email, full_name, phone, default_role_id
        """, (
            user_data.email, user_data.full_name, user_data.username, user_data.phone, 
            hashed_password, user_data.role_id, internal_role_name
        ))
        
        user_row = cursor.fetchone()
        new_user_id = user_row['id'] if hasattr(user_row, 'keys') else user_row[0]
        
        # Link to Company
        cursor.execute("""
            INSERT INTO users_companies (user_id, company_id)
            VALUES (%s, %s)
        """, (new_user_id, company_id))
        
        conn.commit()
        
        # Format response
        if hasattr(user_row, 'keys'):
            return CompanyUserResponse(
                id=new_user_id,
                email=user_row.get('email'),
                full_name=user_row.get('full_name'),
                phone=user_row.get('phone'),
                default_role_id=user_row.get('default_role_id'),
                role_name=new_user_role_name
            )
        else:
            return CompanyUserResponse(
                id=new_user_id,
                email=user_row[1],
                full_name=user_row[2],
                phone=user_row[3],
                default_role_id=user_row[4],
                role_name=new_user_role_name
            )
            
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error creating company user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create user: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.autocommit = True
            conn.close()