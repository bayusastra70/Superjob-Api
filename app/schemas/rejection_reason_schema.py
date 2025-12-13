from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class RejectionReasonCreate(BaseModel):
    """Schema untuk membuat rejection reason baru"""
    reason_code: str = Field(..., description="Unique code for the rejection reason")
    reason_text: str = Field(..., description="Description of the rejection reason")
    is_custom: bool = Field(default=False, description="Whether this is a custom reason")
    created_by: Optional[str] = Field(None, description="User who created this reason")


class RejectionReasonUpdate(BaseModel):
    """Schema untuk update rejection reason"""
    reason_code: Optional[str] = None
    reason_text: Optional[str] = None
    is_active: Optional[bool] = None


class RejectionReasonResponse(BaseModel):
    """Schema untuk response rejection reason"""
    id: int
    reason_code: str
    reason_text: str
    is_custom: bool
    is_active: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

