from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
import re

class CompanyData(BaseModel):
    name: str = Field(..., max_length=255)
    industry: str = Field(..., max_length=100)
    description: str
    website: str = Field(..., max_length=255)
    location: str
    logo_url: str = Field(..., max_length=255)
    founded_year: Optional[int] = None
    employee_size: Optional[str] = None
    linkedin_url: str = Field("", max_length=255)
    twitter_url: str = Field("", max_length=255)
    instagram_url: str = Field("", max_length=255)

class AdminUserData(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)

    @validator('phone')
    def validate_phone(cls, v):
        phone_digits = re.sub(r'\D', '', v)
        if len(phone_digits) < 10 or len(phone_digits) > 15:
            raise ValueError('Phone number must be 10-15 digits')
        if not phone_digits.startswith(('08', '62', '0')):
             raise ValueError('Invalid phone format')
        
        if phone_digits.startswith('0'):
            phone_digits = '62' + phone_digits[1:]
        elif phone_digits.startswith('+62'):
            phone_digits = phone_digits[1:]
        
        return phone_digits

    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least 1 uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least 1 lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least 1 digit')
        return v

class CompanyRegisterRequest(BaseModel):
    company: CompanyData
    user: AdminUserData

class CompanyRegisterResponse(BaseModel):
    success: bool
    company_id: int
    user_id: int
