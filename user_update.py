from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re

class UserUpdate(BaseModel):
    """Enhanced model for updating user information"""
    username: Optional[str] = Field(
        None, 
        min_length=3, 
        max_length=50,
        description="Username must be between 3 and 50 characters"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Valid email address"
    )
    phone_number: Optional[str] = Field(
        None, 
        min_length=10, 
        max_length=20,
        description="Phone number must be between 10 and 20 characters"
    )
    password: Optional[str] = Field(
        None, 
        min_length=6,
        description="Password must be at least 6 characters long"
    )
    current_password: Optional[str] = Field(
        None,
        description="Current password required for password updates"
    )
    
    @field_validator('username')
    def validate_username(cls, v):
        if v is not None:
            # Username should only contain alphanumeric characters and underscores
            if not re.match(r'^[a-zA-Z0-9_]+$', v):
                raise ValueError('Username can only contain letters, numbers, and underscores')
        return v
    
    @field_validator('phone_number')
    def validate_phone_number(cls, v):
        if v is not None:
            # Remove any non-digit characters for validation
            digits_only = re.sub(r'\D', '', v)
            if len(digits_only) < 10:
                raise ValueError('Phone number must contain at least 10 digits')
        return v
    
    @field_validator('password')
    def validate_password(cls, v):
        if v is not None:
            # Add password strength requirements
            if len(v) < 6:
                raise ValueError('Password must be at least 6 characters long')
            # Optional: Add more complex requirements
            # if not re.search(r'[A-Za-z]', v) or not re.search(r'\d', v):
            #     raise ValueError('Password must contain both letters and numbers')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe_updated",
                "email": "john.updated@example.com",
                "phone_number": "+1234567891",
                "current_password": "oldpassword123",
                "password": "newpassword123"
            }
        }