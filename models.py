from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Model for creating a new user"""
    username: str = Field(..., min_length=3, max_length=50, description="Username must be between 3 and 50 characters")
    email: EmailStr = Field(..., description="Valid email address required")
    phone_number: str = Field(..., min_length=10, max_length=20, description="Phone number must be between 10 and 20 characters")
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters long")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john.doe@example.com",
                "phone_number": "+1234567890",
                "password": "securepassword123"
            }
        }

class UserResponse(BaseModel):
    """Model for user response (without password)"""
    id: int
    username: str
    email: str
    phone_number: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "john_doe",
                "email": "john.doe@example.com",
                "phone_number": "+1234567890",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }

class UserUpdate(BaseModel):
    """Model for updating user information"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    password: Optional[str] = Field(None, min_length=6)
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe_updated",
                "email": "john.updated@example.com",
                "phone_number": "+1234567891"
            }
        }

class UserLogin(BaseModel):
    """Model for user login"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "securepassword123"
            }
        }

class Token(BaseModel):
    """Model for authentication token"""
    access_token: str
    token_type: str = "bearer"
    
class TokenData(BaseModel):
    """Model for token data"""
    username: Optional[str] = None

class APIResponse(BaseModel):
    """Generic API response model"""
    success: bool
    message: str
    data: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {}
            }
        }