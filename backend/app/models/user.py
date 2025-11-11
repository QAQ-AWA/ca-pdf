"""Database models related to user accounts and authentication."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base_class import Base
from app.models.role import Role, RoleSlug

UserRole = RoleSlug


class User(Base):
    """User account stored in the relational database."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    _role_slug: Mapped[str] = mapped_column(
        "role",
        String(50),
        ForeignKey("roles.slug", ondelete="RESTRICT"),
        nullable=False,
        default=UserRole.USER.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    role_relationship: Mapped[Optional[Role]] = relationship(
        Role,
        back_populates="users",
        lazy="joined",
    )

    revoked_tokens: Mapped[list["TokenBlocklist"]] = relationship(
        "TokenBlocklist",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property
    def role(self) -> str:
        return self._role_slug

    @role.setter
    def role(self, value: str | UserRole) -> None:
        if isinstance(value, UserRole):
            self._role_slug = value.value
        else:
            self._role_slug = value.lower()

    def role_enum(self) -> UserRole:
        return UserRole(self._role_slug)


class TokenBlocklist(Base):
    """Represents revoked JWT tokens."""

    __tablename__ = "token_blocklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    jti: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    token_type: Mapped[str] = mapped_column(String(16), nullable=False)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL")
    )
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped[User | None] = relationship("User", back_populates="revoked_tokens")
