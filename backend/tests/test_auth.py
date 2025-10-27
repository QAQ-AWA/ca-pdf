"""Integration tests covering authentication flows."""

from __future__ import annotations

import os

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.crud.user import create_user
from app.db.session import get_session_factory
from app.models.user import UserRole

LOGIN_URL = f"{settings.api_v1_prefix}/auth/login"
REFRESH_URL = f"{settings.api_v1_prefix}/auth/refresh"
LOGOUT_URL = f"{settings.api_v1_prefix}/auth/logout"
ME_URL = f"{settings.api_v1_prefix}/auth/me"
ADMIN_PING_URL = f"{settings.api_v1_prefix}/auth/admin/ping"

ADMIN_EMAIL = settings.admin_email or os.environ.get("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = settings.admin_password or os.environ.get(
    "ADMIN_PASSWORD", "AdminPass123!"
)


@pytest.mark.anyio
async def test_login_returns_tokens(client: AsyncClient) -> None:
    response = await client.post(
        LOGIN_URL,
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_with_invalid_credentials_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        LOGIN_URL,
        json={"email": ADMIN_EMAIL, "password": "incorrect"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.anyio
async def test_refresh_flow_rotates_tokens(client: AsyncClient) -> None:
    login_response = await client.post(
        LOGIN_URL,
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    login_data = login_response.json()

    refresh_response = await client.post(
        REFRESH_URL,
        json={"refresh_token": login_data["refresh_token"]},
    )

    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()
    assert refreshed["access_token"] != login_data["access_token"]
    assert refreshed["refresh_token"] != login_data["refresh_token"]

    reuse_response = await client.post(
        REFRESH_URL,
        json={"refresh_token": login_data["refresh_token"]},
    )

    assert reuse_response.status_code == 401
    assert reuse_response.json()["detail"] == "Token has been revoked"


@pytest.mark.anyio
async def test_logout_revokes_tokens(client: AsyncClient) -> None:
    login_response = await client.post(
        LOGIN_URL,
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    login_data = login_response.json()

    logout_response = await client.post(
        LOGOUT_URL,
        headers={"Authorization": f"Bearer {login_data['access_token']}"},
        json={"refresh_token": login_data["refresh_token"]},
    )

    assert logout_response.status_code == 200

    me_response = await client.get(
        ME_URL,
        headers={"Authorization": f"Bearer {login_data['access_token']}"},
    )

    assert me_response.status_code == 401
    assert me_response.json()["detail"] in {
        "Token has been revoked",
        "Not authenticated",
    }

    refresh_response = await client.post(
        REFRESH_URL,
        json={"refresh_token": login_data["refresh_token"]},
    )

    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] in {
        "Token has been revoked",
        "Invalid refresh token",
    }


@pytest.mark.anyio
async def test_admin_route_requires_admin_role(client: AsyncClient) -> None:
    admin_login = await client.post(
        LOGIN_URL,
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    admin_access = admin_login.json()["access_token"]

    admin_response = await client.get(
        ADMIN_PING_URL,
        headers={"Authorization": f"Bearer {admin_access}"},
    )
    assert admin_response.status_code == 200
    assert admin_response.json()["detail"] == "admin-ok"

    session_factory = get_session_factory()
    async with session_factory() as session:
        await create_user(
            session=session,
            email="user@example.com",
            password="UserPassword123!",
            role=UserRole.USER,
        )

    user_login = await client.post(
        LOGIN_URL,
        json={"email": "user@example.com", "password": "UserPassword123!"},
    )
    user_access = user_login.json()["access_token"]

    forbidden_response = await client.get(
        ADMIN_PING_URL,
        headers={"Authorization": f"Bearer {user_access}"},
    )

    assert forbidden_response.status_code == 403
    assert forbidden_response.json()["detail"] in {
        "Insufficient permissions",
        "User is inactive",
    }


@pytest.mark.anyio
async def test_rate_limit_applies_to_failed_logins(client: AsyncClient) -> None:
    for _ in range(settings.auth_rate_limit_requests):
        response = await client.post(
            LOGIN_URL,
            json={"email": ADMIN_EMAIL, "password": "bad-password"},
        )
        assert response.status_code == 401

    blocked_response = await client.post(
        LOGIN_URL,
        json={"email": ADMIN_EMAIL, "password": "bad-password"},
    )

    assert blocked_response.status_code == 429
    assert "Too many" in blocked_response.json()["detail"]
