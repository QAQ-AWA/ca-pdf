"""Security utilities for password hashing and JWT management."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal, cast
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.schemas.auth import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TokenType = Literal["access", "refresh"]


class InvalidTokenError(Exception):
    """Raised when a JWT cannot be decoded or is otherwise invalid."""


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if the provided password matches the stored hash."""

    return bool(pwd_context.verify(plain_password, hashed_password))


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt."""

    hashed = pwd_context.hash(password)
    return cast(str, hashed)


def _create_token(*, subject: str, role: str, token_type: TokenType, expires_delta: timedelta) -> str:
    expiration = datetime.now(tz=timezone.utc) + expires_delta
    to_encode = {
        "exp": expiration,
        "sub": subject,
        "type": token_type,
        "role": role,
        "jti": str(uuid4()),
    }
    token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return cast(str, token)


def create_access_token(*, subject: str, role: str) -> str:
    """Create a signed JWT access token for the given subject."""

    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    return _create_token(subject=subject, role=role, token_type="access", expires_delta=expires_delta)


def create_refresh_token(*, subject: str, role: str) -> str:
    """Create a signed JWT refresh token for the given subject."""

    expires_delta = timedelta(minutes=settings.refresh_token_expire_minutes)
    return _create_token(subject=subject, role=role, token_type="refresh", expires_delta=expires_delta)


def decode_token(token: str) -> TokenPayload:
    """Decode a JWT and return its payload if valid."""

    try:
        decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:  # pragma: no cover - protective branch
        raise InvalidTokenError("Token decode failed") from exc

    payload = cast(dict[str, Any], decoded)

    try:
        return TokenPayload(**payload)
    except ValueError as exc:  # pragma: no cover - protective branch
        raise InvalidTokenError("Token payload invalid") from exc
