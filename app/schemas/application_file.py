from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class FileUploadStatus(str, Enum):
    """File upload status"""
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


class FileType(str, Enum):
    """File type"""
    RESUME = "resume"
    PORTFOLIO = "portfolio"
    CERTIFICATE = "certificate"
    COVER_LETTER = "cover_letter"
    OTHER = "other"


class ApplicationFileBase(BaseModel):
    """Base schema for application file"""
    application_id: int
    file_name: str
    file_type: Optional[FileType] = FileType.RESUME
    upload_status: Optional[FileUploadStatus] = FileUploadStatus.PENDING


class ApplicationFileCreate(ApplicationFileBase):
    """Schema for creating application file"""
    pass


class ApplicationFileResponse(ApplicationFileBase):
    """Schema for application file response"""
    id: int
    stored_filename: Optional[str] = None
    upload_process_time: Optional[int] = None  # in milliseconds
    file_url: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ApplicationFileUploadResponse(BaseModel):
    """Schema for file upload response"""
    message: str
    file_id: int
    file_url: Optional[str] = None
    file_name: str
    upload_status: str
    upload_process_time: Optional[int] = None


class FileUploadRequest(BaseModel):
    """Schema for file upload request"""
    file_type: FileType = Field(default=FileType.RESUME, description="Type of file being uploaded")