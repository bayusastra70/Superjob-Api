# from pydantic import BaseModel, EmailStr, Field
# from typing import Optional

# class UserBase(BaseModel):
#     email: EmailStr
#     username: str = Field(..., min_length=3, max_length=50)
#     full_name: Optional[str] = None
#     is_active: Optional[bool] = True

# class UserCreate(BaseModel):
#     email: EmailStr
#     username: str = Field(..., min_length=3, max_length=50)
#     password: str = Field(..., min_length=6, max_length=72)  # Max 72 for bcrypt
#     full_name: Optional[str] = None

# class UserLogin(BaseModel):
#     email: EmailStr
#     password: str

# class UserResponse(UserBase):
#     id: int
#     is_superuser: bool = False

#     class Config:
#         from_attributes = True

# # Juga update OdooUser schema jika masih diperlukan
# class OdooUser(BaseModel):
#     id: int
#     name: str
#     email: str
#     partner_id: int

from pydantic import BaseModel
from typing import Optional

from pydantic import BaseModel, EmailStr, validator
from datetime import datetime

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "candidate"
    
    @validator('role')
    def validate_role(cls, v):
        if v is None or v == "":
            return "candidate"
        
        if v not in ['admin', 'employer', 'candidate']:
            raise ValueError('Role must be one of: admin, employer, candidate')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower() 

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: Optional[bool] = False

    role: Optional[str] = ""
    
    class Config:
        from_attributes = True

# Hapus OdooUser jika tidak digunakan
# class OdooUser(BaseModel):
#     id: int
#     name: str
#     email: str
#     partner_id: int