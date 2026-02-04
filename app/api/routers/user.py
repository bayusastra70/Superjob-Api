from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Request,
    UploadFile,
    File,
)
from typing import Optional
from loguru import logger

from app.services.database import get_db_connection
from app.core.security import get_current_user

from app.utils.response import (
    success_response,
    unauthorized_response,
    internal_server_error_response,
    not_found_response,
    bad_request_response,
    created_response,
)

from app.schemas.user import (
    UserUpdate,
    UserListResponse,
    UserResponse,
    UserUpdateSimple,
    UserUpdateResponseSimple,
    UserPasswordUpdate,
    UserProfileResponse,
    JobPreferencesUpdate,
)
from pydantic import ValidationError
from app.exceptions.custom_exceptions import BadRequestException
from app.schemas.response import BaseResponse
from app.services.auth import auth
from app.services.user_service import user_service
from app.services.role_base_access_control_service import RoleBaseAccessControlService
from app.services.application_service import ApplicationService
from app.core.limiter import limiter


router = APIRouter(prefix="/users", tags=["users"])

application_service = ApplicationService()


@router.get(
    "/",
    response_model=UserListResponse,
    summary="Get Users List",
    description="""
    Get list of users with pagination, filtering, and sorting.
    
    **Permissions:** Any authenticated user
    **Features:**
    - Pagination (page, limit)
    - Search by email, username, or full_name
    - Filter by role and active status
    - Sort by any field
    """,
)
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(
        None, description="Search in email, username, full_name"
    ),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
):
    """Get users list with pagination and filtering"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        # GUNAKAN cursor dengan dictionary=False (default) atau handle keduanya
        cursor = conn.cursor()

        # Validasi sort order
        if sort_order.lower() not in ["asc", "desc"]:
            sort_order = "desc"

        # Validasi sort field
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

        # Hitung offset
        offset = (page - 1) * limit

        # Build WHERE clause
        where_clause = "WHERE 1=1"
        params = []

        if search:
            search_pattern = f"%{search}%"
            where_clause += (
                " AND (email ILIKE %s OR username ILIKE %s OR full_name ILIKE %s)"
            )
            params.extend([search_pattern, search_pattern, search_pattern])

        if role:
            where_clause += " AND role = %s"
            params.append(role)

        if is_active is not None:
            where_clause += " AND is_active = %s"
            params.append(is_active)

        # Query untuk count (tanpa alias untuk menghindari RealDictRow)
        count_query = f"SELECT COUNT(*) FROM users {where_clause}"

        # Query untuk data
        data_query = f"""
            SELECT id, email, username, full_name, phone, role,
                   is_active, is_superuser, created_at, updated_at
            FROM users {where_clause}
            ORDER BY {sort_by} {sort_order.upper()}
            LIMIT %s OFFSET %s
        """

        # Eksekusi count (tanpa alias)
        cursor.execute(count_query, params)
        count_result = cursor.fetchone()

        # Handle berbagai format hasil
        if count_result:
            # Jika RealDictRow
            if hasattr(count_result, "keys"):
                total_count = (
                    count_result["count"]
                    if "count" in count_result
                    else list(count_result.values())[0]
                )
            # Jika tuple
            elif isinstance(count_result, (tuple, list)):
                total_count = count_result[0]
            # Lainnya
            else:
                total_count = count_result
        else:
            total_count = 0

        # Eksekusi data dengan pagination params
        data_params = params + [limit, offset]
        cursor.execute(data_query, data_params)
        users = cursor.fetchall()

        # Format results dengan handle RealDictRow
        users_list = []
        for user in users:
            # Jika RealDictRow
            if hasattr(user, "keys"):
                users_list.append(
                    {
                        "id": user.get("id"),
                        "email": user.get("email"),
                        "username": user.get("username"),
                        "full_name": user.get("full_name"),
                        "phone": user.get("phone"),
                        "role": user.get("role"),
                        "is_active": user.get("is_active"),
                        "is_superuser": user.get("is_superuser"),
                        "created_at": user.get("created_at"),
                        "updated_at": user.get("updated_at"),
                    }
                )
            # Jika tuple/list
            else:
                users_list.append(
                    {
                        "id": user[0],
                        "email": user[1],
                        "username": user[2],
                        "full_name": user[3],
                        "phone": user[4],
                        "role": user[5],
                        "is_active": user[6],
                        "is_superuser": user[7],
                        "created_at": user[8],
                        "updated_at": user[9],
                    }
                )

        # Hitung total pages
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
                "has_prev": page > 1,
            },
            "filters": {
                "search": search,
                "role": role,
                "is_active": is_active,
                "sort_by": sort_by,
                "sort_order": sort_order,
            },
        }

    except Exception as e:
        logger.error(f"Error getting users list: {str(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users list",
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Update juga endpoint lainnya untuk handle RealDictRow
@router.get(
    "/{user_id}",
    response_model=BaseResponse[UserProfileResponse],
    summary="Get User by ID",
    description="""
    Get user information by ID with authorization check.
    
    **Authorization Rules:**
    - **Self:** Users can view their own profile.
    - **Admin:** Admins can view any profile.
    - **Employer:** Can view candidates who applied to their company's jobs.
    """,
)
async def get_user_by_id(
    user_id: int, current_user: UserResponse = Depends(get_current_user)
):
    """Get user by ID with authorization"""

    current_user_id = current_user.id
    current_user_role = current_user.role or ""

    # Check authorization
    if not user_service.can_access_profile(current_user_id, current_user_role, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    # Get user profile with CV data
    user_data = user_service.get_user_profile_with_cv(user_id)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    return success_response(message="User retrieved successfully", data=user_data)


# Update juga get_my_profile
# @router.get(
#     "/profile/me",
#     summary="Get My Profile",
#     description="Get current user's profile information"
# )
# async def get_my_profile(
#     current_user: UserResponse = Depends(get_current_user)
# ):
#     """Get current user's profile"""
#     conn = None
#     cursor = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         cursor.execute(
#             """
#             SELECT u.id, u.email, u.username, u.full_name, u.phone, u.role, u.default_role_id,
#                    u.is_active, u.is_superuser, u.created_at, u.updated_at, uc.company_id
#             FROM users u
#             LEFT JOIN users_companies uc ON u.id = uc.user_id
#             WHERE u.id = %s
#             """,
#             (current_user.id,)
#         )

#         user = cursor.fetchone()

#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="User not found"
#             )

#         # Handle RealDictRow
#         if hasattr(user, 'keys'):
#             user_data = {
#                 "id": user.get('id'),
#                 "email": user.get('email'),
#                 "username": user.get('username'),
#                 "full_name": user.get('full_name'),
#                 "phone": user.get('phone'),
#                 "role": user.get('role'),
#                 "default_role_id": user.get('default_role_id'),
#                 "company_id": user.get('company_id'),
#                 "is_active": user.get('is_active'),
#                 "is_superuser": user.get('is_superuser'),
#                 "created_at": user.get('created_at'),
#                 "updated_at": user.get('updated_at')
#             }
#         else:
#             user_data = {
#                 "id": user[0],
#                 "email": user[1],
#                 "username": user[2],
#                 "full_name": user[3],
#                 "phone": user[4],
#                 "role": user[5],
#                 "default_role_id": user[6],
#                 "is_active": user[7],
#                 "is_superuser": user[8],
#                 "created_at": user[9],
#                 "updated_at": user[10],
#                 "company_id": user[11]
#             }

#         return {
#             "code": 200,
#             "is_success": True,
#             "message": "Profile retrieved successfully",
#             "data": user_data
#         }

#     except Exception as e:
#         logger.error(f"Error getting user profile: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to retrieve profile information"
#         )
#     finally:
#         if cursor:
#             cursor.close()
#         if conn:
#             conn.close()


# @router.get(
#     "/profile/me",
#     summary="Get My Profile",
#     description="Get current user's profile information"
# )
# async def get_my_profile(
#     current_user: UserResponse = Depends(get_current_user)
# ):
#     """Get current user's profile"""
#     conn = None
#     cursor = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Coba query baru dulu, jika gagal coba query fallback
#         try:
#             cursor.execute(
#                 """
#                 SELECT
#                     u.id,
#                     u.email,
#                     u.username,
#                     u.full_name,
#                     u.phone,
#                     u.is_active,
#                     u.is_superuser,
#                     u.created_at,
#                     u.updated_at,
#                     uc.company_id,
#                     -- Ambil role dari user_roles
#                     COALESCE(
#                         (SELECT r.name
#                          FROM user_roles ur
#                          JOIN roles r ON ur.role_id = r.id
#                          WHERE ur.user_id = u.id
#                          AND ur.is_active = true
#                          ORDER BY ur.assigned_at DESC
#                          LIMIT 1),
#                         'candidate'
#                     ) as role,
#                     -- Ambil role_id sebagai default_role_id
#                     COALESCE(
#                         (SELECT ur.role_id
#                          FROM user_roles ur
#                          WHERE ur.user_id = u.id
#                          AND ur.is_active = true
#                          ORDER BY ur.assigned_at DESC
#                          LIMIT 1),
#                         3
#                     ) as default_role_id
#                 FROM users u
#                 LEFT JOIN users_companies uc ON u.id = uc.user_id
#                 WHERE u.id = %s
#                 """,
#                 (current_user.id,)
#             )
#         except Exception as query_error:
#             # Jika query gagal, coba query tanpa kolom RBAC (fallback)
#             logger.warning(f"RBAC query failed, using fallback: {query_error}")
#             cursor.execute(
#                 """
#                 SELECT
#                     u.id,
#                     u.email,
#                     u.username,
#                     u.full_name,
#                     u.phone,
#                     u.is_active,
#                     u.is_superuser,
#                     u.created_at,
#                     u.updated_at,
#                     uc.company_id
#                 FROM users u
#                 LEFT JOIN users_companies uc ON u.id = uc.user_id
#                 WHERE u.id = %s
#                 """,
#                 (current_user.id,)
#             )

#         user = cursor.fetchone()

#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="User not found"
#             )

#         # Handle RealDictRow
#         if hasattr(user, 'keys'):
#             user_data = {
#                 "id": user.get('id'),
#                 "email": user.get('email'),
#                 "username": user.get('username'),
#                 "full_name": user.get('full_name'),
#                 "phone": user.get('phone'),
#                 "company_id": user.get('company_id'),
#                 "is_active": user.get('is_active'),
#                 "is_superuser": user.get('is_superuser'),
#                 "created_at": user.get('created_at'),
#                 "updated_at": user.get('updated_at')
#             }

#             # Tambahkan role dan default_role_id jika ada di result
#             if 'role' in user:
#                 user_data["role"] = user.get('role')
#             else:
#                 user_data["role"] = current_user.role or "candidate"

#             if 'default_role_id' in user:
#                 user_data["default_role_id"] = user.get('default_role_id')
#             else:
#                 user_data["default_role_id"] = current_user.default_role_id or 3

#         else:
#             # Cek berapa banyak kolom yang return
#             col_count = len(user)

#             user_data = {
#                 "id": user[0],
#                 "email": user[1],
#                 "username": user[2],
#                 "full_name": user[3],
#                 "phone": user[4],
#                 "is_active": user[5],
#                 "is_superuser": user[6],
#                 "created_at": user[7],
#                 "updated_at": user[8],
#                 "company_id": user[9] if col_count > 9 else None,
#                 "role": user[10] if col_count > 10 else (current_user.role or "candidate"),
#                 "default_role_id": user[11] if col_count > 11 else (current_user.default_role_id or 3)
#             }

#         return {
#             "code": 200,
#             "is_success": True,
#             "message": "Profile retrieved successfully",
#             "data": user_data
#         }

#     except Exception as e:
#         logger.error(f"Error getting user profile: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to retrieve profile information"
#         )
#     finally:
#         if cursor:
#             cursor.close()
#         if conn:
#             conn.close()


@router.get(
    "/profile/me",
    summary="Get My Profile",
    description="Get current user's profile information",
)
async def get_my_profile(current_user: UserResponse = Depends(get_current_user)):
    """Get current user's profile"""
    try:
        # Gunakan service untuk mendapatkan profile dengan RBAC
        user_data = user_service.get_user_profile_with_rbac(current_user.id)

        if not user_data:
            return not_found_response(message=f"User not found")

        return success_response(
            data=user_data, message="Profile retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise


@router.get(
    "/me/applications",
    summary="Get My Applications",
    description="""
    Mendapatkan daftar lamaran user yang sedang login.

    **Fitur:**
    - User hanya bisa melihat lamaran miliknya sendiri
    - Filter berdasarkan status
    - Support pagination (limit & offset)

    **Status yang valid:**
    - `applied` - Baru melamar
    - `in_review` - Sedang direview
    - `qualified` - Lolos kualifikasi
    - `not_qualified` - Tidak lolos
    - `contract_signed` - Kontrak ditandatangani

    **⚠️ Membutuhkan Authorization Token!**
    """,
)
async def get_my_applications(
    status: Optional[str] = Query(
        None,
        description="Filter by status (applied, in_review, qualified, not_qualified, contract_signed)",
    ),
    limit: int = Query(50, ge=1, le=100, description="Jumlah item per halaman"),
    offset: int = Query(0, ge=0, description="Offset untuk pagination"),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get current user's applications with optional status filter"""
    # Validasi status jika diberikan
    valid_statuses = [
        "applied",
        "in_review",
        "qualified",
        "not_qualified",
        "contract_signed",
    ]
    if status and status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Status '{status}' tidak valid. Status yang tersedia: {', '.join(valid_statuses)}",
                "valid_statuses": valid_statuses,
                "example": f"?status={valid_statuses[0]}",
            },
        )

    try:
        applications = application_service.get_my_applications(
            user_id=current_user.id,
            status=status,
            limit=limit,
            offset=offset,
        )

        total = application_service.count_my_applications(
            user_id=current_user.id,
            status=status,
        )

        # Calculate pagination metadata
        page = (offset // limit) + 1
        total_pages = (total + limit - 1) // limit if total > 0 else 1

        return success_response(
            data={
                "applications": applications,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
            },
            message="Berhasil mengambil daftar lamaran",
        )

    except Exception as e:
        logger.error(f"Error getting my applications: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put(
    "/{user_id}/update",
    response_model=UserUpdateResponseSimple,
    summary="Update User Data (No Auth Required)",
    description="""
    Update semua data user TANPA authentication/authorization.
    Hanya untuk testing/demo purposes.

    **⚠️ WARNING:** Tidak ada security check! Gunakan dengan hati-hati.

    **Fields yang bisa diupdate:**
    - email
    - username
    - full_name
    - phone
    - role (admin, employer, candidate)
    - is_active
    """,
    tags=["users"],
)
async def update_user_no_auth(user_id: int, user_data: UserUpdateSimple):
    """Update user data without authentication (for testing)"""
    try:
        try:
            updated_user = auth.update_user_simple(
                user_id=user_id,
                email=user_data.email,
                username=user_data.username,
                full_name=user_data.full_name,
                phone=user_data.phone,
                role=user_data.role,
                is_active=user_data.is_active,
            )
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        return {
            "success": True,
            "message": "User updated successfully",
            "user": updated_user,
        }

    except HTTPException:
        raise


@router.put(
    "/{user_id}",
    summary="Update User Profile (Candidate Only)",
    description="""
    Update user profile information.

    **Features:**
    - Updates standard fields (full_name, phone)
    - Upload CV file to Solvera Storage
    - Save extracted CV data (if provided)

    **Permissions:**
    - **Candidates Only:** Only users with candidate privileges can use this endpoint.
    - **Self Update Only:** Users can only update their own profile.

    **Content-Type:** multipart/form-data
    """,
)
async def update_user(
    request: Request,
    user_id: int,
    current_user: UserResponse = Depends(get_current_user),
):
    """Update user profile via Service Layer (Candidate Only)"""

    current_user_id = current_user.id

    if current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )

    is_candidate = RoleBaseAccessControlService.user_has_role(
        current_user_id, "candidate"
    )

    if not is_candidate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can use this endpoint",
        )

    try:
        form_data = await request.form()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid form data",
        )

    full_name = form_data.get("full_name")
    phone = form_data.get("phone")
    linkedin_url = form_data.get("linkedin_url")
    cv_file = form_data.get("cv_file")

    user_update_data = {
        "full_name": full_name,
        "phone": phone,
        "linkedin_url": linkedin_url,
    }

    # Track uploaded file for potential cleanup
    uploaded_storage_id = None

    if cv_file and hasattr(cv_file, "filename") and cv_file.filename:
        try:
            cv_url, storage_id = await user_service.upload_cv_file(user_id, cv_file)
            user_update_data["cv_url"] = cv_url
            uploaded_storage_id = storage_id  # Track for rollback
            logger.info(f"CV file uploaded for user {user_id}: {cv_url}")
        except Exception as e:
            logger.error(f"Failed to upload CV file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload CV file",
            )

    try:
        user_service.update_user_profile(user_id, user_update_data)
    except Exception as e:
        # Database update failed - cleanup uploaded file
        if uploaded_storage_id:
            logger.warning(
                f"Database update failed, cleaning up uploaded CV file: {uploaded_storage_id}"
            )
            await user_service.delete_cv_file(uploaded_storage_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile",
        )

    updated_user = user_service.get_user_profile_with_cv(user_id)

    if not updated_user:
        # User not found after update - cleanup uploaded file
        if uploaded_storage_id:
            logger.warning(
                f"User not found after update, cleaning up uploaded CV file: {uploaded_storage_id}"
            )
            await user_service.delete_cv_file(uploaded_storage_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    summary = form_data.get("summary")
    email = form_data.get("email")
    skills_str = form_data.get("skills")
    languages_str = form_data.get("languages")
    experience_str = form_data.get("experience")
    education_str = form_data.get("education")
    certifications_str = form_data.get("certifications")

    # Build cv_data only with fields that were explicitly provided
    # Use "is not None" to distinguish between "not provided" vs "provided as empty"
    cv_data = {}

    # Build profile data with email and summary
    profile_data = {}
    if email is not None:
        profile_data["email"] = email
    if summary is not None:
        profile_data["summary"] = summary
    if profile_data:
        cv_data["profile"] = profile_data

    if skills_str is not None:
        import json

        cv_data["skills"] = json.loads(skills_str)

    if languages_str is not None:
        import json

        cv_data["languages"] = json.loads(languages_str)

    if experience_str is not None:
        import json
        from app.schemas.cv_extraction import WorkExperience

        try:
            experience_list = json.loads(experience_str)
            if not isinstance(experience_list, list):
                raise ValueError("experience must be a list")
            for i, exp in enumerate(experience_list):
                WorkExperience(**exp)
            cv_data["experience"] = experience_list
        except (json.JSONDecodeError, ValueError) as e:
            raise BadRequestException(message=f"Experience data: {str(e)}")

    if education_str is not None:
        import json
        from app.schemas.cv_extraction import Education

        try:
            education_list = json.loads(education_str)
            if not isinstance(education_list, list):
                raise ValueError("education must be a list")
            for i, edu in enumerate(education_list):
                Education(**edu)
            cv_data["education"] = education_list
        except (json.JSONDecodeError, ValueError) as e:
            raise BadRequestException(message=f"Education data: {str(e)}")

    if certifications_str is not None:
        import json
        from app.schemas.cv_extraction import Certification

        try:
            certifications_list = json.loads(certifications_str)
            if not isinstance(certifications_list, list):
                raise ValueError("certifications must be a list")
            for i, cert in enumerate(certifications_list):
                Certification(**cert)
            cv_data["certifications"] = certifications_list
        except (json.JSONDecodeError, ValueError) as e:
            raise BadRequestException(message=f"Certification data: {str(e)}")

    # Only update if there's data to update
    if cv_data:
        try:
            user_service.update_user_cv_data(user_id, cv_data)
        except Exception as e:
            # CV data update failed - cleanup uploaded file if it was new
            if uploaded_storage_id:
                logger.warning(
                    f"CV data update failed, cleaning up uploaded CV file: {uploaded_storage_id}"
                )
                await user_service.delete_cv_file(uploaded_storage_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update CV data",
            )

    # Handle job preferences
    preferred_locations_str = form_data.get("preferred_locations")
    preferred_work_modes_str = form_data.get("preferred_work_modes")
    preferred_job_types_str = form_data.get("preferred_job_types")
    expected_salary_min_str = form_data.get("expected_salary_min")
    expected_salary_max_str = form_data.get("expected_salary_max")
    preferred_industries_str = form_data.get("preferred_industries")
    preferred_divisions_str = form_data.get("preferred_divisions")
    auto_apply_enabled_str = form_data.get("auto_apply_enabled")

    job_preferences = {}
    import json

    if preferred_locations_str is not None:
        try:
            locations = json.loads(preferred_locations_str)
            if not isinstance(locations, list):
                raise ValueError("must be a list")
            job_preferences["preferred_locations"] = locations
        except (json.JSONDecodeError, ValueError) as e:
            raise BadRequestException(message=f"Preferred locations: {str(e)}")

    if preferred_work_modes_str is not None:
        try:
            modes = json.loads(preferred_work_modes_str)
            if not isinstance(modes, list):
                raise ValueError("must be a list")
            job_preferences["preferred_work_modes"] = modes
        except (json.JSONDecodeError, ValueError) as e:
            raise BadRequestException(
                message=f"Preferred work modes format is invalid: {str(e)}"
            )

    if preferred_job_types_str is not None:
        try:
            types = json.loads(preferred_job_types_str)
            if not isinstance(types, list):
                raise ValueError("must be a list")
            job_preferences["preferred_job_types"] = types
        except (json.JSONDecodeError, ValueError) as e:
            raise BadRequestException(
                message=f"Preferred job types format is invalid: {str(e)}"
            )

    if expected_salary_min_str is not None:
        try:
            job_preferences["expected_salary_min"] = float(expected_salary_min_str)
        except ValueError:
            raise BadRequestException(message="Minimum salary must be a valid number")

    if expected_salary_max_str is not None:
        try:
            job_preferences["expected_salary_max"] = float(expected_salary_max_str)
        except ValueError:
            raise BadRequestException(message="Maximum salary must be a valid number")

    if preferred_industries_str is not None:
        try:
            industries = json.loads(preferred_industries_str)
            if not isinstance(industries, list):
                raise ValueError("must be a list")
            job_preferences["preferred_industries"] = industries
        except (json.JSONDecodeError, ValueError) as e:
            raise BadRequestException(
                message=f"Preferred industries format is invalid: {str(e)}"
            )

    if preferred_divisions_str is not None:
        try:
            divisions = json.loads(preferred_divisions_str)
            if not isinstance(divisions, list):
                raise ValueError("must be a list")
            job_preferences["preferred_divisions"] = divisions
        except (json.JSONDecodeError, ValueError) as e:
            raise BadRequestException(
                message=f"Preferred divisions format is invalid: {str(e)}"
            )

    if auto_apply_enabled_str is not None:
        job_preferences["auto_apply_enabled"] = auto_apply_enabled_str.lower() in (
            "true",
            "1",
            "yes",
        )

    if job_preferences:
        try:
            validated_preferences = JobPreferencesUpdate(**job_preferences)
            user_service.update_job_preferences(
                user_id, validated_preferences.model_dump(exclude_unset=True)
            )
        except ValidationError as e:
            error = e.errors()[0]
            loc = " > ".join(str(l) for l in error["loc"]) if error["loc"] else "field"
            field_name = loc.split(" > ")[-1].replace("_", " ").title()
            raise BadRequestException(message=f"{field_name}: {error['msg']}")
        except Exception as e:
            logger.error(f"Failed to update job preferences: {e}")
            raise BadRequestException(message="Failed to update job preferences")

    if work_modes_str is not None:
        try:
            modes = json.loads(work_modes_str)
            if not isinstance(modes, list):
                raise ValueError("must be a list")
            job_preferences["work_modes"] = modes
        except (json.JSONDecodeError, ValueError) as e:
            raise BadRequestException(message=f"Work modes: {str(e)}")

    if job_types_str is not None:
        try:
            types = json.loads(job_types_str)
            if not isinstance(types, list):
                raise ValueError("must be a list")
            job_preferences["job_types"] = types
        except (json.JSONDecodeError, ValueError) as e:
            raise BadRequestException(message=f"Job types: {str(e)}")

    if expected_salary_min_str is not None:
        try:
            job_preferences["expected_salary_min"] = float(expected_salary_min_str)
        except ValueError:
            raise BadRequestException(message="Minimum salary must be a valid number")

    if expected_salary_max_str is not None:
        try:
            job_preferences["expected_salary_max"] = float(expected_salary_max_str)
        except ValueError:
            raise BadRequestException(message="Maximum salary must be a valid number")

    if preferred_industries_str is not None:
        try:
            industries = json.loads(preferred_industries_str)
            if not isinstance(industries, list):
                raise ValueError("must be a list")
            job_preferences["preferred_industries"] = industries
        except (json.JSONDecodeError, ValueError) as e:
            raise BadRequestException(message=f"Preferred industries: {str(e)}")

    if preferred_divisions_str is not None:
        try:
            divisions = json.loads(preferred_divisions_str)
            if not isinstance(divisions, list):
                raise ValueError("must be a list")
            job_preferences["preferred_divisions"] = divisions
        except (json.JSONDecodeError, ValueError) as e:
            raise BadRequestException(message=f"Preferred divisions: {str(e)}")

    if auto_apply_enabled_str is not None:
        job_preferences["auto_apply_enabled"] = auto_apply_enabled_str.lower() in (
            "true",
            "1",
            "yes",
        )

    if job_preferences:
        try:
            validated_preferences = JobPreferencesUpdate(**job_preferences)
            user_service.update_job_preferences(
                user_id, validated_preferences.model_dump(exclude_unset=True)
            )
        except ValidationError as e:
            error = e.errors()[0]
            loc = " > ".join(str(l) for l in error["loc"]) if error["loc"] else "field"
            field_name = loc.split(" > ")[-1].replace("_", " ").title()
            raise BadRequestException(message=f"{field_name}: {error['msg']}")
        except Exception as e:
            logger.error(f"Failed to update job preferences: {e}")
            raise BadRequestException(message="Failed to update job preferences")

    return {
        "code": 200,
        "is_success": True,
        "message": "User profile updated successfully",
        "data": updated_user,
    }


@router.put(
    "/{user_id}/password",
    summary="Update User Password",
    description="""
    Update user password. Requires current password verification.

    **Permissions:**
    - **Self Update Only:** Users can only update their own password.

    **Rate Limit:** 5 requests per minute.
    """,
)
@limiter.limit("5/minute")
async def update_password(
    request: Request,
    user_id: int,
    password_data: UserPasswordUpdate,
    current_user: UserResponse = Depends(get_current_user),
):
    """Update user password endpoint"""

    current_user_id = current_user.id

    # Strict Self-Update Check
    if current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's password",
        )

    success = user_service.update_user_password(user_id, password_data)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return {
        "code": 200,
        "is_success": True,
        "message": "Password updated successfully",
        "data": None,
    }
