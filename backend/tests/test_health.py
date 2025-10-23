import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.main import app


@pytest.mark.anyio
async def test_health_endpoint_returns_ok_status() -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": settings.app_name}
