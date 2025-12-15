from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from app.core.config import settings

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

    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: str = None,
        role: str = "candidate",
    ):
        """Create a new user in database"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if user already exists
            cursor.execute(
                """
                SELECT id FROM users 
                WHERE email = %s OR username = %s
            """,
                (email, username),
            )

            existing_user = cursor.fetchone()
            if existing_user:
                logger.warning(f"User already exists: {email} or {username}")
                return None

            # Hash password
            password_bytes = password.encode("utf-8")
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

            # Insert new user
            cursor.execute(
                """
                INSERT INTO users 
                (email, username, full_name, password_hash, role, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id, email, username, full_name, role, is_active, is_superuser
            """,
                (email, username, full_name, hashed_password, role),
            )

            new_user = cursor.fetchone()
            conn.commit()

            logger.info(f"New user created: {email} with role: {role}")
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

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise


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
