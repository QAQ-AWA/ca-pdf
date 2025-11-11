"""Debug test."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.anyio
async def test_login_debug(client: AsyncClient) -> None:
    response = await client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": settings.admin_email, "password": settings.admin_password},
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
