from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict


class CandidateApplicationBase(BaseModel):
    """Base schema untuk candidate application"""
    name: str
    email: EmailStr
    applied_position: str
    status: Optional[str] = "pending"
    rejection_reason_id: Optional[int] = None


class CandidateApplicationCreate(CandidateApplicationBase):
    """Schema untuk membuat candidate application baru"""
    pass


class CandidateApplicationUpdate(BaseModel):
    """Schema untuk update candidate application"""
    status: Optional[str] = None
    rejection_reason_id: Optional[int] = None


class CandidateApplicationRead(CandidateApplicationBase):
    """Schema untuk response candidate application"""
    id: int
    applied_at: datetime
    
    class Config:
        from_attributes = True


class CandidateApplicationResponse(CandidateApplicationRead):
    """Schema lengkap untuk response dengan relasi rejection_reason"""
    rejection_reason: Optional[Dict] = None
    
    class Config:
        from_attributes = True

