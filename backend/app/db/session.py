"""SQLAlchemy session and engine configuration."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _build_engine() -> Engine:
    connect_args: dict[str, object] = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(settings.database_url, connect_args=connect_args)


def _build_sessionmaker(bind_engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=bind_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


engine: Engine = _build_engine()
SessionLocal = _build_sessionmaker(engine)


def refresh_session_factory() -> None:
    """Recreate the engine and session factory using current settings."""

    global engine, SessionLocal
    engine = _build_engine()
    SessionLocal = _build_sessionmaker(engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for request-scoped usage."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
