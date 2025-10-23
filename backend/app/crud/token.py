"""CRUD helpers for token revocation tracking."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import TokenBlocklist


def is_token_revoked(*, session: Session, jti: str) -> bool:
    """Return True if the supplied token identifier has been revoked."""

    statement = select(TokenBlocklist).where(TokenBlocklist.jti == jti)
    return session.scalar(statement) is not None


def revoke_token(
    *,
    session: Session,
    jti: str,
    token_type: str,
    user_id: int | None,
) -> TokenBlocklist:
    """Persist a token identifier in the blocklist."""

    statement = select(TokenBlocklist).where(TokenBlocklist.jti == jti)
    existing = session.scalar(statement)
    if existing is not None:
        return existing

    token = TokenBlocklist(jti=jti, token_type=token_type, user_id=user_id)
    session.add(token)
    session.commit()
    session.refresh(token)
    return token
