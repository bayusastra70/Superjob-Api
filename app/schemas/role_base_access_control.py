from pydantic import BaseModel, validator
from datetime import datetime
from typing import List, Optional


# ========== PERMISSION SCHEMAS ==========
class PermissionBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    module: str
    action: str

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class PermissionInDB(PermissionBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== ROLE SCHEMAS ==========
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_system: bool = False

class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = None

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[int]] = None

class RoleInDB(RoleBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    permissions: List[PermissionInDB] = []
    
    class Config:
        from_attributes = True


# ========== USER ROLE ASSIGNMENT SCHEMAS ==========
class UserRoleBase(BaseModel):
    user_id: int
    role_id: int
    expires_at: Optional[datetime] = None
    is_active: bool = True

class UserRoleCreate(UserRoleBase):
    assigned_by: Optional[int] = None

class UserRoleUpdate(BaseModel):
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None

class UserRoleInDB(UserRoleBase):
    assigned_at: datetime
    assigned_by: Optional[int]
    
    class Config:
        from_attributes = True


# ========== COMPOSITE SCHEMAS ==========
class UserWithRoles(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    roles: List[RoleInDB] = []
    permissions: List[str] = []
    
    class Config:
        from_attributes = True

class RoleWithPermissions(RoleInDB):
    permissions: List[PermissionInDB] = []
    
    class Config:
        from_attributes = True