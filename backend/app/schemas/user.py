"""Pydantic schemas representing user-facing data structures."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole
    is_active: bool = True


class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserInDB(UserBase):
    hashed_password: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="user", pattern="^(user|admin)$")
    is_active: bool = True

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Validate that username is alphanumeric with allowed special chars."""
        if not all(c.isalnum() or c in "_-" for c in v):
            raise ValueError(
                "Username must be alphanumeric with underscores or hyphens"
            )
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Complete user response schema."""

    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list response."""

    items: list[UserResponse]
    total_count: int
    skip: int
    limit: int


class ResetPasswordRequest(BaseModel):
    """Schema for resetting user password."""

    new_password: str = Field(..., min_length=8, max_length=128)
