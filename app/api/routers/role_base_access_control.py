from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas import role_base_access_control as schemas
from app.services import role_base_access_control_service as rbac_service
from app.core.security import get_current_user, require_permission

from app.schemas.response import BaseResponse
from app.utils.response import success_response

from loguru import logger



router = APIRouter(prefix="/rbac", tags=["RoleBaseAccessControl"])


# ========== PERMISSION ENDPOINTS ==========
@router.get(
    "/permissions",
    response_model=BaseResponse[List[schemas.PermissionInDB]],
    # dependencies=[Depends(require_permission("permission.read"))]
)
# @require_permission("permission.read")
def read_permissions(
    skip: int = 0,
    limit: int = 100,
    module: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user = Depends(get_current_user)
):
    try:
        permissions = rbac_service.RoleBaseAccessControlService.get_permissions(
            skip=skip,
            limit=limit,
            module=module,
            is_active=is_active
        )
        return success_response(
            data=permissions,
            message="Permissions retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


@router.post(
    "/permissions",
    response_model=BaseResponse[schemas.PermissionInDB],
    status_code=status.HTTP_201_CREATED
)
# @require_permission("permission.create")
def create_permission(
    permission: schemas.PermissionCreate,
    current_user = Depends(get_current_user)
):
    try:
        result = rbac_service.RoleBaseAccessControlService.create_permission(permission)
        return success_response(
            data=result,
            message="Permission created successfully"
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


# ========== ROLE ENDPOINTS ==========
@router.get(
    "/roles",
    response_model=BaseResponse[List[schemas.RoleWithPermissions]]
)
# @require_permission("role.read")
def read_roles(
    skip: int = 0,
    limit: int = 100,
    is_system: Optional[bool] = None,
    is_active: Optional[bool] = None,
    current_user = Depends(get_current_user)
):
    try:
        roles = rbac_service.RoleBaseAccessControlService.get_roles(
            skip=skip, limit=limit, is_system=is_system, is_active=is_active
        )
        return success_response(
            data=roles,
            message="Roles retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


@router.get(
    "/roles/{role_id}",
    response_model=BaseResponse[schemas.RoleWithPermissions]
)
# @require_permission("role.read")
def read_role(
    role_id: int,
    current_user = Depends(get_current_user)
):
    try:
        role = rbac_service.RoleBaseAccessControlService.get_role(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        return success_response(
            data=role,
            message="Role retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


@router.post(
    "/roles",
    response_model=BaseResponse[schemas.RoleWithPermissions],
    status_code=status.HTTP_201_CREATED
)
# @require_permission("role.create")
def create_role(
    role: schemas.RoleCreate,
    current_user = Depends(get_current_user)
):
    try:

        result = rbac_service.RoleBaseAccessControlService.create_role(
            role, created_by=current_user.id
        )
        return success_response(
            data=result,
            message="Role created successfully"
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


@router.put(
    "/roles/{role_id}",
    response_model=BaseResponse[schemas.RoleWithPermissions]
)
# @require_permission("role.update")
def update_role(
    role_id: int,
    role_update: schemas.RoleUpdate,
    current_user=Depends(get_current_user)
):
    try:
        role = rbac_service.RoleBaseAccessControlService.update_role(
            role_id=role_id,
            role_update=role_update,
            updated_by=current_user.id
        )

        return success_response(
            data=role,
            message="Role updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update role error: {e}")
        raise



# ========== USER ROLE MANAGEMENT ==========
@router.get(
    "/users/{user_id}/roles",
    response_model=BaseResponse[List[schemas.RoleInDB]]
)
# @require_permission("user.role.read")
def get_user_roles(
    user_id: int,
    current_user = Depends(get_current_user)
):
    try:
        roles = rbac_service.RoleBaseAccessControlService.get_user_roles(user_id)
        return success_response(
            data=roles,
            message="User roles retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


@router.post(
    "/users/{user_id}/roles/{role_id}",
    response_model=BaseResponse[dict],
    status_code=status.HTTP_201_CREATED
)
# @require_permission("user.role.assign")
def assign_role_to_user(
    user_id: int,
    role_id: int,
    user_role: schemas.UserRoleCreate,
    current_user = Depends(get_current_user)
):
    try:
        rbac_service.RoleBaseAccessControlService.assign_role_to_user(
            user_id=user_id,
            role_id=role_id,
            assigned_by=current_user.id,
            expires_at=user_role.expires_at,
            is_active=user_role.is_active
        )
        return success_response(
            message="Role assigned successfully"
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    response_model=BaseResponse[dict]
)
# @require_permission("user.role.remove")
def remove_role_from_user(
    user_id: int,
    role_id: int,
    current_user = Depends(get_current_user)
):
    try:
        rbac_service.RoleBaseAccessControlService.remove_role_from_user(user_id, role_id)
        return success_response(
            message="Role removed successfully"
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


# ========== CURRENT USER ==========
@router.get(
    "/me/roles",
    response_model=BaseResponse[List[schemas.RoleInDB]]
)
def get_my_roles(
    current_user = Depends(get_current_user)
):
    try:
        logger.info(f"CURRENT USER: {current_user}")
        roles = rbac_service.RoleBaseAccessControlService.get_user_roles(current_user.id)
        return success_response(
            data=roles,
            message="Current user roles retrieved"
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
