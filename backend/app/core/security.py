"""Security utilities for password hashing and JWT management."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal, cast
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.schemas.auth import TokenPayload

try:
    import bcrypt
except ImportError:  # pragma: no cover - bcrypt backend not available
    bcrypt = None  # type: ignore[assignment]
else:
    _original_hashpw = bcrypt.hashpw
    _original_checkpw = getattr(bcrypt, "checkpw", None)

    def _hashpw_with_truncation(password: bytes, salt: bytes) -> bytes:
        if len(password) > 72:
            password = password[:72]
        return _original_hashpw(password, salt)

    def _checkpw_with_truncation(password: bytes, hashed: bytes) -> bool:
        if len(password) > 72:
            password = password[:72]
        if _original_checkpw is None:
            return False
        return bool(_original_checkpw(password, hashed))

    bcrypt.hashpw = _hashpw_with_truncation  # type: ignore[assignment]
    if _original_checkpw is not None:
        bcrypt.checkpw = _checkpw_with_truncation  # type: ignore[assignment]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TokenType = Literal["access", "refresh"]


class InvalidTokenError(Exception):
    """Raised when a JWT cannot be decoded or is otherwise invalid."""


def _normalize_password_for_bcrypt(password: str) -> str:
    """Encode the password to UTF-8 and truncate to 72 bytes for bcrypt."""

    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return password_bytes.decode("utf-8", errors="ignore")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if the provided password matches the stored hash."""

    normalized = _normalize_password_for_bcrypt(plain_password)
    return bool(pwd_context.verify(normalized, hashed_password))


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt."""

    normalized = _normalize_password_for_bcrypt(password)
    hashed = pwd_context.hash(normalized)
    return cast(str, hashed)


def _create_token(
    *, subject: str, role: str, token_type: TokenType, expires_delta: timedelta
) -> str:
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
    return _create_token(
        subject=subject, role=role, token_type="access", expires_delta=expires_delta
    )


def create_refresh_token(*, subject: str, role: str) -> str:
    """Create a signed JWT refresh token for the given subject."""

    expires_delta = timedelta(minutes=settings.refresh_token_expire_minutes)
    return _create_token(
        subject=subject, role=role, token_type="refresh", expires_delta=expires_delta
    )


def decode_token(token: str) -> TokenPayload:
    """Decode a JWT and return its payload if valid."""

    try:
        decoded = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as exc:  # pragma: no cover - protective branch
        raise InvalidTokenError("Token decode failed") from exc

    payload = cast(dict[str, Any], decoded)

    try:
        return TokenPayload(**payload)
    except ValueError as exc:  # pragma: no cover - protective branch
        raise InvalidTokenError("Token payload invalid") from exc
