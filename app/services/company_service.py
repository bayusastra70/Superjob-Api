from loguru import logger
from typing import Any, Dict
from fastapi import HTTPException, status
from sqlalchemy import Float, case, cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.company_review import CompanyReview
from app.schemas.company_review_schema import CompanyRatingSummaryResponse
from app.schemas.company_schema import (
    UpdateCompanyUser,
    CreateCompanyUser,
    CompanyUserResponse,
)
from app.services.database import get_db_connection
from app.services.auth import get_password_hash
from app.utils.solvera_storage import solvera_storage, StorageFolder, UploaderName
from app.services.role_base_access_control_service import RoleBaseAccessControlService


def get_company_by_id(company_id: int) -> dict:
    """Get company by ID with admin users (role_id 1) and attachments mapped"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch company with its direct email/phone and attachments
        query = """
            SELECT c.*, ca.nib_url, ca.npwp_url, ca.proposal_url, ca.portfolio_url
            FROM companies c
            LEFT JOIN company_attachments ca ON c.id = ca.company_id
            WHERE c.id = %s
            LIMIT 1
        """
        cursor.execute(query, (company_id,))
        company = cursor.fetchone()

        if company:
            # Format documents array (always return all 4 types)
            documents = []
            doc_types = ["nib", "npwp", "proposal", "portfolio"]
            for dtype in doc_types:
                url_key = f"{dtype}_url"
                documents.append({"id": dtype, "url": company.get(url_key) or ""})
            company["documents"] = documents

            # Format social media array (always return all 6 types)
            social_media = []
            social_types = [
                "linkedin",
                "twitter",
                "instagram",
                "facebook",
                "tiktok",
                "youtube",
            ]
            for stype in social_types:
                url_key = f"{stype}_url"
                social_media.append({"id": stype, "url": company.get(url_key) or ""})
            company["social_media"] = social_media

        return company
    finally:
        if cursor:
            cursor.close()


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


async def update_company_profile(
    company_id: int,
    updates: dict = None,
    logo: Any = None,
    banner: Any = None,
    nib_document: Any = None,
    npwp_document: Any = None,
    proposal_document: Any = None,
    portfolio_document: Any = None,
    current_user_id: int = None,
) -> Dict[str, Any]:
    """
    Update company profile with full business logic.
    - Handles text field updates (including social links in companies table)
    - Synchronizes phone/email to users table
    - Handles multi-file uploads/deletions for NIB, NPWP, Proposal, Portfolio
    - Performs sync DB updates across 3 tables (companies, users, company_attachments)
    """
    # 1. Get current company state
    company = get_company_by_id(company_id)
    if not company:
        return None

    final_updates = {}
    actual_changed_fields = []

    # 2. Process updates
    if updates:
        company_fields = [
            "name",
            "industry",
            "description",
            "website",
            "location",
            "founded_year",
            "employee_size",
            "linkedin_url",
            "twitter_url",
            "instagram_url",
            "facebook_url",
            "tiktok_url",
            "youtube_url",
            "phone",
            "email",
        ]

        for key, value in updates.items():
            if value is not None:
                if key in company_fields:
                    old_value = company.get(key)
                    if old_value != value:
                        # Uniqueness check for company name
                        if key == "name":
                            conn_n = None
                            cursor_n = None
                            try:
                                conn_n = get_db_connection()
                                cursor_n = conn_n.cursor()
                                cursor_n.execute(
                                    "SELECT id FROM companies WHERE name = %s AND id != %s LIMIT 1",
                                    (value, company_id),
                                )
                                if cursor_n.fetchone():
                                    raise HTTPException(
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Nama perusahaan sudah digunakan",
                                    )
                            finally:
                                if cursor_n:
                                    cursor_n.close()
                                if conn_n:
                                    conn_n.close()

                        final_updates[key] = value
                        actual_changed_fields.append(key)

    # 3. Handle Logo Upload
    logo_to_upload = None
    if logo and hasattr(logo, "filename") and logo.filename:
        logo_to_upload = logo

    # 3.5 Handle Banner Upload
    banner_to_upload = None
    if banner and hasattr(banner, "filename") and banner.filename:
        banner_to_upload = banner

    # 4. Handle Document Uploads (Consolidated table)
    attachment_updates = {}
    docs_to_upload = {
        "nib": nib_document,
        "npwp": npwp_document,
        "proposal": proposal_document,
        "portfolio": portfolio_document,
    }

    # Atomic Validation: Check ALL files before any upload starts

    # Atomic Validation: Check ALL files before any upload starts

    # A. Validate logo (if provided)
    if logo_to_upload:
        # 1. Read first few bytes to check signature
        header = await logo_to_upload.read(8)
        await logo_to_upload.seek(0)

        is_image = (
            header.startswith(b"\xff\xd8")  # JPEG
            or header.startswith(b"\x89PNG\r\n\x1a\n")  # PNG
            or (header.startswith(b"RIFF") and b"WEBP" in header)  # WebP
        )

        if not is_image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Logo must be a valid image file (JPEG, PNG, or WEBP).",
            )

        # 2. Check Content Type (additional check)
        if logo_to_upload.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Logo content type must be an image. Got: {logo_to_upload.content_type}",
            )

        logo_to_upload.file.seek(0, 2)
        logo_size = logo_to_upload.file.tell()
        logo_to_upload.file.seek(0)

        if logo_size > 2 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Logo exceeds 2MB limit (Size: {logo_size / (1024 * 1024):.2f}MB)",
            )

    # A-2. Validate banner (if provided)
    if banner_to_upload:
        # 1. Read first few bytes to check signature
        header = await banner_to_upload.read(8)
        await banner_to_upload.seek(0)

        is_image = (
            header.startswith(b"\xff\xd8")  # JPEG
            or header.startswith(b"\x89PNG\r\n\x1a\n")  # PNG
            or (header.startswith(b"RIFF") and b"WEBP" in header)  # WebP
        )

        if not is_image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Banner must be a valid image file (JPEG, PNG, or WEBP).",
            )

        # 2. Check Content Type (additional check)
        if banner_to_upload.content_type not in [
            "image/jpeg",
            "image/png",
            "image/webp",
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Banner content type must be an image. Got: {banner_to_upload.content_type}",
            )

        banner_to_upload.file.seek(0, 2)
        banner_size = banner_to_upload.file.tell()
        banner_to_upload.file.seek(0)

        if banner_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Banner exceeds 10MB limit (Size: {banner_size / (1024 * 1024):.2f}MB)",
            )

    # B. Validate documents (if provided)
    for doc_id, file_obj in docs_to_upload.items():
        if file_obj and hasattr(file_obj, "filename") and file_obj.filename:
            logger.info(
                f"Validating document {doc_id}: filename={file_obj.filename}, content_type={file_obj.content_type}"
            )

            # 1. Read first few bytes to check PDF signature
            header = await file_obj.read(5)
            await file_obj.seek(0)

            if not header.startswith(b"%PDF-"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Document '{doc_id}' is not a valid PDF file (Signature mismatch).",
                )

            # 2. Check Content Type
            if file_obj.content_type != "application/pdf":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Document '{doc_id}' must be a PDF file metadata. Got: {file_obj.content_type}",
                )

            file_obj.file.seek(0, 2)
            file_size = file_obj.file.tell()
            file_obj.file.seek(0)

            if file_size > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Document '{doc_id}' exceeds 10MB limit (Size: {file_size / (1024 * 1024):.2f}MB)",
                )

    # C. Upload Logo
    if logo_to_upload:
        logger.info(f"Processing logo upload for company {company_id}")
        logo_result = await solvera_storage.upload_file(
            file=logo_to_upload,
            folder=StorageFolder.COMPANY_LOGO,
            allowed_types=["image/jpeg", "image/png", "image/webp"],
            max_size_mb=2,
            uploader_name=UploaderName.SUPERJOB_SERVICE,
        )

        # Delete old logo if exists
        if company.get("logo_storage_id"):
            await solvera_storage.delete_file(company["logo_storage_id"])

        final_updates["logo_url"] = logo_result["url"]
        final_updates["logo_storage_id"] = logo_result["id"]
        actual_changed_fields.append("logo")

    # C-2. Upload Banner
    if banner_to_upload:
        logger.info(f"Processing banner upload for company {company_id}")
        banner_result = await solvera_storage.upload_file(
            file=banner_to_upload,
            folder=StorageFolder.COMPANY_BANNER,
            allowed_types=["image/jpeg", "image/png", "image/webp"],
            max_size_mb=10,
            uploader_name=UploaderName.SUPERJOB_SERVICE,
        )

        # Delete old banner if exists
        if company.get("banner_storage_id"):
            await solvera_storage.delete_file(company["banner_storage_id"])

        final_updates["banner_url"] = banner_result["url"]
        final_updates["banner_storage_id"] = banner_result["id"]
        actual_changed_fields.append("banner")

    # Fetch current attachments for deletion logic
    current_attachments = {}
    conn_a = None
    cursor_a = None
    try:
        conn_a = get_db_connection()
        cursor_a = conn_a.cursor()
        cursor_a.execute(
            "SELECT * FROM company_attachments WHERE company_id = %s", (company_id,)
        )
        current_attachments = cursor_a.fetchone() or {}
    finally:
        if cursor_a:
            cursor_a.close()
        if conn_a:
            conn_a.close()

    for doc_id, file_obj in docs_to_upload.items():
        if file_obj and hasattr(file_obj, "filename") and file_obj.filename:
            # Upload to Solvera Storage
            # Note: solv_storage.upload_file also does internal validation,
            # but we pre-validate above to ensure atomicity.
            upload_result = await solvera_storage.upload_file(
                file=file_obj,
                folder=StorageFolder.COMPANY_DOCUMENT,
                allowed_types=["application/pdf"],
                max_size_mb=10,
                uploader_name=UploaderName.SUPERJOB_SERVICE,
            )

            # Delete old version if exists
            old_storage_id = current_attachments.get(f"{doc_id}_storage_id")
            if old_storage_id:
                await solvera_storage.delete_file(old_storage_id)

            attachment_updates[f"{doc_id}_url"] = upload_result["url"]
            attachment_updates[f"{doc_id}_storage_id"] = upload_result["id"]
            actual_changed_fields.append(doc_id)

    # 5. Apply DB Updates if any
    if final_updates or attachment_updates:
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            conn.autocommit = False  # Use transaction
            cursor = conn.cursor()

            # A. Update Companies Table
            if final_updates:
                fields = []
                params = []
                for key, value in final_updates.items():
                    fields.append(f"{key} = %s")
                    params.append(value)

                params.append(company_id)
                set_clause = ", ".join(fields)
                query = f"UPDATE companies SET {set_clause} WHERE id = %s RETURNING *"
                cursor.execute(query, params)
                updated_company = cursor.fetchone()
            else:
                updated_company = company

            # C. Update Company Attachments (UPSERT)
            if attachment_updates:
                logger.info(f"Updating attachments for company {company_id}")
                att_fields = ["company_id"]
                att_params = [company_id]
                for key, value in attachment_updates.items():
                    att_fields.append(key)
                    att_params.append(value)

                placeholders = ", ".join(["%s"] * len(att_fields))
                update_items = ", ".join(
                    [f"{k} = EXCLUDED.{k}" for k in attachment_updates.keys()]
                )

                att_query = f"""
                    INSERT INTO company_attachments ({", ".join(att_fields)})
                    VALUES ({placeholders})
                    ON CONFLICT (company_id) DO UPDATE SET {update_items}
                """
                cursor.execute(att_query, att_params)

            conn.commit()

            # Attach changed fields for activity logging
            updated_company["_changed_fields"] = actual_changed_fields

            # Final fetch to ensure documents array is up to date (or manually construct it)
            # Re-fetch the full object using the new logic
            return get_company_by_id(company_id)
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error updating company/user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )
        finally:
            if cursor:
                cursor.close()

    # Return original if no changes
    company["_changed_fields"] = []
    return company


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

    company = get_company_by_id(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
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
        base_query = _apply_employment_duration_filter(
            base_query, employment_duration_clause
        )

    if employment_status_clause is not None:
        base_query = base_query.where(
            func.lower(CompanyReview.employment_status) == employment_status_clause
        )

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total_reviews = (await db.execute(count_stmt)).scalar_one()

    total_all_stmt = (
        select(func.count())
        .select_from(CompanyReview)
        .where(CompanyReview.company_id == company_id)
    )
    total_all_reviews = (await db.execute(total_all_stmt)).scalar_one()
    total_pages = (total_reviews + limit - 1) // limit if total_reviews > 0 else 0

    avg_rating_stmt = select(func.avg(CompanyReview.rating)).where(
        CompanyReview.company_id == company_id
    )
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
        "pagination": {"page": page, "limit": limit, "total_pages": total_pages},
        "summary": {
            "average_rating": average_rating,
            "total_reviews": total_all_reviews,
            "rating_breakdown": rating_breakdown,
        },
        "reviews": reviews,
    }


async def get_company_rating_summary(
    db: AsyncSession, company_id: int
) -> CompanyRatingSummaryResponse:
    company = get_company_by_id(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )

    avg_rating_stmt = select(func.avg(CompanyReview.rating)).where(
        CompanyReview.company_id == company_id
    )
    avg_rating = (await db.execute(avg_rating_stmt)).scalar_one()
    average_rating = float(avg_rating) if avg_rating is not None else 0.0

    total_reviews_stmt = (
        select(func.count())
        .select_from(CompanyReview)
        .where(CompanyReview.company_id == company_id)
    )
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
                status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
            )

        # Check if current user belongs to this company
        cursor.execute(
            """
            SELECT 1 FROM users_companies
            WHERE user_id = %s AND company_id = %s
        """,
            (current_user_id, company_id),
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view users from this company",
            )

        # Validate sort order
        if sort_order.lower() not in ["asc", "desc"]:
            sort_order = "desc"

        # Validate sort field
        valid_sort_fields = [
            "id",
            "email",
            "username",
            "full_name",
            "phone",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        ]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"

        # Calculate offset
        offset = (page - 1) * limit

        # Build WHERE clause
        where_conditions = ["uc.company_id = %s"]
        params = [company_id]

        if search:
            where_conditions.append(
                "(u.email ILIKE %s OR u.username ILIKE %s OR u.full_name ILIKE %s)"
            )
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        if role_id is not None:
            where_conditions.append(
                "EXISTS (SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id AND ur.role_id = %s AND ur.is_active = true)"
            )
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
        if hasattr(total_count_result, "keys"):
            total_count = (
                total_count_result["count"]
                if "count" in total_count_result
                else list(total_count_result.values())[0]
            )
        else:
            total_count = total_count_result[0]

        # Data query
        data_params = params + [limit, offset]
        data_query = f"""
            SELECT
                u.id,
                u.email,
                u.username,
                u.full_name,
                u.phone,
                COALESCE(
                    (SELECT r.name
                    FROM user_roles ur
                    JOIN roles r ON ur.role_id = r.id
                    WHERE ur.user_id = u.id
                    AND ur.is_active = true
                    ORDER BY ur.assigned_at DESC
                    LIMIT 1),
                    'candidate'
                ) as role,
                COALESCE(
                    (SELECT ur.role_id
                    FROM user_roles ur
                    WHERE ur.user_id = u.id
                    AND ur.is_active = true
                    ORDER BY ur.assigned_at DESC
                    LIMIT 1),
                    3
                ) as default_role_id,
                u.is_active,
                u.is_superuser,
                u.linkedin_url,
                u.created_at,
                u.updated_at
            FROM users u
            INNER JOIN users_companies uc ON u.id = uc.user_id
            WHERE {where_clause}
            ORDER BY u.{sort_by} {sort_order.upper()}
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, data_params)
        users = cursor.fetchall()

        # Format results
        users_list = []
        for user in users:
            is_dict = hasattr(user, "keys")
            users_list.append(
                {
                    "id": user.get("id") if is_dict else user[0],
                    "email": user.get("email") if is_dict else user[1],
                    "username": user.get("username") if is_dict else user[2],
                    "full_name": user.get("full_name") if is_dict else user[3],
                    "phone": user.get("phone") if is_dict else user[4],
                    "role": user.get("role") if is_dict else user[5],
                    "default_role_id": user.get("default_role_id")
                    if is_dict
                    else user[6],
                    "is_active": user.get("is_active") if is_dict else user[7],
                    "is_superuser": user.get("is_superuser") if is_dict else user[8],
                    "linkedin_url": user.get("linkedin_url") if is_dict else user[9],
                    "created_at": user.get("created_at") if is_dict else user[10],
                    "updated_at": user.get("updated_at") if is_dict else user[11],
                }
            )

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
                "limit": limit,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_company_users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        if cursor:
            cursor.close()


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
        conn.autocommit = False  # Use transaction
        cursor = conn.cursor()

        # 1. Verify company exists
        cursor.execute("SELECT id FROM companies WHERE id = %s", (company_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
            )

        # 2. Authorization Check
        # Check strict company membership first
        cursor.execute(
            """
            SELECT 1
            FROM users_companies
            WHERE user_id = %s AND company_id = %s
        """,
            (current_user_id, company_id),
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to manage users for this company",
            )

        # 3. RBAC Permission Check
        cursor.execute(
            "SELECT is_superuser FROM users WHERE id = %s", (current_user_id,)
        )
        user_status = cursor.fetchone()

        is_superuser = False
        if user_status:
            is_superuser = (
                user_status["is_superuser"]
                if hasattr(user_status, "keys")
                else user_status[0]
            )

        if not is_superuser:
            # RBAC checks moved to router to avoid connection closure mid-transaction
            pass

        # 4. Request Validation
        if user_data.role_id == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign Admin role (ID 1) via this endpoint. Only one admin allowed per company.",
            )

        cursor.execute("SELECT name FROM roles WHERE id = %s", (user_data.role_id,))
        role_result = cursor.fetchone()
        if not role_result:
            raise HTTPException(
                status_code=400, detail=f"Role ID {user_data.role_id} not found"
            )

        new_user_role_name = (
            role_result["name"] if hasattr(role_result, "keys") else role_result[0]
        )

        # Check if email/username/phone already exists globally
        cursor.execute(
            """
            SELECT 1 FROM users
            WHERE email = %s OR username = %s
        """,
            (user_data.email, user_data.username),
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists",
            )

        # 5. Create User and Link to Company
        # Hash password
        hashed_password = get_password_hash(user_data.password)

        # Map granular role to base role ('admin', 'employer', 'candidate')
        # This keeps the 'users.role' column valid for the DB ENUM/system logic.
        if new_user_role_name == "admin":
            base_role = "admin"
        elif new_user_role_name == "candidate":
            base_role = "candidate"
        else:
            # All other roles (employer, hr_manager, recruiter, etc.) are under 'employer'
            base_role = "employer"

        internal_role_name = base_role

        # Insert User and return with role name
        cursor.execute(
            """
            INSERT INTO users (email, full_name, username, phone, password_hash, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, true, NOW(), NOW())
            RETURNING id, email, username, full_name, phone, is_active, is_superuser, created_at, updated_at
        """,
            (
                user_data.email,
                user_data.full_name,
                user_data.username,
                user_data.phone,
                hashed_password,
            ),
        )

        user_row = cursor.fetchone()
        new_user_id = user_row.get("id") if hasattr(user_row, "keys") else user_row[0]

        # 5. Assign role using RBAC system
        cursor.execute(
            """
            INSERT INTO user_roles (user_id, role_id, assigned_at, is_active)
            VALUES (%s, %s, CURRENT_TIMESTAMP, true)
        """,
            (new_user_id, user_data.role_id),
        )

        # 6. Link user to company
        cursor.execute(
            """
            INSERT INTO users_companies (user_id, company_id)
            VALUES (%s, %s)
        """,
            (new_user_id, company_id),
        )

        # 7. Get role name for response
        cursor.execute("SELECT name FROM roles WHERE id = %s", (user_data.role_id,))
        role_name = cursor.fetchone()
        role_name = (
            role_name.get("name") if hasattr(role_name, "keys") else role_name[0]
        )

        conn.commit()

        # Return formatted user data
        is_dict = hasattr(user_row, "keys")
        return CompanyUserResponse(
            id=user_row.get("id") if is_dict else user_row[0],
            email=user_row.get("email") if is_dict else user_row[1],
            username=user_row.get("username") if is_dict else user_row[2],
            full_name=user_row.get("full_name") if is_dict else user_row[3],
            phone=user_row.get("phone") if is_dict else user_row[4],
            role=role_name,
            default_role_id=user_data.role_id,
            is_active=user_row.get("is_active") if is_dict else user_row[5],
            is_superuser=user_row.get("is_superuser") if is_dict else user_row[6],
            created_at=user_row.get("created_at") if is_dict else user_row[7],
            updated_at=user_row.get("updated_at") if is_dict else user_row[8],
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
            detail="Internal server error",
        )
    finally:
        if cursor:
            cursor.close()


async def update_company_user(
    company_id: int,
    user_id: int,
    user_data: UpdateCompanyUser,
    current_user_id: int,
    is_self_edit: bool = False,
) -> Dict[str, Any]:
    """
    Update an existing user in a company.

    Args:
        company_id: ID of the company
        user_id: ID of the user to update
        user_data: Update data
        current_user_id: ID of the user performing the update
        is_self_edit: True if user is editing their own profile
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor()

        # 1. Verify company exists (only for admin edits)
        if not is_self_edit:
            cursor.execute("SELECT id FROM companies WHERE id = %s", (company_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
                )

        # 2. Authorization Check:
        # - Self-edit: Being owner of profile is enough
        # - Admin edit: Current user must belong to the company
        if not is_self_edit:
            cursor.execute(
                """
                SELECT 1 FROM users_companies
                WHERE user_id = %s AND company_id = %s
            """,
                (current_user_id, company_id),
            )
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to manage users for this company",
                )

        # 3. Verify user exists
        if is_self_edit:
            # For self-edit, just verify user exists (no company check needed)
            cursor.execute(
                """
                SELECT
                    u.id, u.email, u.username, u.full_name, u.phone, u.linkedin_url,
                    COALESCE(
                        (SELECT r.name
                        FROM user_roles ur
                        JOIN roles r ON ur.role_id = r.id
                        WHERE ur.user_id = u.id
                        AND ur.is_active = true
                        ORDER BY ur.assigned_at DESC
                        LIMIT 1),
                        'candidate'
                    ) as role,
                    COALESCE(
                        (SELECT ur.role_id
                        FROM user_roles ur
                        WHERE ur.user_id = u.id
                        AND ur.is_active = true
                        ORDER BY ur.assigned_at DESC
                        LIMIT 1),
                        3
                    ) as default_role_id,
                    u.is_active, u.is_superuser, u.created_at, u.updated_at
                FROM users u
                WHERE u.id = %s
            """,
                (user_id,),
            )
        else:
            # For admin edit, verify user belongs to this company
            cursor.execute(
                """
                SELECT
                    u.id, u.email, u.username, u.full_name, u.phone, u.linkedin_url,
                    COALESCE(
                        (SELECT r.name
                        FROM user_roles ur
                        JOIN roles r ON ur.role_id = r.id
                        WHERE ur.user_id = u.id
                        AND ur.is_active = true
                        ORDER BY ur.assigned_at DESC
                        LIMIT 1),
                        'candidate'
                    ) as role,
                    COALESCE(
                        (SELECT ur.role_id
                        FROM user_roles ur
                        WHERE ur.user_id = u.id
                        AND ur.is_active = true
                        ORDER BY ur.assigned_at DESC
                        LIMIT 1),
                        3
                    ) as default_role_id,
                    u.is_active, u.is_superuser, u.created_at, u.updated_at
                FROM users u
                INNER JOIN users_companies uc ON u.id = uc.user_id
                WHERE u.id = %s AND uc.company_id = %s
            """,
                (user_id, company_id),
            )

        target_user = cursor.fetchone()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
                if is_self_edit
                else "User not found in this company",
            )

        # 5. Prepare Updates
        fields = []
        params = []

        if user_data.full_name is not None:
            fields.append("full_name = %s")
            params.append(user_data.full_name)

        if user_data.phone is not None:
            fields.append("phone = %s")
            params.append(user_data.phone)

        if user_data.linkedin_url is not None:
            fields.append("linkedin_url = %s")
            params.append(user_data.linkedin_url)

        # Field restrictions for self-edit:
        # - Self-edit: Cannot change role_id or is_active
        # - Admin edit: Can change all fields
        if is_self_edit:
            if user_data.role_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot change your own role",
                )
            if user_data.is_active is not None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot change your own active status",
                )
        else:
            # Admin edit: Allow role and is_active updates
            if user_data.is_active is not None:
                fields.append("is_active = %s")
                params.append(user_data.is_active)

        # Handle role update if provided (only for admin edits)
        if user_data.role_id is not None:
            if user_data.role_id == 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot assign Admin role (ID 1). Only one admin allowed per company.",
                )

            cursor.execute("SELECT name FROM roles WHERE id = %s", (user_data.role_id,))
            role_result = cursor.fetchone()
            if not role_result:
                raise HTTPException(
                    status_code=400, detail=f"Role ID {user_data.role_id} not found"
                )

            new_role_name = (
                role_result["name"] if hasattr(role_result, "keys") else role_result[0]
            )

            # Map granular role to base role category
            if new_role_name == "admin":
                base_role = "admin"
            elif new_role_name == "candidate":
                base_role = "candidate"
            else:
                base_role = "employer"

            # Update role in RBAC system
            cursor.execute(
                """
                UPDATE user_roles
                SET is_active = false
                WHERE user_id = %s AND is_active = true
            """,
                (user_id,),
            )

            cursor.execute(
                """
                INSERT INTO user_roles (user_id, role_id, assigned_at, is_active)
                VALUES (%s, %s, CURRENT_TIMESTAMP, true)
                ON CONFLICT (user_id, role_id)
                DO UPDATE SET is_active = true, assigned_at = CURRENT_TIMESTAMP
            """,
                (user_id, user_data.role_id),
            )

        if fields:
            fields.append("updated_at = NOW()")
            params.append(user_id)

            update_query = f"""
                UPDATE users
                SET {", ".join(fields)}
                WHERE id = %s
                RETURNING id, email, username, full_name, phone, linkedin_url, is_active, is_superuser, created_at, updated_at
            """
            cursor.execute(update_query, params)
            final_user = cursor.fetchone()

            # Get updated role information
            cursor.execute(
                """
                SELECT
                    COALESCE(
                        (SELECT r.name
                        FROM user_roles ur
                        JOIN roles r ON ur.role_id = r.id
                        WHERE ur.user_id = %s
                        AND ur.is_active = true
                        ORDER BY ur.assigned_at DESC
                        LIMIT 1),
                        'candidate'
                    ) as role,
                    COALESCE(
                        (SELECT ur.role_id
                        FROM user_roles ur
                        WHERE ur.user_id = %s
                        AND ur.is_active = true
                        ORDER BY ur.assigned_at DESC
                        LIMIT 1),
                        3
                    ) as default_role_id
            """,
                (user_id, user_id),
            )
            role_info = cursor.fetchone()
        else:
            # No fields to update, return current user
            final_user = target_user
            role_info = None

        conn.commit()

        # Format response based on data type
        is_dict = hasattr(final_user, "keys")

        if is_dict:
            role_name = (
                role_info.get("role")
                if role_info and hasattr(role_info, "keys")
                else target_user.get("role")
            )
            role_id = (
                role_info.get("default_role_id")
                if role_info and hasattr(role_info, "keys")
                else target_user.get("default_role_id")
            )

            return {
                "id": final_user["id"],
                "email": final_user["email"],
                "username": final_user["username"],
                "full_name": final_user["full_name"],
                "phone": final_user["phone"],
                "linkedin_url": final_user.get("linkedin_url"),
                "role": role_name,
                "default_role_id": role_id,
                "is_active": final_user["is_active"],
                "is_superuser": final_user["is_superuser"],
                "created_at": final_user["created_at"],
                "updated_at": final_user["updated_at"],
            }
        else:
            role_name = role_info[0] if role_info else target_user[6]
            role_id = role_info[1] if role_info else target_user[7]

            return {
                "id": final_user[0],
                "email": final_user[1],
                "username": final_user[2],
                "full_name": final_user[3],
                "phone": final_user[4],
                "linkedin_url": final_user[5],
                "role": role_name,
                "default_role_id": role_id,
                "is_active": final_user[6],
                "is_superuser": final_user[7],
                "created_at": final_user[8],
                "updated_at": final_user[9],
            }

    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error updating company user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        if cursor:
            cursor.close()


async def delete_company_user(
    company_id: int,
    user_id: int,
    current_user_id: int,
) -> bool:
    """
    Hard delete a user and their association with the company.

    This service:
    1. **Authorization**: Ensures the current user has rights to delete for this company.
    2. **Verification**: Checks if the user actually belongs to this company.
    3. **Hard Delete**: Removes the user from the `users` table entirely.
       Note: Related records in `users_companies` and `user_roles` will be
       automatically removed via database CASCADE constraints.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        conn.autocommit = False  # Use transaction
        cursor = conn.cursor()

        # 1. Verify company exists
        cursor.execute("SELECT id FROM companies WHERE id = %s", (company_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
            )

        # 2. Authorization Check
        cursor.execute(
            """
            SELECT 1 FROM users_companies
            WHERE user_id = %s AND company_id = %s
        """,
            (current_user_id, company_id),
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to manage users for this company",
            )

        # 3. RBAC Permission Check
        cursor.execute(
            "SELECT is_superuser FROM users WHERE id = %s", (current_user_id,)
        )
        user_status = cursor.fetchone()
        is_superuser = (
            user_status["is_superuser"]
            if hasattr(user_status, "keys")
            else user_status[0]
        )

        if not is_superuser:
            # RBAC checks moved to router to avoid connection closure mid-transaction
            pass

        # 4. Prevent self-deletion
        if user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot delete your own account",
            )

        # 5. Check if user belongs to this company
        cursor.execute(
            """
            SELECT 1 FROM users_companies
            WHERE user_id = %s AND company_id = %s
        """,
            (user_id, company_id),
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in this company",
            )

        # 6. Hard Delete from Users table
        # This will cascade delete from users_companies and user_roles if constraints are set,
        # otherwise we delete explicitly.
        cursor.execute("DELETE FROM users_companies WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

        conn.commit()
        return True

    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error deleting company user association: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        if cursor:
            cursor.close()


async def verify_company(company_id: int) -> Dict[str, Any]:
    """
    Verify a company by setting is_verified to True.
    Also activates the company admin user so they can login.

    Args:
        company_id: ID of the company to verify

    Returns:
        Dict containing the updated company data

    Raises:
        HTTPException: 404 if company not found, 400 if already verified
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor()

        # 1. Get company with admin user info
        cursor.execute(
            """
            SELECT c.is_verified, u.id as admin_user_id, u.email as admin_email, u.full_name as admin_name
            FROM companies c
            INNER JOIN users_companies uc ON c.id = uc.company_id
            INNER JOIN users u ON uc.user_id = u.id
            INNER JOIN user_roles ur ON u.id = ur.user_id
            WHERE c.id = %s AND ur.role_id = 1 AND ur.is_active = true
            LIMIT 1
        """,
            (company_id,),
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
            )

        # Extract values
        is_verified = row.get("is_verified") if hasattr(row, "keys") else row[0]
        if is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company is already verified",
            )

        admin_user_id = row.get("admin_user_id") if hasattr(row, "keys") else row[1]
        admin_email = row.get("admin_email") if hasattr(row, "keys") else row[2]
        admin_name = row.get("admin_name") if hasattr(row, "keys") else row[3]

        # 2. Update is_verified to True
        cursor.execute(
            "UPDATE companies SET is_verified = true, updated_at = NOW() WHERE id = %s",
            (company_id,),
        )

        # 3. Activate the company admin user so they can login
        cursor.execute(
            "UPDATE users SET is_active = true, updated_at = NOW() WHERE id = %s",
            (admin_user_id,),
        )

        conn.commit()

        # 4. Get full company data for response
        company = get_company_by_id(company_id)

        return {
            "company": company,
            "admin_email": admin_email,
            "admin_name": admin_name,
            "company_name": company["name"],
        }

    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error verifying company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        if cursor:
            cursor.close()
