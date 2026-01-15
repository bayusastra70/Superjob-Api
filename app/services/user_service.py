
import logging
import bcrypt
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

from app.schemas.user import UserUpdate, UserPasswordUpdate
from app.utils.storage import delete_vercel_blob_sync
from app.services.database import get_db_connection

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self):
        pass
    
    def update_user_profile(self, user_id: int, update_data: UserUpdate) -> Optional[Dict[str, Any]]:
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

            # 1. Fetch User
            cursor.execute("""
                SELECT id, full_name, phone, default_role_id, role, auth_provider
                FROM users 
                WHERE id = %s
            """, (user_id,))
            user_row = cursor.fetchone()
            
            if not user_row:
                return None

            # Extract user data
            if hasattr(user_row, 'keys'):
                user_data = {
                    'id': user_row['id'],
                    'full_name': user_row['full_name'],
                    'phone': user_row['phone'],
                    'default_role_id': user_row['default_role_id'],
                    'role': user_row['role'],
                    'auth_provider': user_row['auth_provider']
                }
            else:
                user_data = {
                    'id': user_row[0],
                    'full_name': user_row[1],
                    'phone': user_row[2],
                    'default_role_id': user_row[3],
                    'role': user_row[4],
                    'auth_provider': user_row[5]
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
            is_candidate = (user_data['default_role_id'] == 3) or (user_data['role'] == "candidate")
            if is_candidate and update_data.cv_url is not None:
                self._handle_candidate_cv_update(cursor, user_id, update_data.cv_url)

            # 4. Apply Updates if any
            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                update_params.append(user_id)
                
                update_query = f"""
                    UPDATE users 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                    RETURNING id, email, username, full_name, phone, role, default_role_id
                """
                cursor.execute(update_query, update_params)
                updated_user = cursor.fetchone()
            else:
                # No standard fields updated, just fetch current data
                cursor.execute("""
                    SELECT id, email, username, full_name, phone, role, default_role_id
                    FROM users WHERE id = %s
                """, (user_id,))
                updated_user = cursor.fetchone()

            conn.commit()
            
            # Format response
            if hasattr(updated_user, 'keys'):
                return {
                    'id': updated_user['id'],
                    'email': updated_user['email'],
                    'username': updated_user['username'],
                    'full_name': updated_user['full_name'],
                    'phone': updated_user['phone'],
                    'role': updated_user['role'],
                    'default_role_id': updated_user['default_role_id']
                }
            else:
                return {
                    'id': updated_user[0],
                    'email': updated_user[1],
                    'username': updated_user[2],
                    'full_name': updated_user[3],
                    'phone': updated_user[4],
                    'role': updated_user[5],
                    'default_role_id': updated_user[6]
                }

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Profile update failed for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.autocommit = True
                conn.close()

    def _handle_candidate_cv_update(self, cursor, user_id: int, new_cv_url: str):
        """
        Helper to safely update candidate CV.
        - Creates CandidateInfo if missing.
        - Deletes old file from storage if URL changes.
        - Updates DB record.
        """
        # Check if candidate_info exists
        cursor.execute("""
            SELECT cv_url FROM candidate_info WHERE user_id = %s
        """, (user_id,))
        candidate_info = cursor.fetchone()
        
        if not candidate_info:
            # Create new info if it doesn't exist
            cursor.execute("""
                INSERT INTO candidate_info (user_id, cv_url, created_at, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (user_id, new_cv_url))
        else:
            # Get current CV URL
            current_cv_url = candidate_info['cv_url'] if hasattr(candidate_info, 'keys') else candidate_info[0]
            
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
            cursor.execute("""
                UPDATE candidate_info 
                SET cv_url = %s, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (new_cv_url, user_id))

    def update_user_password(self, user_id: int, password_data: UserPasswordUpdate) -> bool:
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
            cursor.execute("""
                SELECT id, password_hash, auth_provider
                FROM users 
                WHERE id = %s
            """, (user_id,))
            user_row = cursor.fetchone()
            
            if not user_row:
                return False

            # Extract user data
            if hasattr(user_row, 'keys'):
                password_hash = user_row['password_hash']
                auth_provider = user_row['auth_provider']
            else:
                password_hash = user_row[1]
                auth_provider = user_row[2]

            # 2. Security Check: Google Users
            # Users authenticated via Google typically don't have a password to update
            # and should manage security via Google.
            if auth_provider == "google":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Google users cannot update their password."
                )

            # 3. Verify Current Password
            # If the user has a password set, we MUST verify it.
            if password_hash:
                is_password_valid = bcrypt.checkpw(
                    password_data.current_password.encode('utf-8'), 
                    password_hash.encode('utf-8')
                )
                if not is_password_valid:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Incorrect current password"
                    )
            
            # 4. Hash & Set New Password
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_data.new_password.encode('utf-8'), salt)
            new_password_hash = hashed.decode('utf-8')

            # 5. Update Password
            cursor.execute("""
                UPDATE users 
                SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_password_hash, user_id))
            
            conn.commit()
            logger.info(f"Password updated for user {user_id}")
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
                detail="Failed to update password"
            )
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.autocommit = True
                conn.close()


# Global singleton instance
user_service = UserService()
