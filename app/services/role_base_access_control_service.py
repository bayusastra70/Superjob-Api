from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas import role_base_access_control as schemas



from datetime import datetime

# Import dari model yang spesifik
from app.models.role_base_access_control import Role, Permission
from app.models.user import User

class NotFoundException(Exception):
    pass

class ConflictException(Exception):
    pass

class ForbiddenException(Exception):
    pass

class RoleBaseAccessControlService:
    
    # ========== PERMISSION METHODS ==========
    @staticmethod
    def get_permission(db: Session, permission_id: int) -> Optional[Permission]:
        return db.query(Permission).filter(Permission.id == permission_id).first()
    
    @staticmethod
    def get_permission_by_code(db: Session, code: str) -> Optional[Permission]:
        return db.query(Permission).filter(Permission.code == code).first()
    
    @staticmethod
    def get_permissions(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        module: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Permission]:
        query = db.query(Permission)
        if module:
            query = query.filter(Permission.module == module)
        if is_active is not None:
            query = query.filter(Permission.is_active == is_active)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def create_permission(db: Session, permission: schemas.PermissionCreate) -> Permission:
        # Check if code already exists
        db_permission = RoleBaseAccessControlService.get_permission_by_code(db, permission.code)
        if db_permission:
            raise ConflictException(f"Permission with code '{permission.code}' already exists")
        
        db_permission = Permission(**permission.dict())
        db.add(db_permission)
        db.commit()
        db.refresh(db_permission)
        return db_permission
    
    # ========== ROLE METHODS ==========
    @staticmethod
    def get_role(db: Session, role_id: int) -> Optional[Role]:
        return db.query(Role).filter(Role.id == role_id).first()
    
    @staticmethod
    def get_role_by_name(db: Session, name: str) -> Optional[Role]:
        return db.query(Role).filter(Role.name == name).first()
    
    @staticmethod
    def get_roles(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_system: Optional[bool] = None,
        is_active: Optional[bool] = None
    ) -> List[Role]:
        query = db.query(Role)
        if is_system is not None:
            query = query.filter(Role.is_system == is_system)
        if is_active is not None:
            query = query.filter(Role.is_active == is_active)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def create_role(db: Session, role: schemas.RoleCreate, created_by: int = None) -> Role:
        # Check if name already exists
        db_role = RoleBaseAccessControlService.get_role_by_name(db, role.name)
        if db_role:
            raise ConflictException(f"Role with name '{role.name}' already exists")
        
        # Create role
        db_role = Role(
            name=role.name,
            description=role.description,
            is_system=role.is_system
        )
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        
        # Assign permissions if provided
        if role.permission_ids:
            RoleBaseAccessControlService.assign_permissions_to_role(db, db_role.id, role.permission_ids, created_by)
        
        return db_role
    
    @staticmethod
    def assign_permissions_to_role(
        db: Session, 
        role_id: int, 
        permission_ids: List[int],
        granted_by: Optional[int] = None
    ):
        role = RoleBaseAccessControlService.get_role(db, role_id)
        if not role:
            raise NotFoundException(f"Role with ID {role_id} not found")
        
        # Get existing permissions
        existing_permission_ids = {p.id for p in role.permissions}
        
        for perm_id in permission_ids:
            if perm_id not in existing_permission_ids:
                permission = RoleBaseAccessControlService.get_permission(db, perm_id)
                if not permission:
                    raise NotFoundException(f"Permission with ID {perm_id} not found")
                
                # Add permission to role
                role.permissions.append(permission)
        
        db.commit()
    
    # ========== USER ROLE METHODS ==========
    @staticmethod
    def assign_role_to_user(
        db: Session,
        user_id: int,
        role_id: int,
        assigned_by: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        is_active: bool = True
    ):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found")
        
        role = RoleBaseAccessControlService.get_role(db, role_id)
        if not role:
            raise NotFoundException(f"Role with ID {role_id} not found")
        
        # Check if already assigned
        existing_assignment = db.query(user_roles).filter(
            user_roles.c.user_id == user_id,
            user_roles.c.role_id == role_id
        ).first()
        
        if existing_assignment:
            raise ConflictException(f"User already has role '{role.name}'")
        
        # Assign role
        stmt = user_roles.insert().values(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            expires_at=expires_at,
            is_active=is_active
        )
        db.execute(stmt)
        db.commit()
    
    @staticmethod
    def get_user_roles(db: Session, user_id: int) -> List[Role]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found")
        
        return user.roles
    
    @staticmethod
    def remove_role_from_user(db: Session, user_id: int, role_id: int):
        stmt = user_roles.delete().where(
            user_roles.c.user_id == user_id,
            user_roles.c.role_id == role_id
        )
        result = db.execute(stmt)
        db.commit()
        
        if result.rowcount == 0:
            raise NotFoundException("Role assignment not found")
    
    @staticmethod
    def user_has_role(db: Session, user_id: int, role_name: str) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        return user.has_role(role_name)
    
    @staticmethod
    def user_has_permission(db: Session, user_id: int, permission_code: str) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        return user.has_permission(permission_code)