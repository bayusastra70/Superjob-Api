from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from app.core.config import settings

from typing import Optional

from app.services.database import get_db_connection

import logging
import bcrypt

logger = logging.getLogger(__name__)


class Authenticator:
    def __init__(self):
        pass

    def get_user_by_email(self, email: str):
        """Get user by email from standalone database"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT id, email, username, full_name, password_hash, is_active, is_superuser, role
            FROM users 
            WHERE email = %s AND is_active = true
            """

            cursor.execute(query, (email,))
            user_data = cursor.fetchone()

            if not user_data:
                logger.warning(f"User not found: {email}")
                return None

            logger.debug(f"User found: {email}")
            return {
                "id": user_data["id"],
                "email": user_data["email"],
                "username": user_data["username"],
                "full_name": user_data["full_name"],
                "is_active": user_data["is_active"],
                "is_superuser": user_data["is_superuser"],
                "role": user_data["role"],
            }

        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt directly"""
        try:
            # Convert password to bytes and truncate to 72 bytes for bcrypt
            password_bytes = password.encode("utf-8")
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
                logger.warning("Password truncated to 72 bytes for bcrypt")

            # Generate salt and hash
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            return hashed.decode("utf-8")
        except Exception as e:
            logger.error(f"Password hashing error: {e}")
            raise

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password using bcrypt directly"""
        try:
            # Convert to bytes
            plain_bytes = plain_password.encode("utf-8")
            if len(plain_bytes) > 72:
                plain_bytes = plain_bytes[:72]

            hashed_bytes = hashed_password.encode("utf-8")

            return bcrypt.checkpw(plain_bytes, hashed_bytes)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def authenticate_user(self, email: str, password: str):
        """Authenticate user against standalone database"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT id, email, username, full_name, password_hash, is_active, is_superuser
            FROM users 
            WHERE email = %s AND is_active = true
            """

            cursor.execute(query, (email,))
            user_data = cursor.fetchone()

            if not user_data:
                logger.warning(f"User not found or inactive: {email}")
                return None

            logger.debug(f"Found user: {user_data['email']}")

            # Verify password
            if not self._verify_password(password, user_data["password_hash"]):
                logger.warning(f"Invalid password for user: {email}")
                return None

            logger.info(f"User authenticated successfully: {email}")
            return {
                "id": user_data["id"],
                "email": user_data["email"],
                "username": user_data["username"],
                "full_name": user_data["full_name"],
                "is_superuser": user_data["is_superuser"],
            }

        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    # def create_user(self, email: str, username: str, password: str, full_name: str = None):
    #     """Create new user in standalone database"""
    #     try:
    #
    #         conn = get_db_connection()
    #         cursor = conn.cursor()

    #         # Check if user already exists
    #         cursor.execute("SELECT id FROM users WHERE email = %s OR username = %s", (email, username))
    #         if cursor.fetchone():
    #             logger.warning(f"User already exists: email={email}, username={username}")
    #             return None

    #         # Hash password
    #         hashed_password = self._hash_password(password)

    #         insert_query = """
    #         INSERT INTO users (email, username, full_name, password_hash)
    #         VALUES (%s, %s, %s, %s)
    #         RETURNING id, email, username, full_name, is_active, is_superuser
    #         """

    #         cursor.execute(insert_query, (email, username, full_name, hashed_password))
    #         result = cursor.fetchone()
    #         conn.commit()
    #         cursor.close()

    #         logger.info(f"User created successfully: {email}")
    #         return result

    #     except Exception as e:
    #         logger.error(f"Error creating user {email}: {e}")
    #         return None

    # def create_user(
    #     self,
    #     email: str,
    #     username: str,
    #     password: str,
    #     full_name: str = None,
    #     role: str = "candidate",
    # ):
    #     """Create a new user in database"""
    #     conn = None
    #     cursor = None
    #     try:
    #         conn = get_db_connection()
    #         cursor = conn.cursor()

    #         # Check if user already exists
    #         cursor.execute(
    #             """
    #             SELECT id FROM users 
    #             WHERE email = %s OR username = %s
    #         """,
    #             (email, username),
    #         )

    #         existing_user = cursor.fetchone()
    #         if existing_user:
    #             logger.warning(f"User already exists: {email} or {username}")
    #             return None

    #         # Hash password
    #         password_bytes = password.encode("utf-8")
    #         salt = bcrypt.gensalt()
    #         hashed_password = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

    #         # Insert new user
    #         cursor.execute(
    #             """
    #             INSERT INTO users 
    #             (email, username, full_name, password_hash, role, is_active, created_at, updated_at)
    #             VALUES (%s, %s, %s, %s, %s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    #             RETURNING id, email, username, full_name, role, is_active, is_superuser
    #         """,
    #             (email, username, full_name, hashed_password, role),
    #         )

    #         new_user = cursor.fetchone()
    #         conn.commit()

    #         logger.info(f"New user created: {email} with role: {role}")
    #         return dict(new_user)

    #     except Exception as e:
    #         logger.error(f"Error creating user: {e}")
    #         return None
    #     finally:
    #         if cursor:
    #             cursor.close()

    def update_user_simple(
        self,
        user_id: int,
        email: Optional[str] = None,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ):
        """Update semua data user tanpa auth check (untuk testing/demo)"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Cek apakah user exists
            cursor.execute(
                "SELECT id FROM users WHERE id = %s",
                (user_id,)
            )
            
            if not cursor.fetchone():
                logger.warning(f"User not found: {user_id}")
                return None
            
            # Build update query
            update_fields = []
            update_params = []
            
            # Update email (dengan pengecekan unik)
            if email is not None:
                # Cek jika email sudah digunakan oleh user lain
                cursor.execute(
                    "SELECT id FROM users WHERE email = %s AND id != %s",
                    (email, user_id)
                )
                if cursor.fetchone():
                    raise ValueError("Email already in use by another user")
                
                update_fields.append("email = %s")
                update_params.append(email.lower())
            
            # Update username (dengan pengecekan unik)
            if username is not None:
                # Cek jika username sudah digunakan oleh user lain
                cursor.execute(
                    "SELECT id FROM users WHERE username = %s AND id != %s",
                    (username, user_id)
                )
                if cursor.fetchone():
                    raise ValueError("Username already in use by another user")
                
                update_fields.append("username = %s")
                update_params.append(username)
            
            # Update full_name
            if full_name is not None:
                update_fields.append("full_name = %s")
                update_params.append(full_name)
            
            # Update phone (dengan pengecekan unik)
            if phone is not None:
                # Cek jika phone sudah digunakan oleh user lain
                cursor.execute(
                    "SELECT id FROM users WHERE phone = %s AND id != %s",
                    (phone, user_id)
                )
                if cursor.fetchone():
                    raise ValueError("Phone number already in use by another user")
                
                update_fields.append("phone = %s")
                update_params.append(phone)
            
            # Update role
            if role is not None:
                if role not in ['admin', 'employer', 'candidate']:
                    raise ValueError("Invalid role. Must be: admin, employer, candidate")
                
                update_fields.append("role = %s")
                update_params.append(role)
            
            # Update is_active
            if is_active is not None:
                update_fields.append("is_active = %s")
                update_params.append(is_active)
            
            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                
                # Add user_id to params
                update_params.append(user_id)
                
                update_query = f"""
                    UPDATE users 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                    RETURNING id, email, username, full_name, phone, role, 
                            is_active, is_superuser, created_at, updated_at
                """
                
                cursor.execute(update_query, update_params)
                updated_user = cursor.fetchone()
                conn.commit()
                
                if updated_user:
                    return self._format_user_response(updated_user)
            
            # Jika tidak ada field yang diupdate, ambil data user saat ini
            cursor.execute(
                """
                SELECT id, email, username, full_name, phone, role, 
                    is_active, is_superuser, created_at, updated_at
                FROM users WHERE id = %s
                """,
                (user_id,)
            )
            
            current_user = cursor.fetchone()
            if current_user:
                return self._format_user_response(current_user)
            
            return None
            
        except ValueError as ve:
            logger.warning(f"Validation error updating user {user_id}: {ve}")
            raise ve
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


    def toggle_user_active_simple(self, user_id: int):
        """Toggle user active status tanpa auth"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get current status
            cursor.execute(
                "SELECT is_active FROM users WHERE id = %s",
                (user_id,)
            )
            
            result = cursor.fetchone()
            if not result:
                return None
            
            # Get current status
            if hasattr(result, 'keys'):
                current_status = result.get('is_active')
            else:
                current_status = result[0]
            
            # Toggle status
            new_status = not current_status
            
            # Update status
            cursor.execute(
                """
                UPDATE users 
                SET is_active = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, email, username, full_name, phone, role, 
                        is_active, is_superuser, created_at, updated_at
                """,
                (new_status, user_id)
            )
            
            updated_user = cursor.fetchone()
            conn.commit()
            
            if updated_user:
                return self._format_user_response(updated_user)
            
            return None
            
        except Exception as e:
            logger.error(f"Error toggling user active status {user_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _format_user_response(self, user_data):
        """Helper method untuk format user response"""
        if hasattr(user_data, 'keys'):  # RealDictRow
            return {
                "id": user_data.get('id'),
                "email": user_data.get('email'),
                "username": user_data.get('username'),
                "full_name": user_data.get('full_name'),
                "phone": user_data.get('phone'),
                "role": user_data.get('role'),
                "is_active": user_data.get('is_active'),
                "is_superuser": user_data.get('is_superuser'),
                "created_at": user_data.get('created_at'),
                "updated_at": user_data.get('updated_at')
            }
        else:  # tuple
            return {
                "id": user_data[0],
                "email": user_data[1],
                "username": user_data[2],
                "full_name": user_data[3],
                "phone": user_data[4],
                "role": user_data[5],
                "is_active": user_data[6],
                "is_superuser": user_data[7],
                "created_at": user_data[8],
                "updated_at": user_data[9]
            }

    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: str = None,
        phone: str = None,  # Tambahkan parameter phone
        role: str = "candidate",
    ):
        """Create a new user in database"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if user already exists (email, username, atau phone)
            cursor.execute(
                """
                SELECT id FROM users 
                WHERE email = %s OR username = %s OR phone = %s
            """,
                (email, username, phone),
            )

            existing_user = cursor.fetchone()
            if existing_user:
                logger.warning(f"User already exists: {email}, {username}, or {phone}")
                return None

            # Hash password
            password_bytes = password.encode("utf-8")
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

            # Insert new user dengan phone
            cursor.execute(
                """
                INSERT INTO users 
                (email, username, full_name, phone, password_hash, role, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id, email, username, full_name, phone, role, is_active, is_superuser
            """,
                (email, username, full_name, phone, hashed_password, role),
            )

            new_user = cursor.fetchone()
            conn.commit()

            logger.info(f"New user created: {email} with role: {role} and phone: {phone}")
            return dict(new_user)

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def reset_password(self, email: str, new_password: str):
        """Reset user password"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Hash new password
            hashed_password = self._hash_password(new_password)

            update_query = """
            UPDATE users 
            SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
            WHERE email = %s
            RETURNING id, email
            """

            cursor.execute(update_query, (hashed_password, email))
            result = cursor.fetchone()
            conn.commit()

            if result:
                logger.info(f"Password reset successfully for: {email}")
                return result

            return None

        except Exception as e:
            logger.error(f"Error resetting password for {email}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.JWT_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise


def create_refresh_token(data: dict, expires_delta: timedelta = None):
    """
    Create JWT refresh token (longer-lived than access token)

    Refresh token digunakan untuk mendapatkan access token baru
    tanpa perlu login ulang.

    Default expiry: 7 days
    """
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            # Default: 7 days for refresh token
            expire = datetime.now(timezone.utc) + timedelta(days=7)

        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating refresh token: {e}")
        raise


def verify_refresh_token(token: str):
    """
    Verify JWT refresh token

    Returns user data if valid, raises exception if invalid or expired.
    Also checks that this is actually a refresh token (not access token).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify this is a refresh token
        token_type = payload.get("type")
        if token_type != "refresh":
            logger.warning(f"Expected refresh token, got: {token_type}")
            raise credentials_exception

        user_id = payload.get("user_id")
        email = payload.get("sub") or payload.get("email")
        role = payload.get("role")

        if email is None or user_id is None:
            logger.warning("Refresh token missing required fields")
            raise credentials_exception

        logger.debug(f"Refresh token verified for user: {email}, id: {user_id}")
        return {"email": email, "user_id": user_id, "role": role}

    except JWTError as jwt_error:
        logger.warning(f"Refresh token verification failed: {jwt_error}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Refresh token verification error: {e}")
        raise credentials_exception


def verify_token(token: str):
    """Verify JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        logger.info(f"Token payload: {payload}")

        user_id = payload.get("user_id")
        email = payload.get("sub") or payload.get("email")

        if email is None or user_id is None:
            logger.warning("Token missing required fields")
            raise credentials_exception

        logger.debug(f"Token verified for user: {email}, id: {user_id}")
        return {"email": email, "user_id": user_id}

    except JWTError as jwt_error:
        logger.warning(f"JWT verification failed: {jwt_error}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise credentials_exception


# Helper function untuk hash password
def get_password_hash(password: str) -> str:
    """Get password hash using bcrypt directly"""
    auth = Authenticator()
    return auth._hash_password(password)


# Helper function untuk verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt directly"""
    auth = Authenticator()
    return auth._verify_password(plain_password, hashed_password)


# Global authenticator instance
auth = Authenticator()
