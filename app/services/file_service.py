import os
import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import List, Optional

UPLOAD_DIR = "static/uploads"
ALLOWED_EXTENSIONS_CV = {".pdf"}
ALLOWED_EXTENSIONS_PORTFOLIO = {".pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

class FileService:
    def __init__(self):
        # Create upload directory if it doesn't exist
        Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    def validate_file(self, file: UploadFile, allowed_extensions: set):
        filename = file.filename if file.filename else "unknown"
        ext = os.path.splitext(filename)[1].lower()
        
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type for {filename}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Check file size (approximate, reading chunk)
        # Real validation usually done by reading content or headers content-length
        # Fastapi UploadFile doesn't have size info easily without reading.
        # We can implement size check during read.

    async def save_file(self, file: UploadFile, subfolder: str = "") -> str:
        """
        Save uploaded file to local storage.
        Returns the relative URL/path to the file.
        """
        # Validate extension
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{ext}"
        
        # Determine save path
        folder_path = Path(UPLOAD_DIR) / subfolder
        folder_path.mkdir(parents=True, exist_ok=True)
        
        file_path = folder_path / unique_filename
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
            
        # Return relative path for database
        return f"/static/uploads/{subfolder}/{unique_filename}".replace("//", "/")

file_service = FileService()
