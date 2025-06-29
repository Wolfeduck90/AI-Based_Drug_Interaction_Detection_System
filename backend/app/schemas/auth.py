"""
Authentication and user schemas
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    DOCTOR = "doctor"
    PHARMACIST = "pharmacist"
    ADMIN = "admin"

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[datetime] = None
    emergency_contact: Optional[str] = Field(None, max_length=500)
    allergies: Optional[List[str]] = []
    medical_conditions: Optional[List[str]] = []

class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=6, max_length=128)
    role: UserRole = UserRole.USER
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserUpdate(BaseModel):
    """User update schema"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[datetime] = None
    emergency_contact: Optional[str] = Field(None, max_length=500)
    allergies: Optional[List[str]] = None
    medical_conditions: Optional[List[str]] = None

class UserInDB(UserBase):
    """User schema for database operations"""
    id: int
    password_hash: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserResponse(UserBase):
    """User response schema (public data)"""
    id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str

class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    """Token data schema"""
    user_id: Optional[int] = None
    email: Optional[str] = None

class AuthResponse(BaseModel):
    """Authentication response schema"""
    user: UserResponse
    token: Token

class PasswordChange(BaseModel):
    """Password change schema"""
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('New password must be at least 6 characters long')
        return v

class PasswordReset(BaseModel):
    """Password reset schema"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str
    new_password: str = Field(..., min_length=6, max_length=128)