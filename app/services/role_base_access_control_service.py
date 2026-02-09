from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas import role_base_access_control as schemas

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database import get_db_connection, release_connection



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
        skip: int = 0,
        limit: int = 100,
        module: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Permission]:

        conn = None
        cursor = None

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM permissions WHERE 1=1"
            params = []

            if module:
                query += " AND module = %s"
                params.append(module)

            if is_active is not None:
                query += " AND is_active = %s"
                params.append(is_active)

            query += " ORDER BY id OFFSET %s LIMIT %s"
            params.extend([skip, limit])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return rows

        except Exception as e:
            logger.error(f"Error get_permissions: {e}")
            raise

        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)
    
    @staticmethod
    def create_permission(permission: schemas.PermissionCreate) -> Permission:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if permission code already exists
            cursor.execute(
                "SELECT id FROM permissions WHERE code = %s",
                (permission.code,)
            )
            existing = cursor.fetchone()

            if existing:
                raise ConflictException(
                    f"Permission with code '{permission.code}' already exists"
                )

            # Insert new permission
            insert_query = """
                INSERT INTO permissions (code, name, module, description, is_active)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, code, name, module, description, is_active
            """

            cursor.execute(
                insert_query,
                (
                    permission.code,
                    permission.name,
                    permission.module,
                    permission.description,
                    permission.is_active,
                )
            )

            new_permission = cursor.fetchone()
            conn.commit()

            return Permission(
                id=new_permission[0],
                code=new_permission[1],
                name=new_permission[2],
                module=new_permission[3],
                description=new_permission[4],
                is_active=new_permission[5],
            )

        except Exception as e:
            conn.rollback()
            raise

        finally:
            cursor.close()
            release_connection(conn)
    
    # ========== ROLE METHODS ==========
    @staticmethod
    def get_role(role_id: int) -> Optional[dict]:
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    r.id,
                    r.name,
                    r.description,
                    r.is_system,
                    r.is_active,
                    r.created_at,
                    r.updated_at
                FROM roles r
                WHERE r.id = %s
                LIMIT 1
                """,
                (role_id,)
            )

            row = cursor.fetchone()
            if not row:
                return None

            # 🔹 ambil permissions role
            cursor.execute(
                """
                SELECT
                    p.id,
                    p.code,
                    p.name,
                    p.description,
                    p.module,
                    p.action,
                    p.is_active,
                    p.created_at
                FROM permissions p
                JOIN role_permissions rp ON rp.permission_id = p.id
                WHERE rp.role_id = %s
                """,
                (role_id,)
            )
            permissions = cursor.fetchall()

            return {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "is_system": row["is_system"],
                "is_active": row["is_active"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "permissions": permissions or []
            }

        finally:
            cursor.close()
            release_connection(conn)

    
    @staticmethod
    def get_role_by_name(db: Session, name: str) -> Optional[Role]:
        return db.query(Role).filter(Role.name == name).first()
    
    @staticmethod
    def get_roles(
        skip: int = 0,
        limit: int = 100,
        is_system: Optional[bool] = None,
        is_active: Optional[bool] = None
    ):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    r.id,
                    r.name,
                    r.description,
                    r.is_system,
                    r.is_active,
                    r.created_at,
                    r.updated_at
                FROM roles r
                WHERE 1=1
            """
            params = []

            if is_system is not None:
                query += " AND r.is_system = %s"
                params.append(is_system)

            if is_active is not None:
                query += " AND r.is_active = %s"
                params.append(is_active)

            query += " ORDER BY r.id OFFSET %s LIMIT %s"
            params.extend([skip, limit])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            roles = []
            for row in rows:
                role_id = row["id"]

                # 🔹 ambil permissions per role
                cursor.execute(
                    """
                    SELECT
                        p.id,
                        p.code,
                        p.name,
                        p.description,
                        p.module,
                        p.action,
                        p.is_active,
                        p.created_at
                    FROM permissions p
                    JOIN role_permissions rp ON rp.permission_id = p.id
                    WHERE rp.role_id = %s
                    """,
                    (role_id,)
                )
                permissions = cursor.fetchall()

                roles.append({
                    "id": role_id,
                    "name": row["name"],
                    "description": row["description"],
                    "is_system": row["is_system"],
                    "is_active": row["is_active"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "permissions": permissions or []
                })

            return roles

        except Exception:
            raise

        finally:
            cursor.close()
            release_connection(conn)
    
    @staticmethod
    def create_role(role: schemas.RoleCreate, created_by: int = None) -> Role:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 1 Check if role name already exists
            cursor.execute(
                "SELECT id FROM roles WHERE name = %s LIMIT 1",
                (role.name,)
            )
            if cursor.fetchone():
                raise ConflictException(f"Role with name '{role.name}' already exists")

            # 2 Insert role
            insert_role_query = """
                INSERT INTO roles (
                    name,
                    description,
                    is_system,
                    is_active,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, %s, TRUE, NOW(), NOW())
                RETURNING id, name, description, is_system, is_active, created_at, updated_at
            """

            cursor.execute(
                insert_role_query,
                (
                    role.name,
                    role.description,
                    role.is_system,
                )
            )

            row = cursor.fetchone()
            conn.commit()

            db_role = Role(
                id=row[0],
                name=row[1],
                description=row[2],
                is_system=row[3],
                is_active=row[4],
                created_at=row[5],
                updated_at=row[6],
            )

            # # 3 Assign permissions (optional)
            # if role.permission_ids:
            #     RoleBaseAccessControlService.assign_permissions_to_role(
            #         role_id=db_role.id,
            #         permission_ids=role.permission_ids,
            #         created_by=created_by,
            #     )

            return db_role

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            release_connection(conn)

    
    @staticmethod
    def assign_permissions_to_role(
        role_id: int,
        permission_ids: List[int],
        granted_by: Optional[int] = None
    ):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 1️⃣ Check role exists
            cursor.execute(
                "SELECT id FROM roles WHERE id = %s LIMIT 1",
                (role_id,)
            )
            if not cursor.fetchone():
                raise NotFoundException(f"Role with ID {role_id} not found")

            # 2️⃣ Get existing permission_ids for this role
            cursor.execute(
                "SELECT permission_id FROM role_permissions WHERE role_id = %s",
                (role_id,)
            )
            existing_permission_ids = {row[0] for row in cursor.fetchall()}

            # 3️⃣ Loop permissions
            for perm_id in permission_ids:
                # 3a️⃣ Skip if already assigned
                if perm_id in existing_permission_ids:
                    continue

                # 3b️⃣ Check permission exists
                cursor.execute(
                    "SELECT id FROM permissions WHERE id = %s LIMIT 1",
                    (perm_id,)
                )
                if not cursor.fetchone():
                    raise NotFoundException(f"Permission with ID {perm_id} not found")

                # 3c️⃣ Insert role_permission
                cursor.execute(
                    """
                    INSERT INTO role_permissions (
                        role_id,
                        permission_id,
                        granted_by,
                        created_at
                    )
                    VALUES (%s, %s, %s, NOW())
                    """,
                    (role_id, perm_id, granted_by)
                )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            release_connection(conn)

    
    # ========== USER ROLE METHODS ==========
    @staticmethod
    def assign_role_to_user(
        user_id: int,
        role_id: int,
        assigned_by: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        is_active: bool = True
    ):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 1️⃣ Check user exists
            cursor.execute(
                "SELECT id FROM users WHERE id = %s LIMIT 1",
                (user_id,)
            )
            if not cursor.fetchone():
                raise NotFoundException(f"User with ID {user_id} not found")

            # 2️⃣ Check role exists
            cursor.execute(
                "SELECT id, name FROM roles WHERE id = %s LIMIT 1",
                (role_id,)
            )
            role = cursor.fetchone()
            if not role:
                raise NotFoundException(f"Role with ID {role_id} not found")

            role_name = role[1]

            # 3️⃣ Check if already assigned (active)
            cursor.execute(
                """
                SELECT 1
                FROM user_roles
                WHERE user_id = %s
                AND role_id = %s
                AND is_active = TRUE
                LIMIT 1
                """,
                (user_id, role_id)
            )
            if cursor.fetchone():
                raise ConflictException(f"User already has role '{role_name}'")

            # 4️⃣ Insert role assignment
            cursor.execute(
                """
                INSERT INTO user_roles (
                    user_id,
                    role_id,
                    assigned_by,
                    expires_at,
                    is_active,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, NOW())
                """,
                (
                    user_id,
                    role_id,
                    assigned_by,
                    expires_at,
                    is_active
                )
            )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            release_connection(conn)

    
    @staticmethod
    def get_user_roles(user_id: int) -> List[dict]:
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 1️⃣ Ambil roles user
            cursor.execute(
                """
                SELECT
                    r.id,
                    r.name,
                    r.description,
                    r.is_system,
                    r.is_active,
                    r.created_at,
                    r.updated_at
                FROM roles r
                JOIN user_roles ur ON ur.role_id = r.id
                WHERE ur.user_id = %s
                AND ur.is_active = TRUE
                AND r.is_active = TRUE
                ORDER BY r.name
                """,
                (user_id,)
            )

            role_rows = cursor.fetchall()
            if not role_rows:
                return []

            roles = []

            for role in role_rows:
                role_id = role["id"]

                # 2️⃣ Ambil permissions per role
                cursor.execute(
                    """
                    SELECT
                        p.id,
                        p.code,
                        p.name,
                        p.description,
                        p.module,
                        p.action,
                        p.is_active,
                        p.created_at
                    FROM permissions p
                    JOIN role_permissions rp ON rp.permission_id = p.id
                    WHERE rp.role_id = %s
                    AND p.is_active = TRUE
                    """,
                    (role_id,)
                )

                permissions = cursor.fetchall()

                roles.append({
                    "id": role["id"],
                    "name": role["name"],
                    "description": role["description"],
                    "is_system": role["is_system"],
                    "is_active": role["is_active"],
                    "created_at": role["created_at"],
                    "updated_at": role["updated_at"],
                    "permissions": permissions or []
                })

            return roles

        finally:
            cursor.close()
            release_connection(conn)


    
    @staticmethod
    def remove_role_from_user(user_id: int, role_id: int):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Optional: check assignment exists dulu
            cursor.execute(
                """
                SELECT 1
                FROM user_roles
                WHERE user_id = %s AND role_id = %s
                LIMIT 1
                """,
                (user_id, role_id)
            )

            if not cursor.fetchone():
                raise NotFoundException("Role assignment not found")

            # Delete assignment
            cursor.execute(
                """
                DELETE FROM user_roles
                WHERE user_id = %s AND role_id = %s
                """,
                (user_id, role_id)
            )

            conn.commit()

        finally:
            cursor.close()
            release_connection(conn)

    
    @staticmethod
    def user_has_role(user_id: int, role_name: str) -> bool:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT 1
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                AND r.name = %s
                AND ur.is_active = TRUE
                LIMIT 1
                """,
                (user_id, role_name)
            )

            return cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"user_has_role error: {e}")
            return False

        finally:
            cursor.close()
            release_connection(conn)

    
    @staticmethod
    def user_has_permission(user_id: int, permission_code: str) -> bool:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT 1
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                JOIN role_permissions rp ON rp.role_id = r.id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE ur.user_id = %s
                AND p.code = %s
                AND ur.is_active = TRUE
                AND r.is_active = TRUE
                AND p.is_active = TRUE
                LIMIT 1
                """,
                (user_id, permission_code)
            )

            return cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"user_has_permission error: {e}")
            return False

        finally:
            cursor.close()
            release_connection(conn)
