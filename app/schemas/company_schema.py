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
    nib_document_url: Optional[str] = Field(None, description="The URL for the NIB document")

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
    nib_document_url: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: int = Field(..., description="The ID of the company")
    created_at: datetime = Field(..., description="The date and time the company was created")
    updated_at: datetime = Field(..., description="The date and time the company was last updated")

    class Config:
        from_attributes = True


class CompanyUserResponse(BaseModel):
    """Schema for user with role information in company context"""
    id: int
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    default_role_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PaginationInfo(BaseModel):
    """Pagination information"""
    page: int
    limit: int
    total_count: int
    total_pages: int
    has_next: bool
    has_prev: bool


class FilterInfo(BaseModel):
    """Filter information"""
    search: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


class CompanyUsersData(BaseModel):
    """Data object for company users list"""
    items: list[CompanyUserResponse]
    page: int
    total: int
    limit: int

class CompanyUsersListResponse(BaseModel):
    """Unified response for company users list"""
    code: int = 200
    is_success: bool = True
    message: str = "Success"
    data: CompanyUsersData


class CreateCompanyUser(BaseModel):
    """Schema for creating a new user in a company"""
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="User full name")
    username: str = Field(..., description="Unique username")
    phone: Optional[str] = Field(None, description="User phone number")
    role_id: int = Field(..., description="Role ID for the user")
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")


class UpdateCompanyUser(BaseModel):
    """Schema for updating an existing user in a company"""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


class CreateCompanyUserResponse(BaseModel):
    """Response after creating a user"""
    success: bool = True
    message: str
    user: CompanyUserResponse


class UpdateCompanyUserResponse(BaseModel):
    """Response after updating a user"""
    success: bool = True
    message: str
    user: CompanyUserResponse