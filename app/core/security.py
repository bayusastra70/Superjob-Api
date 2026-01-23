
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth import verify_token
from app.services.auth import auth
from app.schemas.user import UserResponse

from functools import wraps
from sqlalchemy.orm import Session

from app.services import role_base_access_control_service as rbac_service

from app.services.database import get_db_connection

import logging
logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple authentication - just verify token is valid"""

    logger.info("TEST GET CURRENT USER 1");
    token_data = verify_token(credentials.credentials)
    logger.info("TEST GET CURRENT USER 2");

    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    logger.info("TEST GET CURRENT USER 3");
    
    # Untuk cepat: return dummy user dari token data saja
    # Atau ambil dari database standalone
    
    # from app.services.auth import auth
    email = token_data.get("email") or token_data.get("sub")

    logger.info("TEST GET CURRENT USER 4");
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing email"
        )
    
    logger.info("TEST GET CURRENT USER 5");
    
    # Get user from standalone database
    user = auth.get_user_by_email(email)
    
    logger.info("Auth user data: %s", user)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Populate request state for structured logging
    request.state.user_id = user["id"]
    request.state.user_role = user["role"]
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        username=user["username"],
        full_name=user.get("full_name"),
        is_active=user["is_active"],
        is_superuser=user.get("is_superuser", False),
        role=user.get("role", "candidate"),  # <-- PASTIKAN INI ADA!
        company_id=user.get("company_id")
    )


async def require_admin_role(current_user: dict = Depends(get_current_user)):
    """Dependency untuk memastikan user adalah admin"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def require_role(allowed_roles: list):
    """Dependency factory untuk role-based access control"""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker


def require_permission(permission_code: str):
    def dependency(
        current_user = Depends(get_current_user)
    ):
        # Superuser bypass
        if current_user.is_superuser:
            return

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT 1
                FROM user_roles ur
                JOIN role_permissions rp ON rp.role_id = ur.role_id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE ur.user_id = %s
                  AND ur.is_active = true
                  AND p.code = %s
                  AND p.is_active = true
                LIMIT 1
            """

            cursor.execute(query, (
                current_user.id,
                permission_code
            ))

            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires permission: {permission_code}"
                )
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return dependency



def require_role(role_name: str):
    def dependency(
        current_user = Depends(get_current_user)
    ):
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 1
            FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = %s
              AND r.name = %s
              AND ur.is_active = true
        """, (current_user["id"], role_name))

        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {role_name}"
            )

        cursor.close()
        conn.close()

    return dependency
