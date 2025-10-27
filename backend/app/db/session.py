"""SQLAlchemy async session and engine configuration."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


def _build_engine() -> AsyncEngine:
    return create_async_engine(
        settings.async_database_url,
        echo=settings.database_echo,
        pool_pre_ping=True,
    )


def _build_sessionmaker(bind_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind_engine,
        autoflush=False,
        expire_on_commit=False,
    )


def _ensure_session_factory() -> None:
    global engine, SessionLocal
    if engine is None or SessionLocal is None:
        bind_engine = _build_engine()
        engine = bind_engine
        SessionLocal = _build_sessionmaker(bind_engine)


def get_engine() -> AsyncEngine:
    """Return the lazily constructed async engine."""

    _ensure_session_factory()
    assert engine is not None  # For type checkers
    return engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the lazily constructed async sessionmaker."""

    _ensure_session_factory()
    assert SessionLocal is not None  # For type checkers
    return SessionLocal


async def refresh_session_factory() -> None:
    """Recreate the engine and session factory using the latest settings."""

    global engine, SessionLocal
    if engine is not None:
        await engine.dispose()
    bind_engine = _build_engine()
    engine = bind_engine
    SessionLocal = _build_sessionmaker(bind_engine)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield an async database session for request-scoped usage."""

    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session
