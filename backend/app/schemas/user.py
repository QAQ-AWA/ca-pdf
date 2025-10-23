"""Pydantic schemas representing user-facing data structures."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr

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
