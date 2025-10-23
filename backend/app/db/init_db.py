"""Database initialization and bootstrap utilities."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import base  # noqa: F401  # Ensure models are imported for metadata
from app.db.base import Base
from app.db.session import SessionLocal, engine


def init_db() -> None:
    """Initialize the database schema."""

    Base.metadata.create_all(bind=engine)


def bootstrap_admin() -> None:
    """Create the initial administrator user if configured."""

    if not settings.admin_email or not settings.admin_password:
        return

    with SessionLocal() as session:
        _ensure_admin_user(session=session)


def _ensure_admin_user(*, session: Session) -> None:
    from app.crud.user import ensure_admin_user

    ensure_admin_user(
        session=session,
        email=settings.admin_email,
        password=settings.admin_password,
        role=settings.admin_role,
    )
