from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class WorkTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Work type name")
    code: str = Field(..., min_length=1, max_length=20, description="Unique code")
    description: Optional[str] = Field(None, description="Description of work type")


class WorkTypeCreate(WorkTypeBase):
    @validator('code')
    def code_uppercase(cls, v):
        return v.upper()


class WorkTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = None
    
    @validator('code')
    def code_uppercase(cls, v):
        if v is not None:
            return v.upper()
        return v


class WorkTypeResponse(WorkTypeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WorkTypeListResponse(BaseModel):
    items: List[WorkTypeResponse]
    total: int