from pydantic import BaseModel, Field, validator
from typing import Optional
import uuid
import re

class UserBase(BaseModel):
    email: str = Field(..., description="Valid email address")
    full_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False

class UserCreate(UserBase):
    password: str = Field(..., description="Password must be between 8-128 characters")

    @validator("email")
    def validate_email(cls, v):
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not v or not re.match(email_regex, v):
            raise ValueError("INVALID_EMAIL_FORMAT")
        return v

    @validator("password")
    def validate_password(cls, v):
        if not v or len(v) < 8:
            raise ValueError("PASSWORD_TOO_SHORT")

        if not re.search(r"[A-Z]", v):
            raise ValueError("PASSWORD_MISSING_UPPERCASE")
        if not re.search(r"[a-z]", v):
            raise ValueError("PASSWORD_MISSING_LOWERCASE")
        if not re.search(r"\d", v):
            raise ValueError("PASSWORD_MISSING_DIGIT")

        return v

class UserResponse(UserBase):
    id: uuid.UUID

    class Config:
        from_attributes = True