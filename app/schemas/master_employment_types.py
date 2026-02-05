from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class EmploymentTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Employment type name")
    code: str = Field(..., min_length=1, max_length=20, description="Unique code")
    description: Optional[str] = Field(None, description="Description of employment type")


class EmploymentTypeCreate(EmploymentTypeBase):
    @validator('code')
    def code_uppercase(cls, v):
        return v.upper()


class EmploymentTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = None
    
    @validator('code')
    def code_uppercase(cls, v):
        if v is not None:
            return v.upper()
        return v


class EmploymentTypeResponse(EmploymentTypeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EmploymentTypeListResponse(BaseModel):
    items: List[EmploymentTypeResponse]
    total: int