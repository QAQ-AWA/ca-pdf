"""Database initialization and bootstrap utilities."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.role import ensure_default_roles
from app.crud.user import ensure_admin_user
from app.db import base  # noqa: F401  # Ensure models are imported for metadata
from app.db.base import Base
from app.db.session import get_engine, get_session_factory


async def init_db() -> None:
    """Initialize the database schema."""

    engine = get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def bootstrap_admin() -> None:
    """Create the initial administrator user if configured."""

    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_roles(session)
        await _maybe_create_admin(session=session)


async def _maybe_create_admin(*, session: AsyncSession) -> None:
    if not settings.admin_email or not settings.admin_password:
        return

    await ensure_admin_user(
        session=session,
        email=settings.admin_email,
        password=settings.admin_password,
        role=settings.admin_role,
    )
