from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.main import app


@pytest.mark.anyio
async def test_health_endpoint_returns_ok_status() -> None:
    """Test that the basic health endpoint returns success."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": settings.app_name}


@pytest.mark.anyio
async def test_ping_endpoint_returns_pong() -> None:
    """Test that the ping endpoint returns pong quickly."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/ping")

    assert response.status_code == 200
    assert response.json() == {"status": "pong", "service": settings.app_name}


@pytest.mark.anyio
async def test_health_db_endpoint_returns_connected_status() -> None:
    """Test that the database health endpoint returns success when DB is available."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/health/db")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == settings.app_name
    assert data["database"] == "connected"
    assert "timestamp" in data


@pytest.mark.anyio
async def test_health_db_endpoint_handles_database_failure() -> None:
    """Test that the database health endpoint returns 503 when DB is unavailable."""
    # Mock the database engine to raise SQLAlchemyError
    mock_conn = AsyncMock()
    mock_conn.__aenter__.side_effect = SQLAlchemyError("Connection failed")
    mock_engine = AsyncMock()
    mock_engine.connect.return_value = mock_conn

    with patch("app.api.routes.get_engine", return_value=mock_engine):
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            response = await client.get("/health/db")

    assert response.status_code == 503
    # The exception might be caught as a generic exception depending on the exact type
    detail = response.json()["detail"]
    assert detail in ["Database connectivity failed", "Database health check failed"]


@pytest.mark.anyio
async def test_health_db_endpoint_handles_unexpected_error() -> None:
    """Test that the database health endpoint returns 503 on unexpected errors."""
    # Mock the database engine to raise a generic exception
    mock_conn = AsyncMock()
    mock_conn.__aenter__.side_effect = Exception("Unexpected error")
    mock_engine = AsyncMock()
    mock_engine.connect.return_value = mock_conn

    with patch("app.api.routes.get_engine", return_value=mock_engine):
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            response = await client.get("/health/db")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database health check failed"}


@pytest.mark.anyio
async def test_health_endpoint_responds_quickly() -> None:
    """Test that health endpoint responds within acceptable time limits."""
    import time

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        start_time = time.time()
        response = await client.get("/health")
        end_time = time.time()

    # Should respond within 100ms even under load
    response_time = end_time - start_time
    assert response.status_code == 200
    assert (
        response_time < 0.1
    ), f"Health check took {response_time:.3f}s, expected < 0.1s"


@pytest.mark.anyio
async def test_ping_endpoint_responds_quickly() -> None:
    """Test that ping endpoint responds within acceptable time limits."""
    import time

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        start_time = time.time()
        response = await client.get("/ping")
        end_time = time.time()

    # Should respond within 50ms (minimal endpoint)
    response_time = end_time - start_time
    assert response.status_code == 200
    assert (
        response_time < 0.05
    ), f"Ping check took {response_time:.3f}s, expected < 0.05s"


@pytest.mark.anyio
async def test_health_db_endpoint_responds_quickly_on_success() -> None:
    """Test that database health endpoint responds quickly on success."""
    import time

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        start_time = time.time()
        response = await client.get("/health/db")
        end_time = time.time()

    # Should respond within 500ms even with DB query
    response_time = end_time - start_time
    assert response.status_code == 200
    assert (
        response_time < 0.5
    ), f"DB health check took {response_time:.3f}s, expected < 0.5s"


@pytest.mark.anyio
async def test_health_db_endpoint_responds_quickly_on_failure() -> None:
    """Test that database health endpoint fails fast on DB issues."""
    import time

    # Mock the database engine to raise SQLAlchemyError immediately
    mock_conn = AsyncMock()
    mock_conn.__aenter__.side_effect = SQLAlchemyError("Connection failed")
    mock_engine = AsyncMock()
    mock_engine.connect.return_value = mock_conn

    with patch("app.api.routes.get_engine", return_value=mock_engine):
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            start_time = time.time()
            response = await client.get("/health/db")
            end_time = time.time()

    # Should fail quickly within 100ms
    response_time = end_time - start_time
    assert response.status_code == 503
    assert (
        response_time < 0.1
    ), f"DB health check failure took {response_time:.3f}s, expected < 0.1s"
