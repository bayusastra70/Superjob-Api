from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas import role_base_access_control as schemas
from app.services import role_base_access_control_service as rbac_service
from app.core.security import get_current_user, require_permission

from app.schemas.response import BaseResponse
from app.utils.response import success_response

router = APIRouter()


# ========== PERMISSION ENDPOINTS ==========
@router.get(
    "/permissions",
    response_model=BaseResponse[List[schemas.PermissionInDB]]
)
@require_permission("permission.read")
def read_permissions(
    skip: int = 0,
    limit: int = 100,
    module: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(deps.get_db),
    current_user = Depends(get_current_user)
):
    permissions = rbac_service.RBACService.get_permissions(
        db, skip=skip, limit=limit, module=module, is_active=is_active
    )
    return success_response(
        data=permissions,
        message="Permissions retrieved successfully"
    )


@router.post(
    "/permissions",
    response_model=BaseResponse[schemas.PermissionInDB],
    status_code=status.HTTP_201_CREATED
)
@require_permission("permission.create")
def create_permission(
    permission: schemas.PermissionCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(get_current_user)
):
    result = rbac_service.RBACService.create_permission(db, permission)
    return success_response(
        data=result,
        message="Permission created successfully"
    )


# ========== ROLE ENDPOINTS ==========
@router.get(
    "/roles",
    response_model=BaseResponse[List[schemas.RoleWithPermissions]]
)
@require_permission("role.read")
def read_roles(
    skip: int = 0,
    limit: int = 100,
    is_system: Optional[bool] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(deps.get_db),
    current_user = Depends(get_current_user)
):
    roles = rbac_service.RBACService.get_roles(
        db, skip=skip, limit=limit, is_system=is_system, is_active=is_active
    )
    return success_response(
        data=roles,
        message="Roles retrieved successfully"
    )


@router.get(
    "/roles/{role_id}",
    response_model=BaseResponse[schemas.RoleWithPermissions]
)
@require_permission("role.read")
def read_role(
    role_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(get_current_user)
):
    role = rbac_service.RBACService.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return success_response(
        data=role,
        message="Role retrieved successfully"
    )


@router.post(
    "/roles",
    response_model=BaseResponse[schemas.RoleWithPermissions],
    status_code=status.HTTP_201_CREATED
)
@require_permission("role.create")
def create_role(
    role: schemas.RoleCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(get_current_user)
):
    result = rbac_service.RBACService.create_role(
        db, role, created_by=current_user.id
    )
    return success_response(
        data=result,
        message="Role created successfully"
    )


@router.put(
    "/roles/{role_id}",
    response_model=BaseResponse[schemas.RoleWithPermissions]
)
@require_permission("role.update")
def update_role(
    role_id: int,
    role_update: schemas.RoleUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(get_current_user)
):
    role = rbac_service.RBACService.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role.is_system and role_update.name and role_update.name != role.name:
        raise HTTPException(status_code=400, detail="Cannot rename system roles")

    update_data = role_update.dict(exclude_unset=True, exclude={"permission_ids"})
    for field, value in update_data.items():
        setattr(role, field, value)

    if role_update.permission_ids is not None:
        role.permissions.clear()
        if role_update.permission_ids:
            rbac_service.RBACService.assign_permissions_to_role(
                db, role_id, role_update.permission_ids, current_user.id
            )

    db.commit()
    db.refresh(role)

    return success_response(
        data=role,
        message="Role updated successfully"
    )


# ========== USER ROLE MANAGEMENT ==========
@router.get(
    "/users/{user_id}/roles",
    response_model=BaseResponse[List[schemas.RoleInDB]]
)
@require_permission("user.role.read")
def get_user_roles(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(get_current_user)
):
    roles = rbac_service.RBACService.get_user_roles(db, user_id)
    return success_response(
        data=roles,
        message="User roles retrieved successfully"
    )


@router.post(
    "/users/{user_id}/roles/{role_id}",
    response_model=BaseResponse[dict],
    status_code=status.HTTP_201_CREATED
)
@require_permission("user.role.assign")
def assign_role_to_user(
    user_id: int,
    role_id: int,
    user_role: schemas.UserRoleCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(get_current_user)
):
    rbac_service.RBACService.assign_role_to_user(
        db,
        user_id=user_id,
        role_id=role_id,
        assigned_by=current_user.id,
        expires_at=user_role.expires_at,
        is_active=user_role.is_active
    )
    return success_response(
        message="Role assigned successfully"
    )


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    response_model=BaseResponse[dict]
)
@require_permission("user.role.remove")
def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(get_current_user)
):
    rbac_service.RBACService.remove_role_from_user(db, user_id, role_id)
    return success_response(
        message="Role removed successfully"
    )


# ========== CURRENT USER ==========
@router.get(
    "/me/roles",
    response_model=BaseResponse[List[schemas.RoleInDB]]
)
def get_my_roles(
    db: Session = Depends(deps.get_db),
    current_user = Depends(get_current_user)
):
    return success_response(
        data=current_user.roles,
        message="Current user roles retrieved"
    )


@router.get(
    "/me/permissions",
    response_model=BaseResponse[dict]
)
def get_my_permissions(
    current_user = Depends(get_current_user)
):
    return success_response(
        data={"permissions": current_user.get_permissions()},
        message="Current user permissions retrieved"
    )


@router.get(
    "/check-permission/{permission_code}",
    response_model=BaseResponse[dict]
)
def check_permission(
    permission_code: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(get_current_user)
):
    has_perm = rbac_service.RBACService.user_has_permission(
        db, current_user.id, permission_code
    )
    return success_response(
        data={
            "has_permission": has_perm,
            "permission_code": permission_code
        },
        message="Permission checked successfully"
    )
