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

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: Optional[bool] = False
    
    class Config:
        from_attributes = True

# Hapus OdooUser jika tidak digunakan
# class OdooUser(BaseModel):
#     id: int
#     name: str
#     email: str
#     partner_id: int