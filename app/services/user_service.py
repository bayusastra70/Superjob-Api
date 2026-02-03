from loguru import logger
import bcrypt
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status

from app.schemas.user import UserUpdate, UserPasswordUpdate
from app.utils.storage import delete_vercel_blob_sync
from app.services.database import get_db_connection


class UserService:
    def __init__(self):
        pass

    def get_user_profile_with_rbac(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user profile with RBAC information while maintaining backward compatibility.
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT 
                    u.id, 
                    u.email, 
                    u.username, 
                    u.full_name, 
                    u.phone,
                    u.linkedin_url,
                    u.is_active, 
                    u.is_superuser, 
                    u.created_at, 
                    u.updated_at, 
                    uc.company_id,
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
                    ) as default_role_id
                FROM users u
                LEFT JOIN users_companies uc ON u.id = uc.user_id
                WHERE u.id = %s
                """,
                (user_id,),
            )

            user = cursor.fetchone()

            if not user:
                return None

            if hasattr(user, "keys"):
                user_data = {
                    "id": user.get("id"),
                    "email": user.get("email"),
                    "username": user.get("username"),
                    "full_name": user.get("full_name"),
                    "phone": user.get("phone"),
                    "linkedin_url": user.get("linkedin_url"),
                    "role": user.get("role"),
                    "default_role_id": user.get("default_role_id"),
                    "company_id": user.get("company_id"),
                    "is_active": user.get("is_active"),
                    "is_superuser": user.get("is_superuser"),
                    "created_at": user.get("created_at"),
                    "updated_at": user.get("updated_at"),
                }
            else:
                user_data = {
                    "id": user[0],
                    "email": user[1],
                    "username": user[2],
                    "full_name": user[3],
                    "phone": user[4],
                    "linkedin_url": user[5],
                    "is_active": user[6],
                    "is_superuser": user[7],
                    "created_at": user[8],
                    "updated_at": user[9],
                    "company_id": user[10],
                    "role": user[11] if len(user) > 11 else "candidate",
                    "default_role_id": user[12] if len(user) > 12 else 3,
                }

            return user_data

        except Exception as e:
            logger.error(
                f"Error getting user profile with RBAC for user {user_id}: {str(e)}"
            )
            return None
        finally:  # TAMBAHKAN INI
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_user_roles(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all active roles for a user from RBAC system.

        Returns list of role objects with:
        - id: role id
        - name: role name
        - description: role description
        - assigned_at: when role was assigned
        - is_active: if role assignment is active
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT 
                    r.id,
                    r.name,
                    r.description,
                    ur.assigned_at,
                    ur.is_active as role_assignment_active,
                    ur.expires_at,
                    ur.assigned_by
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = %s AND ur.is_active = true
                ORDER BY ur.assigned_at DESC
                """,
                (user_id,),
            )

            roles = cursor.fetchall()

            formatted_roles = []
            for role in roles:
                if hasattr(role, "keys"):
                    formatted_roles.append(
                        {
                            "id": role.get("id"),
                            "name": role.get("name"),
                            "description": role.get("description"),
                            "assigned_at": role.get("assigned_at"),
                            "is_active": role.get("role_assignment_active"),
                            "expires_at": role.get("expires_at"),
                            "assigned_by": role.get("assigned_by"),
                        }
                    )
                else:
                    formatted_roles.append(
                        {
                            "id": role[0],
                            "name": role[1],
                            "description": role[2],
                            "assigned_at": role[3],
                            "is_active": role[4],
                            "expires_at": role[5],
                            "assigned_by": role[6],
                        }
                    )

            return formatted_roles

        except Exception as e:
            logger.error(f"Error getting roles for user {user_id}: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_user_permissions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all permissions for a user from RBAC system.

        Returns list of permission objects with:
        - id: permission id
        - code: permission code
        - name: permission name
        - module: module name
        - action: action type
        - description: permission description
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT DISTINCT
                    p.id,
                    p.code,
                    p.name,
                    p.module,
                    p.action,
                    p.description
                FROM user_roles ur
                JOIN role_permissions rp ON ur.role_id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE ur.user_id = %s 
                    AND ur.is_active = true 
                    AND p.is_active = true
                ORDER BY p.module, p.action
                """,
                (user_id,),
            )

            permissions = cursor.fetchall()

            formatted_permissions = []
            for perm in permissions:
                if hasattr(perm, "keys"):
                    formatted_permissions.append(
                        {
                            "id": perm.get("id"),
                            "code": perm.get("code"),
                            "name": perm.get("name"),
                            "module": perm.get("module"),
                            "action": perm.get("action"),
                            "description": perm.get("description"),
                        }
                    )
                else:
                    formatted_permissions.append(
                        {
                            "id": perm[0],
                            "code": perm[1],
                            "name": perm[2],
                            "module": perm[3],
                            "action": perm[4],
                            "description": perm[5],
                        }
                    )

            return formatted_permissions

        except Exception as e:
            logger.error(f"Error getting permissions for user {user_id}: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def has_permission(self, user_id: int, permission_code: str) -> bool:
        """
        Check if user has a specific permission.

        Args:
            user_id: User ID
            permission_code: Permission code to check (e.g., 'job.create')

        Returns:
            True if user has permission, False otherwise
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT 1
                FROM user_roles ur
                JOIN role_permissions rp ON ur.role_id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE ur.user_id = %s 
                    AND ur.is_active = true 
                    AND p.is_active = true
                    AND p.code = %s
                LIMIT 1
                """,
                (user_id, permission_code),
            )

            has_perm = cursor.fetchone() is not None
            return has_perm

        except Exception as e:
            logger.error(
                f"Error checking permission {permission_code} for user {user_id}: {str(e)}"
            )
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # def update_user_profile(self, user_id: int, update_data: UserUpdate) -> Optional[Dict[str, Any]]:
    #     """
    #     Update user profile data (Non-password fields).

    #     Features:
    #     - Updates standard fields (full_name, phone).
    #     - Updates CV URL for candidates, removing old files if necessary.
    #     - Transactional updates ensuring data integrity.
    #     """
    #     conn = None
    #     cursor = None
    #     try:
    #         conn = get_db_connection()
    #         conn.autocommit = False
    #         cursor = conn.cursor()

    #         # 1. Fetch User
    #         cursor.execute("""
    #             SELECT id, full_name, phone, default_role_id, role, auth_provider
    #             FROM users
    #             WHERE id = %s
    #         """, (user_id,))
    #         user_row = cursor.fetchone()

    #         if not user_row:
    #             return None

    #         # Extract user data
    #         if hasattr(user_row, 'keys'):
    #             user_data = {
    #                 'id': user_row['id'],
    #                 'full_name': user_row['full_name'],
    #                 'phone': user_row['phone'],
    #                 'default_role_id': user_row['default_role_id'],
    #                 'role': user_row['role'],
    #                 'auth_provider': user_row['auth_provider']
    #             }
    #         else:
    #             user_data = {
    #                 'id': user_row[0],
    #                 'full_name': user_row[1],
    #                 'phone': user_row[2],
    #                 'default_role_id': user_row[3],
    #                 'role': user_row[4],
    #                 'auth_provider': user_row[5]
    #             }

    #         # 2. Update Standard Fields
    #         update_fields = []
    #         update_params = []

    #         if update_data.full_name is not None:
    #             update_fields.append("full_name = %s")
    #             update_params.append(update_data.full_name)

    #         if update_data.phone is not None:
    #             update_fields.append("phone = %s")
    #             update_params.append(update_data.phone)

    #         # 3. Handle CV Update (Candidates Only)
    #         is_candidate = (user_data['default_role_id'] == 3) or (user_data['role'] == "candidate")
    #         if is_candidate and update_data.cv_url is not None:
    #             self._handle_candidate_cv_update(cursor, user_id, update_data.cv_url)

    #         # 4. Apply Updates if any
    #         if update_fields:
    #             update_fields.append("updated_at = CURRENT_TIMESTAMP")
    #             update_params.append(user_id)

    #             update_query = f"""
    #                 UPDATE users
    #                 SET {', '.join(update_fields)}
    #                 WHERE id = %s
    #                 RETURNING id, email, username, full_name, phone, role, default_role_id,
    #                           is_active, is_superuser, created_at, updated_at
    #             """
    #             cursor.execute(update_query, update_params)
    #             updated_user = cursor.fetchone()
    #         else:
    #             # No standard fields updated, just fetch current data
    #             cursor.execute("""
    #                 SELECT id, email, username, full_name, phone, role, default_role_id,
    #                        is_active, is_superuser, created_at, updated_at
    #                 FROM users WHERE id = %s
    #             """, (user_id,))
    #             updated_user = cursor.fetchone()

    #         conn.commit()

    #         # Format response
    #         if hasattr(updated_user, 'keys'):
    #             return {
    #                 'id': updated_user['id'],
    #                 'email': updated_user['email'],
    #                 'username': updated_user['username'],
    #                 'full_name': updated_user['full_name'],
    #                 'phone': updated_user['phone'],
    #                 'role': updated_user['role'],
    #                 'default_role_id': updated_user['default_role_id'],
    #                 'is_active': updated_user['is_active'],
    #                 'is_superuser': updated_user['is_superuser'],
    #                 'created_at': updated_user['created_at'],
    #                 'updated_at': updated_user['updated_at']
    #             }
    #         else:
    #             return {
    #                 'id': updated_user[0],
    #                 'email': updated_user[1],
    #                 'username': updated_user[2],
    #                 'full_name': updated_user[3],
    #                 'phone': updated_user[4],
    #                 'role': updated_user[5],
    #                 'default_role_id': updated_user[6],
    #                 'is_active': updated_user[7],
    #                 'is_superuser': updated_user[8],
    #                 'created_at': updated_user[9],
    #                 'updated_at': updated_user[10]
    #             }

    #     except Exception as e:
    #         if conn:
    #             conn.rollback()
    #         logger.error(f"Profile update failed for user {user_id}: {e}")
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail="Failed to update profile"
    #         )
    #     finally:
    #         if cursor:
    #             cursor.close()
    #         if conn:
    #             conn.autocommit = True
    #             conn.close()

    def update_user_profile(
        self, user_id: int, update_data: UserUpdate
    ) -> Optional[Dict[str, Any]]:
        """
        Update user profile data (Non-password fields).

        Features:
        - Updates standard fields (full_name, phone).
        - Updates CV URL for candidates, removing old files if necessary.
        - Transactional updates ensuring data integrity.
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            conn.autocommit = False
            cursor = conn.cursor()

            # 1. Fetch User dengan RBAC support
            cursor.execute(
                """
                SELECT 
                    u.id, 
                    u.full_name, 
                    u.phone, 
                    u.auth_provider,
                    -- Ambil primary role_id
                    COALESCE(
                        (SELECT ur.role_id 
                         FROM user_roles ur 
                         WHERE ur.user_id = u.id 
                         AND ur.is_active = true 
                         ORDER BY ur.assigned_at DESC 
                         LIMIT 1),
                        3
                    ) as primary_role_id
                FROM users u
                WHERE u.id = %s
            """,
                (user_id,),
            )
            user_row = cursor.fetchone()

            if not user_row:
                return None

            # Extract user data
            if hasattr(user_row, "keys"):
                user_data = {
                    "id": user_row["id"],
                    "full_name": user_row["full_name"],
                    "phone": user_row["phone"],
                    "primary_role_id": user_row["primary_role_id"],
                    "auth_provider": user_row["auth_provider"],
                }
            else:
                user_data = {
                    "id": user_row[0],
                    "full_name": user_row[1],
                    "phone": user_row[2],
                    "primary_role_id": user_row[3],
                    "auth_provider": user_row[4],
                }

            # 2. Update Standard Fields
            update_fields = []
            update_params = []

            if update_data.full_name is not None:
                update_fields.append("full_name = %s")
                update_params.append(update_data.full_name)

            if update_data.phone is not None:
                update_fields.append("phone = %s")
                update_params.append(update_data.phone)

            # 3. Handle CV Update (Candidates Only)
            is_candidate = user_data["primary_role_id"] == 3  # candidate role id
            if is_candidate and update_data.cv_url is not None:
                self._handle_candidate_cv_update(cursor, user_id, update_data.cv_url)

            # 4. Apply Updates if any
            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                update_params.append(user_id)

                update_query = f"""
                    UPDATE users 
                    SET {", ".join(update_fields)}
                    WHERE id = %s
                """
                cursor.execute(update_query, update_params)

            conn.commit()

            # 5. Get updated user profile dengan RBAC
            updated_profile = self.get_user_profile_with_rbac(user_id)

            return updated_profile

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Profile update failed for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile",
            )
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.autocommit = True
                conn.close()

    # def _handle_candidate_cv_update(self, cursor, user_id: int, new_cv_url: str):
    #     """
    #     Helper to safely update candidate CV.
    #     - Creates CandidateInfo if missing.
    #     - Deletes old file from storage if URL changes.
    #     - Updates DB record.
    #     """
    #     # Check if candidate_info exists
    #     cursor.execute("""
    #         SELECT cv_url FROM candidate_info WHERE user_id = %s
    #     """, (user_id,))
    #     candidate_info = cursor.fetchone()

    #     if not candidate_info:
    #         # Create new info if it doesn't exist
    #         cursor.execute("""
    #             INSERT INTO candidate_info (user_id, cv_url, created_at, updated_at)
    #             VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    #         """, (user_id, new_cv_url))
    #     else:
    #         # Get current CV URL
    #         current_cv_url = candidate_info['cv_url'] if hasattr(candidate_info, 'keys') else candidate_info[0]

    #         # Check if URL actually changed before doing anything
    #         if current_cv_url and current_cv_url != new_cv_url:
    #             try:
    #                 # TODO: next step - we gonna use Solvera Storage API here
    #                 # Synchronously delete the old file to clean up storage
    #                 delete_vercel_blob_sync(current_cv_url)
    #                 logger.info(f"Deleted old CV for user {user_id}")
    #             except Exception as e:
    #                 # Log but don't block the update
    #                 logger.warning(f"Failed to delete old CV: {e}")

    #         # Update CV URL
    #         cursor.execute("""
    #             UPDATE candidate_info
    #             SET cv_url = %s, updated_at = CURRENT_TIMESTAMP
    #             WHERE user_id = %s
    #         """, (new_cv_url, user_id))

    def _handle_candidate_cv_update(self, cursor, user_id: int, new_cv_url: str):
        """
        Helper to safely update candidate CV.
        - Creates CandidateInfo if missing.
        - Deletes old file from storage if URL changes.
        - Updates DB record.
        """
        # Check if candidate_info exists
        cursor.execute(
            """
            SELECT cv_url FROM candidate_info WHERE user_id = %s
        """,
            (user_id,),
        )
        candidate_info = cursor.fetchone()

        if not candidate_info:
            # Create new info if it doesn't exist
            cursor.execute(
                """
                INSERT INTO candidate_info (user_id, cv_url, created_at, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
                (user_id, new_cv_url),
            )
        else:
            # Get current CV URL
            current_cv_url = (
                candidate_info["cv_url"]
                if hasattr(candidate_info, "keys")
                else candidate_info[0]
            )

            # Check if URL actually changed before doing anything
            if current_cv_url and current_cv_url != new_cv_url:
                try:
                    # TODO: next step - we gonna use Solvera Storage API here
                    # Synchronously delete the old file to clean up storage
                    delete_vercel_blob_sync(current_cv_url)
                    logger.info(f"Deleted old CV for user {user_id}")
                except Exception as e:
                    # Log but don't block the update
                    logger.warning(f"Failed to delete old CV: {e}")

            # Update CV URL
            cursor.execute(
                """
                UPDATE candidate_info 
                SET cv_url = %s, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """,
                (new_cv_url, user_id),
            )

    # def update_user_password(self, user_id: int, password_data: UserPasswordUpdate) -> bool:
    #     """
    #     Update user password with security checks.

    #     Checks:
    #     - User existence.
    #     - Auth provider restriction (Google users cannot change password).
    #     - Current password verification (if one exists).

    #     Returns:
    #     - True on success.
    #     - Raises HTTPException on failure.
    #     """
    #     conn = None
    #     cursor = None
    #     try:
    #         conn = get_db_connection()
    #         conn.autocommit = False
    #         cursor = conn.cursor()

    #         # 1. Fetch User
    #         cursor.execute("""
    #             SELECT id, password_hash, auth_provider
    #             FROM users
    #             WHERE id = %s
    #         """, (user_id,))
    #         user_row = cursor.fetchone()

    #         if not user_row:
    #             return False

    #         # Extract user data
    #         if hasattr(user_row, 'keys'):
    #             password_hash = user_row['password_hash']
    #             auth_provider = user_row['auth_provider']
    #         else:
    #             password_hash = user_row[1]
    #             auth_provider = user_row[2]

    #         # 2. Security Check: Google Users
    #         # Users authenticated via Google typically don't have a password to update
    #         # and should manage security via Google.
    #         if auth_provider == "google":
    #             raise HTTPException(
    #                 status_code=status.HTTP_403_FORBIDDEN,
    #                 detail="Google users cannot update their password."
    #             )

    #         # 3. Verify Current Password
    #         # If the user has a password set, we MUST verify it.
    #         if password_hash:
    #             is_password_valid = bcrypt.checkpw(
    #                 password_data.current_password.encode('utf-8'),
    #                 password_hash.encode('utf-8')
    #             )
    #             if not is_password_valid:
    #                 raise HTTPException(
    #                     status_code=status.HTTP_400_BAD_REQUEST,
    #                     detail="Incorrect current password"
    #                 )

    #         # 4. Hash & Set New Password
    #         salt = bcrypt.gensalt()
    #         hashed = bcrypt.hashpw(password_data.new_password.encode('utf-8'), salt)
    #         new_password_hash = hashed.decode('utf-8')

    #         # 5. Update Password
    #         cursor.execute("""
    #             UPDATE users
    #             SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
    #             WHERE id = %s
    #         """, (new_password_hash, user_id))

    #         conn.commit()
    #         logger.info(f"Password updated for user {user_id}")
    #         return True

    #     except HTTPException:
    #         if conn:
    #             conn.rollback()
    #         raise
    #     except Exception as e:
    #         if conn:
    #             conn.rollback()
    #         logger.error(f"Password update failed for user {user_id}: {e}")
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail="Failed to update password"
    #         )
    #     finally:
    #         if cursor:
    #             cursor.close()
    #         if conn:
    #             conn.autocommit = True
    #             conn.close()

    def update_user_password(
        self, user_id: int, password_data: UserPasswordUpdate
    ) -> bool:
        """
        Update user password with security checks.

        Checks:
        - User existence.
        - Auth provider restriction (Google users cannot change password).
        - Current password verification (if one exists).

        Returns:
        - True on success.
        - Raises HTTPException on failure.
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            conn.autocommit = False
            cursor = conn.cursor()

            # 1. Fetch User
            cursor.execute(
                """
                SELECT id, password_hash, auth_provider
                FROM users 
                WHERE id = %s
            """,
                (user_id,),
            )
            user_row = cursor.fetchone()

            if not user_row:
                return False

            # Extract user data
            if hasattr(user_row, "keys"):
                password_hash = user_row["password_hash"]
                auth_provider = user_row["auth_provider"]
            else:
                password_hash = user_row[1]
                auth_provider = user_row[2]

            # 2. Security Check: Google Users
            # Users authenticated via Google typically don't have a password to update
            # and should manage security via Google.
            if auth_provider == "google":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Google users cannot update their password.",
                )

            # 3. Verify Current Password
            # If the user has a password set, we MUST verify it.
            if password_hash:
                is_password_valid = bcrypt.checkpw(
                    password_data.current_password.encode("utf-8"),
                    password_hash.encode("utf-8"),
                )
                if not is_password_valid:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Incorrect current password",
                    )

            # 4. Hash & Set New Password
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_data.new_password.encode("utf-8"), salt)
            new_password_hash = hashed.decode("utf-8")

            # 5. Update Password
            cursor.execute(
                """
                UPDATE users 
                SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """,
                (new_password_hash, user_id),
            )

            conn.commit()
            logger.info(
                f"User password changed",
                event="password_changed",
                user={"id": user_id, "role": None},
            )
            return True

        except HTTPException:
            if conn:
                conn.rollback()
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Password update failed for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password",
            )
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.autocommit = True
                conn.close()

    def can_access_profile(
        self, current_user_id: int, current_user_role: str, target_user_id: int
    ) -> bool:
        """
        Check if current user can access target user's profile.

        Access Rules:
        - Self: Always allowed
        - Admin: Always allowed
        - Employer: Only if candidate applied to their company's jobs
        """
        if current_user_id == target_user_id:
            return True

        if current_user_role == "admin":
            return True

        if current_user_role == "employer":
            return self._has_candidate_applied_to_company(
                target_user_id, current_user_id
            )

        return False

    def _has_candidate_applied_to_company(
        self, candidate_id: int, employer_id: int
    ) -> bool:
        """
        Check if candidate has ANY application to employer's company.
        Returns True if candidate has applied to any job at employer's company.
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1 
                    FROM applications a
                    JOIN jobs j ON a.job_id = j.id
                    JOIN users_companies uc ON j.company_id = uc.company_id
                    WHERE a.candidate_id = %s 
                    AND uc.user_id = %s
                ) as has_applied
            """,
                (candidate_id, employer_id),
            )

            result = cursor.fetchone()
            return result.get("has_applied", False) if result else False

        except Exception as e:
            logger.error(f"Error checking candidate application: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_user_profile_with_cv(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user profile including CV extracted data.
        Returns simplified structure with essential fields only.
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT 
                    u.id, 
                    u.email, 
                    u.full_name, 
                    u.phone,
                    u.linkedin_url,
                    ci.cv_url,
                    ci.cv_extracted_profile,
                    ci.cv_extracted_experience,
                    ci.cv_extracted_education,
                    ci.cv_extracted_skills,
                    ci.cv_extracted_languages,
                    ci.cv_extracted_certifications,
                    COALESCE(
                        (SELECT r.name 
                        FROM user_roles ur 
                        JOIN roles r ON ur.role_id = r.id 
                        WHERE ur.user_id = u.id 
                        AND ur.is_active = true 
                        ORDER BY ur.assigned_at DESC 
                        LIMIT 1),
                        'candidate'
                    ) as role
                FROM users u
                LEFT JOIN candidate_info ci ON u.id = ci.user_id
                WHERE u.id = %s
            """,
                (user_id,),
            )

            user = cursor.fetchone()

            if not user:
                return None

            profile = (
                user.get("cv_extracted_profile") if hasattr(user, "get") else user[6]
            )

            user_data = {
                "id": user.get("id") if hasattr(user, "get") else user[0],
                "email": user.get("email") if hasattr(user, "get") else user[1],
                "full_name": user.get("full_name") if hasattr(user, "get") else user[2],
                "phone": user.get("phone") if hasattr(user, "get") else user[3],
                "linkedin_url": user.get("linkedin_url")
                if hasattr(user, "get")
                else user[4],
                "cv_url": user.get("cv_url") if hasattr(user, "get") else user[5],
                "role": user.get("role")
                if hasattr(user, "get")
                else user[12]
                if len(user) > 12
                else "candidate",
            }

            if profile:
                user_data["summary"] = profile.get("summary")

            user_data["skills"] = (
                user.get("cv_extracted_skills")
                if hasattr(user, "get")
                else user[9] or []
            )
            user_data["languages"] = (
                user.get("cv_extracted_languages")
                if hasattr(user, "get")
                else user[10] or []
            )
            user_data["experience"] = (
                user.get("cv_extracted_experience")
                if hasattr(user, "get")
                else user[7] or []
            )
            user_data["education"] = (
                user.get("cv_extracted_education")
                if hasattr(user, "get")
                else user[8] or []
            )
            user_data["certifications"] = (
                user.get("cv_extracted_certifications")
                if hasattr(user, "get")
                else user[11] or []
            )

            return user_data

        except Exception as e:
            logger.error(f"Error getting user profile with CV: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def update_user_cv_data(self, user_id: int, cv_data: Dict[str, Any]) -> bool:
        """
        Update CV extracted data for a user.
        Only updates fields that are provided in cv_data (partial update).
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            conn.autocommit = False
            cursor = conn.cursor()

            from datetime import datetime
            import json

            # Build dynamic UPDATE query based on provided fields
            update_fields = []
            update_params = []

            if "profile" in cv_data:
                # Fetch existing profile data to merge with new data
                cursor.execute(
                    "SELECT cv_extracted_profile FROM candidate_info WHERE user_id = %s",
                    (user_id,),
                )
                existing = cursor.fetchone()

                # Merge existing profile with new profile data
                existing_profile = {}
                if existing and existing.get("cv_extracted_profile"):
                    existing_profile = existing["cv_extracted_profile"]

                # Merge: new data takes precedence over existing
                merged_profile = {**existing_profile, **cv_data["profile"]}

                update_fields.append("cv_extracted_profile = %s")
                update_params.append(json.dumps(merged_profile))

            if "experience" in cv_data:
                update_fields.append("cv_extracted_experience = %s")
                update_params.append(json.dumps(cv_data["experience"]))

            if "education" in cv_data:
                update_fields.append("cv_extracted_education = %s")
                update_params.append(json.dumps(cv_data["education"]))

            if "skills" in cv_data:
                update_fields.append("cv_extracted_skills = %s")
                update_params.append(cv_data["skills"])

            if "languages" in cv_data:
                update_fields.append("cv_extracted_languages = %s")
                update_params.append(cv_data["languages"])

            if "certifications" in cv_data:
                update_fields.append("cv_extracted_certifications = %s")
                update_params.append(json.dumps(cv_data["certifications"]))

            # Always update timestamp and status
            update_fields.append("cv_extracted_at = %s")
            update_params.append(datetime.utcnow())
            update_fields.append("cv_extraction_status = %s")
            update_params.append("completed")
            update_fields.append("cv_extraction_error = NULL")

            # Add user_id for WHERE clause
            update_params.append(user_id)

            if update_fields:
                update_query = f"""
                    UPDATE candidate_info
                    SET {", ".join(update_fields)}
                    WHERE user_id = %s
                """
                cursor.execute(update_query, update_params)

            conn.commit()
            logger.info(
                f"CV data updated for user {user_id} with fields: {list(cv_data.keys())}"
            )
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error updating CV data for user {user_id}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.autocommit = True
                conn.close()

    async def upload_cv_file(self, user_id: int, cv_file) -> tuple[str, str]:
        """
        Upload CV file to Solvera Storage.
        Returns: (cv_url, storage_id) - both needed for rollback
        """
        from app.utils.solvera_storage import (
            solvera_storage,
            StorageFolder,
            UploaderName,
        )

        try:
            upload_result = await solvera_storage.upload_file(
                file=cv_file,
                folder=StorageFolder.CANDIDATE_CV,
                allowed_types=["application/pdf"],
                max_size_mb=10,
                uploader_name=UploaderName.SUPERJOB_SERVICE,
            )
            cv_url = upload_result["url"]
            storage_id = upload_result["id"]
            logger.info(f"CV uploaded for user {user_id}: {cv_url} (id: {storage_id})")
            return cv_url, storage_id

        except Exception as e:
            logger.error(f"Failed to upload CV file for user {user_id}: {e}")
            raise Exception(f"Failed to upload CV file: {str(e)}")

    async def delete_cv_file(self, storage_id: str) -> None:
        """
        Delete CV file from Solvera Storage.
        Used for cleanup on rollback.
        """
        from app.utils.solvera_storage import solvera_storage

        try:
            await solvera_storage.delete_file(storage_id)
            logger.info(f"CV file deleted from storage: {storage_id}")
        except Exception as e:
            # Log error but don't raise - cleanup failure shouldn't fail the request
            logger.error(f"Failed to delete CV file {storage_id} from storage: {e}")

    def update_user_profile(self, user_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Update user profile data in users table.
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            conn.autocommit = False
            cursor = conn.cursor()

            update_fields = []
            update_params = []

            if update_data.get("full_name") is not None:
                update_fields.append("full_name = %s")
                update_params.append(update_data["full_name"])

            if update_data.get("phone") is not None:
                update_fields.append("phone = %s")
                update_params.append(update_data["phone"])

            if update_data.get("linkedin_url") is not None:
                update_fields.append("linkedin_url = %s")
                update_params.append(update_data["linkedin_url"])

            if update_data.get("cv_url") is not None:
                # Update cv_url in candidate_info table
                cursor.execute(
                    """
                    SELECT cv_url FROM candidate_info WHERE user_id = %s
                """,
                    (user_id,),
                )
                existing = cursor.fetchone()

                if existing:
                    if existing.get("cv_url") != update_data["cv_url"]:
                        cursor.execute(
                            """
                            UPDATE candidate_info
                            SET cv_url = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s
                        """,
                            (update_data["cv_url"], user_id),
                        )
                else:
                    cursor.execute(
                        """
                        INSERT INTO candidate_info (user_id, cv_url, created_at, updated_at)
                        VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                        (user_id, update_data["cv_url"]),
                    )

            if update_fields:
                # Add updated_at and user_id for WHERE clause
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                update_params.append(user_id)

                update_query = f"""
                    UPDATE users
                    SET {", ".join(update_fields)}
                    WHERE id = %s
                """
                cursor.execute(update_query, update_params)

            conn.commit()
            logger.info(f"User profile updated for user {user_id}")
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error updating user profile for user {user_id}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.autocommit = True
                conn.close()


# Global singleton instance
user_service = UserService()
