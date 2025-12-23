
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import logging

from app.services.database import get_db_connection
from app.core.security import get_current_user

from app.schemas.user import (
    UserResponse, UserListResponse, 
    UserUpdateSimple, UserUpdateResponseSimple
)
from app.services.auth import auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


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
    response_model=UserResponse,
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
            return {
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
            return {
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
@router.get(
    "/profile/me",
    response_model=UserResponse,
    summary="Get My Profile",
    description="Get current user's profile information"
)
async def get_my_profile(
    current_user: dict = Depends(get_current_user)
):
    """Get current user's profile"""
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
            (current_user["id"],)
        )
        
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Handle RealDictRow
        if hasattr(user, 'keys'):
            return {
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
            return {
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
        
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile information"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


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
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )