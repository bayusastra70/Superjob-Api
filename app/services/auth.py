from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from app.core.config import settings

from typing import Optional

from app.services.database import get_db_connection, release_connection

from loguru import logger
import bcrypt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import psycopg2
from psycopg2 import errors
import time
import random
import string
import random
import string
import secrets
import hashlib
from app.services.email_service import email_service


class Authenticator:
    def __init__(self):
        pass

    def get_user_by_email(self, email: str):
        """Get user by email with all roles"""
        logger.info(f"GET USER BY EMAIL BEGIN for: {email}")
        conn = None
        cursor = None

        try:
            logger.info("Step 1: Getting connection...")
            conn = get_db_connection()
            logger.info("Step 2: Connection obtained, creating cursor...")
            cursor = conn.cursor()
            logger.info("Step 3: Cursor created")

            # Query untuk mendapatkan user dengan semua roles
            query = """
            WITH user_roles_cte AS (
                SELECT
                    ur.user_id,
                    json_agg(
                        json_build_object(
                            'role_id', r.id,
                            'role_name', r.name,
                            'is_active', ur.is_active,
                            'assigned_at', ur.assigned_at
                        )
                    ) as roles_array
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.is_active = true
                GROUP BY ur.user_id
            )
            SELECT
                u.id,
                u.email,
                u.username,
                u.full_name,
                u.password_hash,
                u.is_active,
                u.is_superuser,
                uc.company_id,
                COALESCE(urc.roles_array, '[]'::json) as roles,
                COALESCE(
                    (SELECT r.name
                    FROM user_roles ur
                    JOIN roles r ON ur.role_id = r.id
                    WHERE ur.user_id = u.id
                    AND ur.is_active = true
                    ORDER BY ur.assigned_at DESC
                    LIMIT 1),
                    'candidate'
                ) as primary_role
            FROM users u
            LEFT JOIN users_companies uc ON u.id = uc.user_id
            LEFT JOIN user_roles_cte urc ON u.id = urc.user_id
            WHERE u.email = %s AND u.is_active = true
            LIMIT 1
            """

            logger.info(f"Step 4: Executing query for email: {email}")

            # SET STATEMENT TIMEOUT
            cursor.execute("SET statement_timeout = 5000")  # 5 seconds timeout

            start_time = time.time()
            cursor.execute(query, (email,))
            execution_time = time.time() - start_time
            logger.info(f"Step 5: Query executed in {execution_time:.2f} seconds")

            user_data = cursor.fetchone()
            logger.info(f"Step 6: Fetched data: {user_data is not None}")

            if not user_data:
                logger.warning(f"User not found: {email}")
                return None

            logger.info(f"User found: {email}, ID: {user_data['id']}")

            return {
                "id": user_data["id"],
                "email": user_data["email"],
                "username": user_data["username"],
                "full_name": user_data["full_name"],
                "is_active": user_data["is_active"],
                "is_superuser": user_data["is_superuser"],
                "role": user_data["primary_role"],
                "roles": user_data["roles"],
                "company_id": user_data["company_id"],
            }

        except psycopg2.errors.QueryCanceled as e:
            logger.error(f"QUERY TIMEOUT for email {email}: {e}")
            return None
        except psycopg2.OperationalError as e:
            logger.error(f"DATABASE OPERATIONAL ERROR for email {email}: {e}")
            return None
        except Exception as e:
            logger.error(f"UNEXPECTED ERROR getting user by email {email}: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
        finally:
            if cursor:
                try:
                    cursor.close()
                    logger.info("Cursor closed")
                except:
                    pass
            release_connection(conn)

    def get_user_name_for_otp(self, email: str) -> Optional[str]:
        """
        Lightweight query to get user's full name for OTP emails.
        Returns None if user does not exist.
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT full_name FROM users WHERE email = %s", (email,))

            result = cursor.fetchone()
            if result:
                return result["full_name"]
            return None

        except Exception as e:
            logger.error(f"Error getting user name for OTP: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

    def is_user_active(self, email: str) -> bool:
        """
        Check if user is already active/verified.
        Returns True if user exists and is_active, False otherwise.
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT is_active FROM users WHERE email = %s", (email,))

            result = cursor.fetchone()
            if result:
                return bool(result["is_active"])
            return False

        except Exception as e:
            logger.error(f"Error checking user active status: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

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

    def role_exists(self, role_id: int) -> bool:
        """Check if role exists in roles table"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT 1 FROM roles WHERE id = %s AND is_active = true", (role_id,)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking role existence {role_id}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

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

            logger.info(
                f"User authenticated successfully",
                event="user_login",
                user={"id": user_data["id"], "role": None},
            )
            return {
                "id": user_data["id"],
                "email": user_data["email"],
                "username": user_data["username"],
                "full_name": user_data["full_name"],
                "is_superuser": user_data["is_superuser"],
            }

        except Exception as e:
            logger.error(
                f"Authentication failed",
                event="login_failure",
                error={
                    "type": "AuthenticationError",
                    "message": str(e),
                    "code": "AUTH_FAILED",
                },
                context={"email": email},
            )
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
        is_active: Optional[bool] = None,
    ):
        """Update semua data user tanpa auth check (untuk testing/demo)"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Cek apakah user exists
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))

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
                    (email, user_id),
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
                    (username, user_id),
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
                    (phone, user_id),
                )
                if cursor.fetchone():
                    raise ValueError("Phone number already in use by another user")

                update_fields.append("phone = %s")
                update_params.append(phone)

            # Update role
            if role is not None:
                if role not in ["admin", "employer", "candidate"]:
                    raise ValueError(
                        "Invalid role. Must be: admin, employer, candidate"
                    )

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
                    SET {", ".join(update_fields)}
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
                (user_id,),
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
            release_connection(conn)

    def toggle_user_active_simple(self, user_id: int):
        """Toggle user active status tanpa auth"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get current status
            cursor.execute("SELECT is_active FROM users WHERE id = %s", (user_id,))

            result = cursor.fetchone()
            if not result:
                return None

            # Get current status
            if hasattr(result, "keys"):
                current_status = result.get("is_active")
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
                (new_status, user_id),
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
            release_connection(conn)

    def _format_user_response(self, user_data):
        """Helper method untuk format user response"""
        if hasattr(user_data, "keys"):  # RealDictRow
            return {
                "id": user_data.get("id"),
                "email": user_data.get("email"),
                "username": user_data.get("username"),
                "full_name": user_data.get("full_name"),
                "phone": user_data.get("phone"),
                "role": user_data.get("role"),
                "is_active": user_data.get("is_active"),
                "is_superuser": user_data.get("is_superuser"),
                "created_at": user_data.get("created_at"),
                "updated_at": user_data.get("updated_at"),
            }
        else:  # tuple
            # RETURNING order in create_user: id, email, username, full_name, phone, is_active, is_superuser, created_at, updated_at
            return {
                "id": user_data[0],
                "email": user_data[1],
                "username": user_data[2],
                "full_name": user_data[3],
                "phone": user_data[4],
                "is_active": user_data[5],
                "is_superuser": user_data[6],
                "created_at": user_data[7],
                "updated_at": user_data[8],
            }

    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: str = None,
        phone: str = None,
        role: str = "candidate",
        role_id: int = None,
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
                WHERE email = %s OR username = %s OR (phone IS NOT NULL AND phone = %s)
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

            # Insert new user without deprecated columns
            cursor.execute(
                """
                INSERT INTO users
                (email, username, full_name, phone, password_hash, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id, email, username, full_name, phone, is_active, is_superuser, created_at, updated_at
            """,
                (email, username, full_name, phone, hashed_password),
            )

            new_user = cursor.fetchone()
            user_id = new_user[0] if new_user else None

            # Assign role using RBAC system if role_id provided
            if user_id and role_id:
                from app.services.role_base_access_control_service import (
                    RoleBaseAccessControlService,
                )

                rbac_service = RoleBaseAccessControlService()
                rbac_service.assign_role_to_user(user_id, role_id)

            conn.commit()

            logger.info(
                f"New user registered",
                event="user_registered",
                user={"id": new_user["id"], "role": role},
            )
            return dict(new_user)

        except Exception as e:
            logger.error(
                f"User registration failed",
                event="registration_failure",
                error={
                    "type": "RegistrationError",
                    "message": str(e),
                    "code": "USER_CREATE_FAILED",
                },
            )
            return None
        finally:
            if cursor:
                cursor.close()

    def check_registration_conflicts(
        self, company_name: str, email: str, username: str, phone: str
    ) -> Optional[str]:
        """
        Check for existing company name or user credentials to fail fast.
        Returns error message if conflict found, None otherwise.
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            check_query = """
                SELECT
                    (SELECT 1 FROM companies WHERE name = %s LIMIT 1) as company_exists,
                    (SELECT 1 FROM users WHERE email = %s OR username = %s OR phone = %s LIMIT 1) as user_exists
            """
            cursor.execute(check_query, (company_name, email, username, phone))
            check_result = cursor.fetchone()

            if check_result["company_exists"]:
                return "Company name is already registered"

            if check_result["user_exists"]:
                return "Email, username, or phone number is already registered"

            return None

        except Exception as e:
            logger.error(f"Error checking registration conflicts: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

    def create_company_with_admin(self, company_data: dict, user_data: dict):
        """
        Create a new company and an admin user in a single transaction.
        Relates them in users_companies table.
        Optimized to minimize database round-trips.
        """
        conn = None
        cursor = None
        try:
            # Hash password early to overlap with potential I/O if in async context
            password_bytes = user_data["password"].encode("utf-8")
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

            conn = get_db_connection()
            conn.autocommit = False
            cursor = conn.cursor()

            # 1. Combined Duplicate Check (Single round-trip)
            # check_query = """
            #     SELECT
            #         (SELECT 1 FROM companies WHERE name = %s LIMIT 1) as company_exists,
            #         (SELECT 1 FROM users WHERE email = %s OR username = %s OR phone = %s LIMIT 1) as user_exists
            # """
            # cursor.execute(check_query, (
            #     company_data["name"],
            #     user_data["email"], user_data["username"], user_data["phone"]
            # ))
            # check_result = cursor.fetchone()

            # if check_result["company_exists"]:
            #     logger.warning(f"Company already exists: {company_data['name']}")
            #     conn.rollback()
            #     return {"success": False, "message": "Company already exists"}

            # if check_result["user_exists"]:
            #     logger.warning(f"User already exists: {user_data['email']}, {user_data['username']}, or {user_data['phone']}")
            #     conn.rollback()
            #     return {"success": False, "message": "User with this email, username, or phone already exists"}

            # Validate nib_document_url is required
            if not company_data.get("nib_document_url"):
                logger.error("Missing nib_document_url in company registration")
                conn.rollback()
                return {"success": False, "message": "NIB Document URL is required"}

            # 2. Unified Insertion using CTE (Single round-trip for 4 inserts: company, user, link, attachments)
            unified_insert_query = """
            WITH new_company AS (
                INSERT INTO companies
                (name, description, industry, website, location, logo_url, is_verified, founded_year, employee_size,
                 linkedin_url, twitter_url, instagram_url, email, phone, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id
            ),
            new_attachments AS (
                INSERT INTO company_attachments (company_id, nib_url, nib_storage_id, created_at, updated_at)
                SELECT id, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM new_company
            ),
            new_user AS (
                INSERT INTO users
                (email, username, full_name, phone, password_hash, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id
            ),
            new_link AS (
                INSERT INTO users_companies (user_id, company_id)
                SELECT new_user.id, new_company.id FROM new_user, new_company
            )
            SELECT new_company.id as company_id, new_user.id as user_id
            FROM new_company, new_user;
            """

            cursor.execute(
                unified_insert_query,
                (
                    # Company values
                    company_data["name"],
                    company_data["description"],
                    company_data["industry"],
                    company_data["website"],
                    company_data["location"],
                    company_data["logo_url"],
                    company_data.get("is_verified", False),
                    company_data.get("founded_year"),
                    company_data.get("employee_size"),
                    company_data.get("linkedin_url", ""),
                    company_data.get("twitter_url", ""),
                    company_data.get("instagram_url", ""),
                    company_data.get("email"),
                    company_data.get("phone"),
                    # Attachment values
                    company_data["nib_document_url"],
                    company_data.get("nib_document_storage_id"),
                    # User values
                    user_data["email"],
                    user_data["username"],
                    user_data["full_name"],
                    user_data["phone"],
                    hashed_password,
                ),
            )

            result_ids = cursor.fetchone()
            user_id = result_ids["user_id"]

            # Assign admin role using RBAC system (role_id 1 is admin)
            cursor.execute(
                """
                INSERT INTO user_roles (user_id, role_id, assigned_at, is_active)
                VALUES (%s, 1, CURRENT_TIMESTAMP, true)
                """,
                (user_id,),
            )

            conn.commit()

            logger.info(
                f"Company and admin registered",
                event="company_registered",
                user={"id": result_ids["user_id"], "role": "admin"},
                context={"company_name": company_data["name"]},
            )

            # Send success email
            email_service.send_corporate_registration_email(
                to_email=user_data["email"],
                name=user_data["full_name"],
                company_name=company_data["name"],
            )

            return {
                "success": True,
                "company_id": result_ids["company_id"],
                "user_id": result_ids["user_id"],
            }

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(
                f"Company registration failed",
                event="company_registration_failure",
                error={
                    "type": "CompanyRegistrationError",
                    "message": str(e),
                    "code": "COMPANY_CREATE_FAILED",
                },
            )
            return {"success": False, "message": str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                # Restore autocommit
                conn.autocommit = True

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
                logger.info(
                    f"Password reset successfully",
                    event="password_reset",
                    user={"id": result["id"], "role": None},
                )
                return result

            return None

        except Exception as e:
            logger.error(
                f"Password reset failed",
                event="password_reset_failure",
                error={
                    "type": "PasswordResetError",
                    "message": str(e),
                    "code": "PASSWORD_RESET_FAILED",
                },
                context={"email": email},
            )
            return None
        finally:
            if cursor:
                cursor.close()

    def register_talent(
        self,
        email: str,
        password: Optional[str] = None,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        cv_url: Optional[str] = None,
        username: Optional[str] = None,
        auth_provider: str = "email",
    ):
        """
        Register a new talent user and create their candidate info in a single transaction.
        """
        import uuid

        # Generate a unique username if none is provided (common in OAuth/Google signup)
        # Format: email_prefix + random_suffix
        if not username:
            username = email.split("@")[0] + "_" + str(uuid.uuid4())[:8]

        # Generate a secure random placeholder password if none is provided
        # This prevents empty passwords and ensures accounts created via OAuth are secure
        if not password:
            password = str(uuid.uuid4())

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if user already exists
            cursor.execute(
                """
                SELECT id FROM users
                WHERE email = %s OR username = %s OR (phone IS NOT NULL AND phone = %s)
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

            # Insert new user
            cursor.execute(
                """
                INSERT INTO users
                (email, username, full_name, phone, password_hash, is_active, auth_provider, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, false, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id, email, username, full_name, phone, is_active, is_superuser, created_at, updated_at
                """,
                (email, username, full_name, phone, hashed_password, auth_provider),
            )

            new_user = cursor.fetchone()
            user_id = new_user["id"]

            # Create Candidate Info with CV URL
            cursor.execute(
                """
                INSERT INTO candidate_info (user_id, cv_url, created_at, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (user_id, cv_url),
            )

            # Assign role
            cursor.execute("SELECT id FROM roles WHERE name = 'candidate'")
            role_row = cursor.fetchone()
            if role_row:
                role_id = role_row["id"]
                cursor.execute(
                    """
                    INSERT INTO user_roles (user_id, role_id, assigned_at, is_active)
                    VALUES (%s, %s, CURRENT_TIMESTAMP, true)
                    """,
                    (user_id, role_id),
                )

            conn.commit()

            # SEND OTP
            # Note: We do this after commit so user is created even if email fails (though we could transact it)
            # But OTP table operations are separate usually.
            # Let's call request_otp. We propagate any rate limit error if it somehow happens (unlikely for new user)
            try:
                self.request_otp(email, name=full_name or username)
            except Exception as e:
                logger.error(f"Failed to send initial OTP to {email}: {e}")
                # We don't fail registration, user can request resend later

            logger.info(f"Talent registered: {email}")
            return dict(new_user)

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Talent registration error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

    def request_otp(self, email: str, name: str = ""):
        """
        Request a new OTP for email verification.
        Enforces rate limit: Max 3 requests per 5 minutes.
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 1. Lazy Cleanup: Delete used/expired OTPs older than 1 hour for this email
            cursor.execute(
                """
                DELETE FROM otp_requests 
                WHERE email = %s AND created_at < NOW() - INTERVAL '1 hour'
                """,
                (email,),
            )

            # 2. Rate Limit Check: Count requests in last 5 minutes
            # Fetch count and oldest request time in one query
            cursor.execute(
                """
                WITH recent_otp AS (
                    SELECT created_at FROM otp_requests 
                    WHERE email = %s AND created_at > NOW() - INTERVAL '5 minutes'
                )
                SELECT 
                    COUNT(*) as request_count,
                    MIN(created_at) as oldest_request_time,
                    EXTRACT(EPOCH FROM ((MIN(created_at) + INTERVAL '5 minutes') - NOW())) as wait_seconds
                FROM recent_otp
                """,
                (email,),
            )

            result = cursor.fetchone()
            request_count = result["request_count"]

            if request_count >= 3:
                wait_seconds = result["wait_seconds"] or 0

                if wait_seconds < 0:
                    wait_seconds = 0

                wait_min = int(wait_seconds // 60)
                wait_sec = int(wait_seconds % 60)

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many OTP requests. Please wait {wait_min}m {wait_sec}s before trying again.",
                )

            # 3. Generate OTP
            otp_code = "".join(random.choices(string.digits, k=6))

            # Hash OTP
            otp_hash = bcrypt.hashpw(otp_code.encode("utf-8"), bcrypt.gensalt()).decode(
                "utf-8"
            )

            # 4. Insert OTP HASH
            cursor.execute(
                """
                INSERT INTO otp_requests (email, otp_code, created_at, expires_at)
                VALUES (%s, %s, NOW(), NOW() + INTERVAL '5 minutes')
                """,
                (email, otp_hash),
            )

            conn.commit()

            # 5. Send Email with PLAIN OTP
            email_service.send_otp_email(email, otp_code, name)

            return True

        except HTTPException:
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error requesting OTP for {email}: {e}")
            raise Exception("Failed to generate OTP")
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

    def verify_otp(self, email: str, otp_code: str):
        """Verify OTP code"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Find all valid OTP hashes for this email
            cursor.execute(
                """
                SELECT id, otp_code FROM otp_requests
                WHERE email = %s 
                AND is_used = false 
                AND expires_at > NOW()
                ORDER BY created_at DESC
                """,
                (email,),
            )

            valid_requests = cursor.fetchall()

            otp_id = None

            # Verify against hashes
            for req in valid_requests:
                stored_hash = req["otp_code"]
                if bcrypt.checkpw(
                    otp_code.encode("utf-8"), stored_hash.encode("utf-8")
                ):
                    otp_id = req["id"]
                    break

            if not otp_id:
                return False

            # Mark as used
            cursor.execute(
                "UPDATE otp_requests SET is_used = true WHERE id = %s", (otp_id,)
            )

            # Activate user (verify)
            # Activate user (verify)
            cursor.execute(
                "UPDATE users SET is_active = true WHERE email = %s RETURNING full_name",
                (email,),
            )
            result = cursor.fetchone()
            full_name = result["full_name"] if result else ""

            conn.commit()

            # Send Success Registration Email
            try:
                email_service.send_success_registration_email(email, full_name)
            except Exception as e:
                logger.error(f"Failed to send success email to {email}: {e}")

            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error verifying OTP for {email}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

    def request_password_reset(self, email: str):
        """
        Request password reset token and send email
        """
        conn = None
        cursor = None
        try:
            # 1. Check if user exists
            user_name = self.get_user_name_for_otp(email)

            if not user_name:
                # Security: Return True to prevent email enumeration
                logger.info(f"Password reset requested for non-existent email: {email}")
                return True

            conn = get_db_connection()
            cursor = conn.cursor()

            # 2. Generate Token
            token = secrets.token_urlsafe(32)
            # Use SHA256 for storage to allow fast lookup. Token itself provides entropy.
            token_hash = hashlib.sha256(token.encode()).hexdigest()

            # 3. Store in DB
            cursor.execute(
                """
                INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
                SELECT id, %s, NOW() + INTERVAL '30 minutes'
                FROM users WHERE email = %s
                """,
                (token_hash, email),
            )

            conn.commit()

            # 4. Send Email
            # Frontend URL from env
            reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

            email_service.send_reset_password_email(email, user_name, reset_link)

            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error requesting password reset for {email}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

    def reset_password_with_token(self, token: str, new_password: str):
        """
        Verify token and reset password
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 1. Verify Token
            # We use SHA256 for fast, deterministic lookup.

            import hashlib

            token_hash_lookup = hashlib.sha256(token.encode()).hexdigest()

            cursor.execute(
                """
                SELECT id, user_id, expires_at, is_used 
                FROM password_reset_tokens 
                WHERE token_hash = %s
                """,
                (token_hash_lookup,),
            )

            token_record = cursor.fetchone()

            if not token_record:
                logger.warning("Invalid password reset token")
                return False, "Invalid or expired token"

            if token_record["is_used"]:
                return False, "Token already used"

            # Check if token is valid and not expired (DB handles time comparison)
            cursor.execute(
                """
                SELECT id, user_id 
                FROM password_reset_tokens 
                WHERE token_hash = %s AND is_used = false AND expires_at > NOW()
                """,
                (token_hash_lookup,),
            )
            valid_record = cursor.fetchone()

            if not valid_record:
                return False, "Invalid, expired, or used token"

            user_id = valid_record["user_id"]

            # 2. Update Password
            new_password_hash = self._hash_password(new_password)

            cursor.execute(
                "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s",
                (new_password_hash, user_id),
            )

            # 3. Mark Token Used
            cursor.execute(
                "UPDATE password_reset_tokens SET is_used = true WHERE id = %s",
                (valid_record["id"],),
            )

            conn.commit()
            return True, "Password reset successfully"

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error resetting password: {e}")
            return False, "Internal server error"
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

    def create_candidate_info(self, user_id: int, cv_url: Optional[str] = None):
        """Create or update candidate info"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Using ON CONFLICT to handle both create and update
            query = """
            INSERT INTO candidate_info (user_id, cv_url, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id)
            DO UPDATE SET cv_url = EXCLUDED.cv_url, updated_at = CURRENT_TIMESTAMP
            RETURNING user_id, cv_url
            """

            cursor.execute(query, (user_id, cv_url))
            result = cursor.fetchone()
            conn.commit()

            if result:
                logger.info(f"Candidate info created/updated for user: {user_id}")
                return dict(result)

            return None

        except Exception as e:
            logger.error(f"Error creating/updating candidate info for {user_id}: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

    def google_authenticate_talent(self, id_token_str: str):
        """
        Verify Google ID token and authenticate/register talent user.
        """
        try:
            if not settings.GOOGLE_CLIENT_ID:
                logger.error(
                    "GOOGLE_CLIENT_ID is not set in settings/environment variables."
                )

            # 1. Verify token with Google
            # audience=settings.GOOGLE_CLIENT_ID ensures the token was intended for our app
            # If GOOGLE_CLIENT_ID is None, it might skip audience check or check generic validity
            id_info = id_token.verify_oauth2_token(
                id_token_str, google_requests.Request(), settings.GOOGLE_CLIENT_ID
            )

            email = id_info.get("email")
            name = id_info.get("name", "")

            if not email:
                logger.error("Email not found in Google ID token")
                return None

            # 2. Check if user exists
            user = self.get_user_by_email(email)
            is_new_user = False

            if not user:
                # 3. Register new user if not exists
                user = self.register_talent(
                    email=email, full_name=name, cv_url=None, auth_provider="google"
                )
                if not user:
                    logger.error(f"Failed to register new Google user: {email}")
                    return None
                is_new_user = True
                logger.info(f"New talent registered via Google: {email}")
            else:
                # 4. Existing user - verify role
                # For simplicity, we ensure existing talent users have the candidate role
                if user.get("role") != "candidate":
                    logger.warning(
                        f"Google login attempt for non-candidate role: {email}"
                    )
                    # In a real app, you might want to raise a specific exception here
                    # But for the service layer, we can return None and let the router handle HTTPException
                    return {"error": "ROLE_MISMATCH"}

                logger.info(f"Talent logged in via Google: {email}")

            return {"user": user, "is_new_user": is_new_user}

        except ValueError as e:
            # Invalid token
            logger.error(f"Invalid Google ID token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error during Google authentication service: {e}")
            return None


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
    logger.info("VERIFY TOKEN BEGIN")
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
