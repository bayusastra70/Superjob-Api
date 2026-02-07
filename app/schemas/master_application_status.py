from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ApplicationStatusBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Status name")
    code: str = Field(..., min_length=1, max_length=20, description="Status code")
    description: Optional[str] = Field(None, description="Status description")


class ApplicationStatusCreate(ApplicationStatusBase):
    pass


class ApplicationStatusUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Status name")
    code: Optional[str] = Field(None, min_length=1, max_length=20, description="Status code")
    description: Optional[str] = Field(None, description="Status description")


class ApplicationStatusResponse(ApplicationStatusBase):
    id: int = Field(..., description="Status ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class ApplicationStatusListResponse(BaseModel):
    items: list[ApplicationStatusResponse] = Field(..., description="List of application statuses")
    total: int = Field(..., description="Total number of items")