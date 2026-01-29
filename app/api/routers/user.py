from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
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
    created_response
)

from app.schemas.user import (
    UserUpdate,
    UserListResponse,
    UserResponse,
    UserUpdateSimple,
    UserUpdateResponseSimple,
    UserPasswordUpdate
)
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
    search: Optional[str] = Query(None, description="Search in email, username, full_name"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc")
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
        valid_sort_fields = ["id", "email", "username", "full_name", "phone", "role", "is_active", "created_at", "updated_at"]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"

        # Hitung offset
        offset = (page - 1) * limit

        # Build WHERE clause
        where_clause = "WHERE 1=1"
        params = []

        if search:
            search_pattern = f"%{search}%"
            where_clause += " AND (email ILIKE %s OR username ILIKE %s OR full_name ILIKE %s)"
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
            if hasattr(count_result, 'keys'):
                total_count = count_result['count'] if 'count' in count_result else list(count_result.values())[0]
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
            if hasattr(user, 'keys'):
                users_list.append({
                    "id": user.get('id'),
                    "email": user.get('email'),
                    "username": user.get('username'),
                    "full_name": user.get('full_name'),
                    "phone": user.get('phone'),
                    "role": user.get('role'),
                    "is_active": user.get('is_active'),
                    "is_superuser": user.get('is_superuser'),
                    "created_at": user.get('created_at'),
                    "updated_at": user.get('updated_at')
                })
            # Jika tuple/list
            else:
                users_list.append({
                    "id": user[0],
                    "email": user[1],
                    "username": user[2],
                    "full_name": user[3],
                    "phone": user[4],
                    "role": user[5],
                    "is_active": user[6],
                    "is_superuser": user[7],
                    "created_at": user[8],
                    "updated_at": user[9]
                })

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
                "has_prev": page > 1
            },
            "filters": {
                "search": search,
                "role": role,
                "is_active": is_active,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }

    except Exception as e:
        logger.error(f"Error getting users list: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users list"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Update juga endpoint lainnya untuk handle RealDictRow
@router.get(
    "/{user_id}",
    summary="Get User by ID",
    description="Get user information by ID. Any authenticated user can access."
)
async def get_user_by_id(
    user_id: int
):
    """Get user by ID"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, email, username, full_name, phone, role,
                   is_active, is_superuser, created_at, updated_at
            FROM users WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )

        # Handle RealDictRow
        if hasattr(user, 'keys'):
            user_data = {
                "id": user.get('id'),
                "email": user.get('email'),
                "username": user.get('username'),
                "full_name": user.get('full_name'),
                "phone": user.get('phone'),
                "role": user.get('role'),
                "is_active": user.get('is_active'),
                "is_superuser": user.get('is_superuser'),
                "created_at": user.get('created_at'),
                "updated_at": user.get('updated_at')
            }
        else:
            user_data = {
                "id": user[0],
                "email": user[1],
                "username": user[2],
                "full_name": user[3],
                "phone": user[4],
                "role": user[5],
                "is_active": user[6],
                "is_superuser": user[7],
                "created_at": user[8],
                "updated_at": user[9]
            }

        return {
            "code": 200,
            "is_success": True,
            "message": "User retrieved successfully",
            "data": user_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user by ID: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


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
    description="Get current user's profile information"
)
async def get_my_profile(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get current user's profile"""
    try:
        # Gunakan service untuk mendapatkan profile dengan RBAC
        user_data = user_service.get_user_profile_with_rbac(current_user.id)

        if not user_data:
            return not_found_response(
                    message=f"User not found"
                )

        return success_response(
            data=user_data,
            message="Profile retrieved successfully"
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
    valid_statuses = ["applied", "in_review", "qualified", "not_qualified", "contract_signed"]
    if status and status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Status '{status}' tidak valid. Status yang tersedia: {', '.join(valid_statuses)}",
                "valid_statuses": valid_statuses,
                "example": f"?status={valid_statuses[0]}"
            }
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

        return success_response(
            data={
                "applications": applications,
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": {"status": status},
            },
            message="Berhasil mengambil daftar lamaran"
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
    tags=["users"]
)
async def update_user_no_auth(
    user_id: int,
    user_data: UserUpdateSimple
):
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
                is_active=user_data.is_active
            )
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ve)
            )

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )

        return {
            "success": True,
            "message": "User updated successfully",
            "user": updated_user
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
    - Updates CV URL

    **Permissions:**
    - **Candidates Only:** Only users with candidate privileges can use this endpoint.
    - **Self Update Only:** Users can only update their own profile.
    """
)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update user profile via Service Layer (Candidate Only)"""

    # Extract user info from UserResponse
    current_user_id = current_user.id

    # 1. Strict Self-Update Check
    if current_user_id != user_id:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )

    # 2. Strict Candidate Role Check using RBAC
    is_candidate = RoleBaseAccessControlService.user_has_role(current_user_id, "candidate")

    if not is_candidate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can use this endpoint"
        )

    updated_user = user_service.update_user_profile(user_id, user_update)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "code": 200,
        "is_success": True,
        "message": "User profile updated successfully",
        "data": updated_user
    }


@router.put(
    "/{user_id}/password",
    summary="Update User Password",
    description="""
    Update user password. Requires current password verification.

    **Permissions:**
    - **Self Update Only:** Users can only update their own password.

    **Rate Limit:** 5 requests per minute.
    """
)
@limiter.limit("5/minute")
async def update_password(
    request: Request,
    user_id: int,
    password_data: UserPasswordUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update user password endpoint"""

    current_user_id = current_user.id

    # Strict Self-Update Check
    if current_user_id != user_id:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's password"
        )

    success = user_service.update_user_password(user_id, password_data)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "code": 200,
        "is_success": True,
        "message": "Password updated successfully",
        "data": None
    }
