"""
Solvera Storage API Client

Handles file uploads and deletions to Solvera Storage API.
Documentation: docs/Docs Solvera Storage.md
"""

import httpx
import logging
from typing import Optional, Dict, Any, List
from enum import Enum
from fastapi import UploadFile, HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageFolder(str, Enum):
    """Folder paths for Solvera Storage"""
    COMPANY_LOGO = "Superjob/company/logo"
    COMPANY_DOCUMENT = "Superjob/company/document"
    CANDIDATE_CV = "Superjob/candidate/cv"


class UploaderName(str, Enum):
    """Uploader names for Solvera Storage logging"""
    SUPERJOB_SERVICE = "superjob_service"


class SolveraStorageClient:
    """Client for interacting with Solvera Storage API"""
    
    def __init__(self):
        self.base_url = settings.SOLVERA_STORAGE_BASE_URL
        self.secret = settings.SOLVERA_STORAGE_SECRET
        self.upload_endpoint = f"{self.base_url}/api/external-upload"
        self.delete_endpoint = f"{self.base_url}/api/external-delete"
    
    async def upload_file(
        self, 
        file: UploadFile, 
        folder: StorageFolder,
        allowed_types: List[str],
        max_size_mb: float,
        uploader_name: UploaderName = UploaderName.SUPERJOB_SERVICE
    ) -> Dict[str, Any]:
        """
        Upload file to Solvera Storage
        
        Args:
            file: UploadFile object from FastAPI
            folder: StorageFolder enum value
            allowed_types: List of allowed MIME types (e.g., ["application/pdf"])
            max_size_mb: Maximum file size in MB
            uploader_name: Name of uploader for logging
            
        Returns:
            Dict with 'id', 'url', 'name', 'folder_path' keys
            
        Raises:
            HTTPException: If upload fails or validation fails
        """
        try:
            # Read file content
            file_content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Validate file size
            file_size_mb = len(file_content) / (1024 * 1024)
            if file_size_mb > max_size_mb:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size ({file_size_mb:.2f}MB) exceeds {max_size_mb}MB limit"
                )
            
            # Validate file type
            if file.content_type not in allowed_types:
                allowed_str = ", ".join(allowed_types)
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid file type. Allowed types: {allowed_str}. Got: {file.content_type}"
                )
            
            # Prepare multipart form data
            files = {
                "file": (file.filename, file_content, file.content_type)
            }
            data = {
                "folderName": folder.value,
                "uploaderName": uploader_name.value if isinstance(uploader_name, UploaderName) else uploader_name
            }
            headers = {
                "Authorization": f"Bearer {self.secret}"
            }
            
            # Upload to Solvera Storage
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.upload_endpoint,
                    files=files,
                    data=data,
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Solvera Storage upload failed: {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to upload file to storage"
                    )
                
                result = response.json()
                
                if not result.get("success"):
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=result.get("message", "Upload failed")
                    )
                
                # Extract data from response
                file_data = result.get("data", {})
                logger.info(f"File uploaded to Solvera Storage: {file_data.get('id')}")
                
                return {
                    "id": file_data.get("id"),
                    "url": file_data.get("url"),
                    "name": file_data.get("name"),
                    "folder_path": file_data.get("folderPath")
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading file to Solvera Storage: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file"
            )
    
    async def delete_file(self, file_id: str) -> bool:
        """
        Delete file from Solvera Storage
        
        Args:
            file_id: File ID from Solvera Storage
            
        Returns:
            True if deletion successful, False otherwise
        """
        if not file_id:
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.secret}",
                "Content-Type": "application/json"
            }
            payload = {"fileId": file_id}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    "DELETE",
                    self.delete_endpoint,
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"File deleted from Solvera Storage: {file_id}")
                    return result.get("success", False)
                else:
                    logger.warning(f"Failed to delete file {file_id}: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting file from Solvera Storage: {str(e)}")
            return False


# Global singleton instance
solvera_storage = SolveraStorageClient()
