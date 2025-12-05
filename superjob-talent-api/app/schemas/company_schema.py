from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid

class CompanyBase(BaseModel):
    name: str = Field(..., max_length=255)
    industry: str = Field(..., max_length=100)
    description: str
    website_url: str = Field(..., max_length=255)
    address: str
    logo_url: str = Field(..., max_length=255)

class CompanyCreate(CompanyBase):
    created_by: uuid.UUID = Field(..., description="The ID of the user who created the company")

class CompanyUpdate(CompanyBase):
    name: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: uuid.UUID = Field(..., description="The ID of the company")
    created_at: datetime = Field(..., description="The date and time the company was created")
    updated_at: datetime = Field(..., description="The date and time the company was last updated")

    class Config:
        orm_mode = True