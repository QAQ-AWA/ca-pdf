import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.anyio
async def test_health_endpoint_returns_ok_status(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == settings.app_name
    assert payload["checks"]["live"]["status"] == "ok"
    assert "x-request-id" in {key.lower() for key in response.headers}


@pytest.mark.anyio
async def test_readiness_endpoint_reports_database(client: AsyncClient) -> None:
    response = await client.get("/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["checks"]["database"]["status"] == "ok"


@pytest.mark.anyio
async def test_metrics_endpoint_exposes_prometheus_metrics(client: AsyncClient) -> None:
    response = await client.get("/metrics")

    assert response.status_code == 200
    body = response.text
    assert "http_requests_total" in body or "starlette_requests_total" in body
