"""Authentication and authorization API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_roles
from app.core.config import settings
from app.core.security import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.crud import token as token_crud
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, TokenPayload, TokenResponse
from app.schemas.user import UserRead
from app.services.rate_limiter import RateLimiter

router = APIRouter()
_http_bearer = HTTPBearer(auto_error=False)
_auth_rate_limiter = RateLimiter(
    requests=settings.auth_rate_limit_requests,
    window_seconds=settings.auth_rate_limit_window_seconds,
)


@router.post("/login", response_model=TokenResponse, tags=["auth"])
async def login(
    payload: LoginRequest,
    session: Session = Depends(get_db),
    _: None = Depends(_auth_rate_limiter),
) -> TokenResponse:
    """Authenticate a user and return a pair of access and refresh tokens."""

    user = user_crud.authenticate_user(session=session, email=payload.email, password=payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(subject=str(user.id), role=user.role)
    refresh_token = create_refresh_token(subject=str(user.id), role=user.role)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", tags=["auth"])
async def logout(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    _: None = Depends(_auth_rate_limiter),
    credentials: HTTPAuthorizationCredentials | None = Depends(_http_bearer),
) -> dict[str, str]:
    """Revoke the supplied refresh token and invalidate the active access token."""

    token_payload = _decode_refresh_token_or_raise(payload.refresh_token)
    _validate_token_ownership(token_payload, current_user)

    token_crud.revoke_token(
        session=session,
        jti=token_payload.jti,
        token_type=token_payload.type,
        user_id=current_user.id,
    )

    if credentials is not None:
        try:
            access_payload = decode_token(credentials.credentials)
        except InvalidTokenError:
            access_payload = None
        else:
            if access_payload.type == "access":
                token_crud.revoke_token(
                    session=session,
                    jti=access_payload.jti,
                    token_type=access_payload.type,
                    user_id=current_user.id,
                )

    return {"detail": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse, tags=["auth"])
async def refresh_tokens(
    payload: RefreshRequest,
    session: Session = Depends(get_db),
    _: None = Depends(_auth_rate_limiter),
) -> TokenResponse:
    """Rotate refresh tokens and issue a new token pair."""

    token_payload = _decode_refresh_token_or_raise(payload.refresh_token)

    if token_crud.is_token_revoked(session=session, jti=token_payload.jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    try:
        user_id = int(token_payload.sub)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid subject claim") from exc

    user = user_crud.get_user_by_id(session=session, user_id=user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authorized")

    # Revoke the used refresh token to enforce rotation
    token_crud.revoke_token(
        session=session,
        jti=token_payload.jti,
        token_type=token_payload.type,
        user_id=user.id,
    )

    access_token = create_access_token(subject=str(user.id), role=user.role)
    refresh_token = create_refresh_token(subject=str(user.id), role=user.role)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserRead, tags=["auth"])
async def read_profile(current_user: User = Depends(get_current_user)) -> UserRead:
    """Return the authenticated user's profile."""

    return UserRead.model_validate(current_user)


@router.get("/admin/ping", tags=["auth"])
async def admin_ping(_: User = Depends(require_roles(UserRole.ADMIN))) -> dict[str, str]:
    """A protected endpoint demonstrating role-based access control."""

    return {"detail": "admin-ok"}


def _decode_refresh_token_or_raise(refresh_token: str) -> TokenPayload:
    try:
        token_payload = decode_token(refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    if token_payload.type != "refresh":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wrong token type")

    return token_payload


def _validate_token_ownership(token_payload: TokenPayload, user: User) -> None:
    if token_payload.sub != str(user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token does not belong to user")
