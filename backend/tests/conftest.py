"""Pytest configuration and common fixtures for backend tests."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator

import pytest
from cryptography.fernet import Fernet
from httpx import AsyncClient

# Configure environment variables for deterministic tests before importing app modules
os.environ.setdefault("APP_NAME", "Test API")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_app.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "2")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_MINUTES", "10")
os.environ.setdefault("BACKEND_CORS_ORIGINS", '["http://testclient"]')
os.environ.setdefault("AUTH_RATE_LIMIT_REQUESTS", "5")
os.environ.setdefault("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_PASSWORD", "AdminPass123!")
os.environ.setdefault("ADMIN_ROLE", "admin")
os.environ.setdefault("ENCRYPTED_STORAGE_ALGORITHM", "fernet")
os.environ.setdefault("ENCRYPTED_STORAGE_MASTER_KEY", Fernet.generate_key().decode())

from app.api.endpoints.auth import _auth_rate_limiter
from app.core.config import reload_settings, settings
from app.db.base import Base
from app.db.init_db import bootstrap_admin
from app.db.session import get_engine, refresh_session_factory
from app.main import create_application

# Ensure settings and database connections are refreshed based on test environment
reload_settings()

if settings.async_database_url.startswith("sqlite"):
    db_uri = settings.async_database_url.replace("sqlite+aiosqlite:///", "")
    db_path = Path(db_uri)
    if db_path.exists():
        db_path.unlink()

# Recreate the application instance with the testing configuration
import app.main as app_main

app_main.app = create_application()


@pytest.fixture(scope="function", autouse=True)
async def reset_state() -> AsyncGenerator[None, None]:
    """Reset database schema and rate limiter state before each test."""

    await refresh_session_factory()
    engine = get_engine()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    await bootstrap_admin()
    await _auth_rate_limiter.reset()

    yield

    # Cleanup after test
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
    finally:
        # Dispose of engine to close all connections
        await engine.dispose(close=True)


@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an asynchronous HTTP client bound to the FastAPI app."""

    async with AsyncClient(
        app=app_main.app, base_url="http://testserver"
    ) as async_client:
        yield async_client
