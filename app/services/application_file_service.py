
import logging
import os
import time
import uuid
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from pathlib import Path
from dotenv import load_dotenv
import httpx
import jwt

from app.services.database import get_db_connection
from app.schemas.application_file import (
    ApplicationFileUploadResponse,
    ApplicationFileResponse,
)

env_path = Path(__file__).parent.parent.parent / ".env"

# Only load .env in development
if os.getenv("RENDER") is None:  # Not running on Render
    load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


class ApplicationFileService:
    def __init__(self):
        # Supabase Configuration
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.bucket_name = os.getenv("SUPABASE_STORAGE_BUCKET", "cvs")
        
        # File validation
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE_MB", 10)) * 1024 * 1024
        self.allowed_extensions = os.getenv("ALLOWED_FILE_EXTENSIONS", ".pdf,.doc,.docx,.jpg,.jpeg,.png").split(",")
        
        # Debug logging
        logger.info(f"Supabase Config - URL: {self.supabase_url}")
        logger.info(f"Supabase Config - Bucket: {self.bucket_name}")
        logger.info(f"Supabase Config - Key starts with: {self.supabase_key[:20] if self.supabase_key else 'MISSING'}...")
        
        # Verify JWT role
        if self.supabase_key:
            try:
                decoded = jwt.decode(
                    self.supabase_key, 
                    options={"verify_signature": False}
                )
                role = decoded.get('role', 'unknown')
                logger.info(f"JWT Role detected: {role}")
                if role != 'service_role':
                    logger.warning("⚠️ Key is NOT service_role! Upload may fail due to RLS.")
            except Exception as e:
                logger.warning(f"Could not decode JWT: {e}")
    
    async def upload_file(
        self,
        application_id: int,
        file: UploadFile,
        original_filename: str,
        stored_filename: str,
        file_type: str,
        uploader_id: int,
        uploader_ip: Optional[str] = None,
        uploader_user_agent: Optional[str] = None
    ) -> Optional[ApplicationFileUploadResponse]:
        """Upload file to Supabase Storage using direct HTTP API"""
        start_time = time.time()
        file_id = None
        
        try:
            # ========== VALIDASI FILE ==========
            # Validasi ukuran
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)
            
            if file_size > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Max size: {self.max_file_size//1024//1024}MB"
                )
            
            # Validasi ekstensi
            file_extension = os.path.splitext(original_filename)[1].lower()
            if file_extension not in self.allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type not allowed. Allowed: {', '.join(self.allowed_extensions)}"
                )
            
            # ========== GENERATE FILENAME UNIK ==========
            unique_filename = f"{file_type}_{uuid.uuid4().hex}{file_extension}"
            
            # ========== SIMPAN KE DATABASE (status: uploading) ==========
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO application_files (
                application_id, 
                file_name, 
                stored_filename,
                upload_status,
                file_type,
                created_by,
                uploader_ip,
                uploader_user_agent
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """, (
                application_id,
                original_filename,
                unique_filename,
                "uploading",
                file_type,
                uploader_id,
                uploader_ip,
                uploader_user_agent
            ))
            
            file_id = cursor.fetchone()['id']
            
            # ========== UPLOAD KE SUPABASE STORAGE VIA HTTP API ==========
            if not self.supabase_url or not self.supabase_key:
                raise Exception("Supabase configuration missing")
            
            # Baca konten file
            file_content = await file.read()
            
            # Upload via HTTP API langsung
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": file.content_type or "application/octet-stream",
                }
                
                # URL untuk upload ke Supabase Storage
                upload_url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{unique_filename}"
                
                logger.info(f"Uploading to: {upload_url}")
                logger.info(f"File size: {len(file_content)} bytes")
                
                response = await client.post(
                    upload_url,
                    headers=headers,
                    content=file_content
                )
                
                logger.info(f"Supabase response status: {response.status_code}")
                
                if response.status_code not in [200, 201]:
                    try:
                        error_detail = response.json()
                        logger.error(f"Supabase error details: {error_detail}")
                    except:
                        error_detail = response.text
                    
                    if response.status_code == 403:
                        raise Exception(
                            f"Permission denied (403). Check: "
                            f"1) Service Role Key is correct, "
                            f"2) Bucket '{self.bucket_name}' exists and is public, "
                            f"3) No RLS policies blocking upload. Error: {error_detail}"
                        )
                    else:
                        raise Exception(f"Supabase upload failed ({response.status_code}): {error_detail}")
            
            # ========== GENERATE PUBLIC URL ==========
            # Untuk bucket public, URL formatnya:
            file_url = f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{unique_filename}"
            
            # ========== UPDATE DATABASE (status: completed) ==========
            upload_time = int((time.time() - start_time) * 1000)  # milliseconds
            
            cursor.execute("""
            UPDATE application_files 
            SET upload_status = %s,
                file_url = %s,
                upload_process_time = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """, (
                "completed",
                file_url,
                upload_time,
                file_id
            ))
            
            conn.commit()
            
            logger.info(f"✅ File uploaded successfully: {file_id} - {unique_filename}")
            logger.info(f"📎 Public URL: {file_url}")
            
            return ApplicationFileUploadResponse(
                message="File uploaded successfully",
                file_id=file_id,
                file_url=file_url,
                file_name=original_filename,
                upload_status="completed",
                upload_process_time=upload_time
            )
            
        except HTTPException:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"❌ Error uploading file: {e}")
            
            # Update status di database menjadi failed
            if file_id:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                    UPDATE application_files 
                    SET upload_status = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """, ("failed", file_id))
                    conn.commit()
                    logger.info(f"Updated file {file_id} status to 'failed'")
                except Exception as db_error:
                    logger.error(f"Failed to update DB status: {db_error}")
            
            return None
    
    def get_application_files(
        self,
        application_id: int,
        file_type: Optional[str] = None,
        upload_status: Optional[str] = None
    ) -> List[ApplicationFileResponse]:
        """Get files for an application"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT 
                id,
                application_id,
                file_name,
                stored_filename,
                upload_status,
                upload_process_time,
                file_url,
                file_type,
                created_by,
                created_at,
                updated_at
            FROM application_files
            WHERE application_id = %s
            """
            params = [application_id]
            
            if file_type:
                query += " AND file_type = %s"
                params.append(file_type)
            
            if upload_status:
                query += " AND upload_status = %s"
                params.append(upload_status)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            files = cursor.fetchall()
            
            return [
                ApplicationFileResponse(
                    id=row['id'],
                    application_id=row['application_id'],
                    file_name=row['file_name'],
                    stored_filename=row.get('stored_filename'),
                    upload_status=row['upload_status'],
                    upload_process_time=row['upload_process_time'],
                    file_url=row['file_url'],
                    file_type=row.get('file_type'),
                    created_by=row.get('created_by'),
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                for row in files
            ]
            
        except Exception as e:
            logger.error(f"Error getting application files: {e}")
            return []
    
    def get_file_by_id(
        self,
        file_id: int,
        application_id: Optional[int] = None
    ) -> Optional[ApplicationFileResponse]:
        """Get specific file by ID"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT 
                id,
                application_id,
                file_name,
                stored_filename,
                upload_status,
                upload_process_time,
                file_url,
                file_type,
                created_by,
                created_at,
                updated_at
            FROM application_files
            WHERE id = %s
            """
            params = [file_id]
            
            if application_id:
                query += " AND application_id = %s"
                params.append(application_id)
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return ApplicationFileResponse(
                id=row['id'],
                application_id=row['application_id'],
                file_name=row['file_name'],
                stored_filename=row.get('stored_filename'),
                upload_status=row['upload_status'],
                upload_process_time=row['upload_process_time'],
                file_url=row['file_url'],
                file_type=row.get('file_type'),
                created_by=row.get('created_by'),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            
        except Exception as e:
            logger.error(f"Error getting file by ID: {e}")
            return None
    
    async def delete_file(
        self,
        file_id: int,
        application_id: int,
        deleter_id: int
    ) -> bool:
        """Delete file from Supabase Storage and database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get file info before deleting
            cursor.execute("""
            SELECT stored_filename, file_url 
            FROM application_files 
            WHERE id = %s AND application_id = %s
            """, (file_id, application_id))
            
            file_info = cursor.fetchone()
            if not file_info:
                return False
            
            stored_filename = file_info['stored_filename']
            
            # Delete from Supabase Storage via HTTP API
            if stored_filename and self.supabase_url and self.supabase_key:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        headers = {
                            "Authorization": f"Bearer {self.supabase_key}",
                        }
                        
                        delete_url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{stored_filename}"
                        logger.info(f"Deleting from Supabase: {delete_url}")
                        
                        response = await client.delete(delete_url, headers=headers)
                        
                        if response.status_code not in [200, 204]:
                            logger.warning(f"Supabase delete returned {response.status_code}: {response.text}")
                        else:
                            logger.info(f"✅ File deleted from Supabase: {stored_filename}")
                except Exception as storage_error:
                    logger.error(f"Error deleting from Supabase: {storage_error}")
                    # Continue with DB deletion anyway
            
            # Delete from database
            cursor.execute("""
            DELETE FROM application_files 
            WHERE id = %s AND application_id = %s
            """, (file_id, application_id))
            
            # Log deletion (opsional)
            cursor.execute("""
            INSERT INTO file_deletion_logs (
                file_id,
                application_id,
                deleted_by,
                deletion_time
            ) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """, (file_id, application_id, deleter_id))
            
            conn.commit()
            
            logger.info(f"File record deleted from DB: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def cleanup_failed_uploads(self, hours_ago: int = 24) -> int:
        """Cleanup failed uploads older than specified hours"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get failed uploads
            cursor.execute("""
            SELECT id, stored_filename 
            FROM application_files 
            WHERE upload_status = 'failed' 
            AND created_at < CURRENT_TIMESTAMP - INTERVAL %s
            """, (f"{hours_ago} hours",))
            
            failed_files = cursor.fetchall()
            
            deleted_count = 0
            for file in failed_files:
                stored_filename = file['stored_filename']
                
                # Delete from Supabase Storage jika ada (SYNC VERSION)
                if stored_filename and self.supabase_url and self.supabase_key:
                    try:
                        # Gunakan sync client karena ini method sync
                        with httpx.Client(timeout=10.0) as client:
                            headers = {
                                "Authorization": f"Bearer {self.supabase_key}",
                            }
                            
                            delete_url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{stored_filename}"
                            response = client.delete(delete_url, headers=headers)
                            
                            if response.status_code not in [200, 204]:
                                logger.warning(f"Supabase delete returned {response.status_code}: {response.text}")
                    except Exception as e:
                        logger.warning(f"Failed to delete from Supabase: {e}")
                
                # Delete from database
                cursor.execute("DELETE FROM application_files WHERE id = %s", (file['id'],))
                deleted_count += 1
            
            conn.commit()
            
            logger.info(f"Cleaned up {deleted_count} failed uploads older than {hours_ago} hours")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up failed uploads: {e}")
            return 0
    
    