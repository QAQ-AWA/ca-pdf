"""CRUD helpers for token revocation tracking."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import TokenBlocklist


async def is_token_revoked(*, session: AsyncSession, jti: str) -> bool:
    """Return True if the supplied token identifier has been revoked."""

    statement = select(TokenBlocklist).where(TokenBlocklist.jti == jti)
    result = await session.execute(statement)
    return result.scalar_one_or_none() is not None


async def revoke_token(
    *,
    session: AsyncSession,
    jti: str,
    token_type: str,
    user_id: int | None,
) -> TokenBlocklist:
    """Persist a token identifier in the blocklist."""

    statement = select(TokenBlocklist).where(TokenBlocklist.jti == jti)
    result = await session.execute(statement)
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    token = TokenBlocklist(jti=jti, token_type=token_type, user_id=user_id)
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return token
