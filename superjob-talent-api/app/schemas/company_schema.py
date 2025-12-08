from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid

class CompanyBase(BaseModel):
    name: str = Field(..., max_length=255)
    industry: str = Field(..., max_length=100)
    description: str
    website: str = Field(..., max_length=255)
    location: str
    logo_url: str = Field(..., max_length=255)
    founded_year: int = Field(..., description="The year the company was founded")
    employee_size: str = Field(..., description="The size of the company")
    linkedin_url: str = Field(..., max_length=255)
    twitter_url: str = Field(..., max_length=255)
    instagram_url: str = Field(..., max_length=255)

class CompanyCreate(CompanyBase):
    created_by: uuid.UUID = Field(..., description="The ID of the user who created the company")

class CompanyUpdate(CompanyBase):
    name: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    logo_url: Optional[str] = None
    founded_year: Optional[int] = None
    employee_size: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    instagram_url: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: uuid.UUID = Field(..., description="The ID of the company")
    created_at: datetime = Field(..., description="The date and time the company was created")
    updated_at: datetime = Field(..., description="The date and time the company was last updated")

    class Config:
        orm_mode = True