"""Integration tests covering seal management API endpoints."""

from __future__ import annotations

from io import BytesIO
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.crud.seal import create_seal
from app.crud.user import create_user
from app.db.session import get_session_factory
from app.models.user import UserRole
from app.services.storage import EncryptedStorageService

SEALS_URL = f"{settings.api_v1_prefix}/pdf/seals"


# Test fixtures
@pytest.fixture()
async def authenticated_client(client: AsyncClient) -> AsyncClient:
    """Return an authenticated HTTP client as a test user."""
    # Create a test user
    session_factory = get_session_factory()
    async with session_factory() as session:
        await create_user(
            session=session,
            email="testuser@example.com",
            password="TestPass123!",
            role=UserRole.USER,
        )

    # Login to get access token
    response = await client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": "testuser@example.com", "password": "TestPass123!"},
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    token = response.json()["access_token"]

    # Add authorization header
    client.headers["Authorization"] = f"Bearer {token}"
    return client


def create_png_bytes() -> bytes:
    """Create valid PNG bytes for testing."""
    # Minimal valid PNG (1x1 pixel, black)
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05"
        b"\x18\r\xad\xf4"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def create_svg_bytes() -> bytes:
    """Create valid SVG bytes for testing."""
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        b"</svg>"
    )


# Upload tests
@pytest.mark.anyio
async def test_upload_seal_successfully(
    authenticated_client: AsyncClient,
) -> None:
    """Test successful seal upload."""
    png_data = create_png_bytes()

    response = await authenticated_client.post(
        SEALS_URL,
        data={
            "name": "Test Seal",
            "description": "A test seal",
        },
        files={"file": ("test.png", BytesIO(png_data), "image/png")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Seal"
    assert data["description"] == "A test seal"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.anyio
async def test_upload_svg_seal(
    authenticated_client: AsyncClient,
) -> None:
    """Test uploading an SVG seal."""
    svg_data = create_svg_bytes()

    response = await authenticated_client.post(
        SEALS_URL,
        data={
            "name": "SVG Seal",
            "description": "An SVG seal",
        },
        files={"file": ("test.svg", BytesIO(svg_data), "image/svg+xml")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "SVG Seal"


@pytest.mark.anyio
async def test_upload_seal_without_authentication(client: AsyncClient) -> None:
    """Test seal upload fails without authentication."""
    png_data = create_png_bytes()

    response = await client.post(
        SEALS_URL,
        data={"name": "Test Seal"},
        files={"file": ("test.png", BytesIO(png_data), "image/png")},
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_upload_seal_with_invalid_format(
    authenticated_client: AsyncClient,
) -> None:
    """Test seal upload rejects invalid file formats."""
    response = await authenticated_client.post(
        SEALS_URL,
        data={"name": "Test Seal"},
        files={"file": ("test.jpg", BytesIO(b"fake jpg data"), "image/jpeg")},
    )

    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_upload_seal_with_invalid_png_signature(
    authenticated_client: AsyncClient,
) -> None:
    """Test seal upload rejects PNG with invalid signature."""
    fake_png = b"This is not a valid PNG file"

    response = await authenticated_client.post(
        SEALS_URL,
        data={"name": "Test Seal"},
        files={"file": ("test.png", BytesIO(fake_png), "image/png")},
    )

    assert response.status_code == 400
    assert "signature" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_upload_seal_with_duplicate_name(
    authenticated_client: AsyncClient,
) -> None:
    """Test that duplicate seal names for same user are rejected."""
    png_data = create_png_bytes()

    # First upload
    response1 = await authenticated_client.post(
        SEALS_URL,
        data={"name": "Duplicate Test"},
        files={"file": ("test1.png", BytesIO(png_data), "image/png")},
    )
    assert response1.status_code == 201

    # Second upload with same name
    response2 = await authenticated_client.post(
        SEALS_URL,
        data={"name": "Duplicate Test"},
        files={"file": ("test2.png", BytesIO(png_data), "image/png")},
    )
    assert response2.status_code == 400


@pytest.mark.anyio
async def test_upload_seal_without_name(
    authenticated_client: AsyncClient,
) -> None:
    """Test seal upload fails without name."""
    png_data = create_png_bytes()

    response = await authenticated_client.post(
        SEALS_URL,
        data={},
        files={"file": ("test.png", BytesIO(png_data), "image/png")},
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.anyio
async def test_upload_seal_with_long_name(
    authenticated_client: AsyncClient,
) -> None:
    """Test seal upload with name exceeding max length."""
    png_data = create_png_bytes()
    long_name = "x" * 121  # Max is 120

    response = await authenticated_client.post(
        SEALS_URL,
        data={"name": long_name},
        files={"file": ("test.png", BytesIO(png_data), "image/png")},
    )

    assert response.status_code == 422


# List tests
@pytest.mark.anyio
async def test_list_seals_empty(
    authenticated_client: AsyncClient,
) -> None:
    """Test listing seals when none exist."""
    response = await authenticated_client.get(SEALS_URL)

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["skip"] == 0
    assert data["limit"] == 10


@pytest.mark.anyio
async def test_list_seals_with_multiple_items(
    authenticated_client: AsyncClient,
) -> None:
    """Test listing multiple seals."""
    png_data = create_png_bytes()

    # Create multiple seals
    for i in range(3):
        response = await authenticated_client.post(
            SEALS_URL,
            data={"name": f"Seal {i+1}"},
            files={"file": (f"test{i}.png", BytesIO(png_data), "image/png")},
        )
        assert response.status_code == 201

    # List seals
    response = await authenticated_client.get(SEALS_URL)

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 3


@pytest.mark.anyio
async def test_list_seals_with_pagination(
    authenticated_client: AsyncClient,
) -> None:
    """Test seal list pagination."""
    png_data = create_png_bytes()

    # Create 5 seals
    for i in range(5):
        response = await authenticated_client.post(
            SEALS_URL,
            data={"name": f"Seal {i+1}"},
            files={"file": (f"test{i}.png", BytesIO(png_data), "image/png")},
        )
        assert response.status_code == 201

    # Get first page (limit 2)
    response = await authenticated_client.get(SEALS_URL, params={"skip": 0, "limit": 2})

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["skip"] == 0
    assert data["limit"] == 2

    # Get second page
    response = await authenticated_client.get(SEALS_URL, params={"skip": 2, "limit": 2})

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["skip"] == 2

    # Get third page (partial)
    response = await authenticated_client.get(SEALS_URL, params={"skip": 4, "limit": 2})

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1


@pytest.mark.anyio
async def test_list_seals_without_authentication(client: AsyncClient) -> None:
    """Test seal list fails without authentication."""
    response = await client.get(SEALS_URL)

    assert response.status_code == 401


@pytest.mark.anyio
async def test_list_seals_only_shows_owned_seals(
    client: AsyncClient,
) -> None:
    """Test that list only shows seals owned by current user."""
    png_data = create_png_bytes()

    # Get admin token
    admin_response = await client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={
            "email": settings.admin_email or "admin@example.com",
            "password": settings.admin_password or "AdminPass123!",
        },
    )
    admin_token = admin_response.json()["access_token"]

    # Admin uploads a seal
    client.headers["Authorization"] = f"Bearer {admin_token}"
    admin_seal_response = await client.post(
        SEALS_URL,
        data={"name": "Admin Seal"},
        files={"file": ("admin.png", BytesIO(png_data), "image/png")},
    )
    assert admin_seal_response.status_code == 201

    # Create and login as test user
    session_factory = get_session_factory()
    async with session_factory() as session:
        await create_user(
            session=session,
            email="otheruser@example.com",
            password="TestPass123!",
            role=UserRole.USER,
        )

    test_user_response = await client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": "otheruser@example.com", "password": "TestPass123!"},
    )
    user_token = test_user_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {user_token}"

    user_seal_response = await client.post(
        SEALS_URL,
        data={"name": "User Seal"},
        files={"file": ("user.png", BytesIO(png_data), "image/png")},
    )
    assert user_seal_response.status_code == 201

    # Test user lists seals
    list_response = await client.get(SEALS_URL)
    assert list_response.status_code == 200
    data = list_response.json()

    # Should only see their own seal
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "User Seal"


# Download tests
@pytest.mark.anyio
async def test_download_seal_image(
    authenticated_client: AsyncClient,
) -> None:
    """Test downloading seal image."""
    png_data = create_png_bytes()

    # Upload seal
    upload_response = await authenticated_client.post(
        SEALS_URL,
        data={"name": "Download Test"},
        files={"file": ("test.png", BytesIO(png_data), "image/png")},
    )
    assert upload_response.status_code == 201
    seal_id = upload_response.json()["id"]

    # Download image
    download_response = await authenticated_client.get(f"{SEALS_URL}/{seal_id}/image")

    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "image/png"
    assert download_response.content == png_data


@pytest.mark.anyio
async def test_download_svg_seal_image(
    authenticated_client: AsyncClient,
) -> None:
    """Test downloading SVG seal image."""
    svg_data = create_svg_bytes()

    # Upload seal
    upload_response = await authenticated_client.post(
        SEALS_URL,
        data={"name": "SVG Download Test"},
        files={"file": ("test.svg", BytesIO(svg_data), "image/svg+xml")},
    )
    assert upload_response.status_code == 201
    seal_id = upload_response.json()["id"]

    # Download image
    download_response = await authenticated_client.get(f"{SEALS_URL}/{seal_id}/image")

    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "image/svg+xml"
    assert download_response.content == svg_data


@pytest.mark.anyio
async def test_download_nonexistent_seal_image(
    authenticated_client: AsyncClient,
) -> None:
    """Test downloading image of non-existent seal."""
    fake_seal_id = str(uuid4())

    response = await authenticated_client.get(f"{SEALS_URL}/{fake_seal_id}/image")

    assert response.status_code == 404


@pytest.mark.anyio
async def test_download_other_users_seal_image(
    client: AsyncClient,
) -> None:
    """Test that users cannot download other users' seal images."""
    png_data = create_png_bytes()

    # Admin uploads a seal
    admin_response = await client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={
            "email": settings.admin_email or "admin@example.com",
            "password": settings.admin_password or "AdminPass123!",
        },
    )
    admin_token = admin_response.json()["access_token"]

    client.headers["Authorization"] = f"Bearer {admin_token}"
    upload_response = await client.post(
        SEALS_URL,
        data={"name": "Admin Seal"},
        files={"file": ("admin.png", BytesIO(png_data), "image/png")},
    )
    assert upload_response.status_code == 201
    admin_seal_id = upload_response.json()["id"]

    # Create and login as test user
    session_factory = get_session_factory()
    async with session_factory() as session:
        await create_user(
            session=session,
            email="otheruser2@example.com",
            password="TestPass123!",
            role=UserRole.USER,
        )

    user_response = await client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": "otheruser2@example.com", "password": "TestPass123!"},
    )
    user_token = user_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {user_token}"

    download_response = await client.get(f"{SEALS_URL}/{admin_seal_id}/image")

    assert download_response.status_code == 403


@pytest.mark.anyio
async def test_download_seal_image_without_authentication(
    client: AsyncClient,
) -> None:
    """Test downloading seal image fails without authentication."""
    fake_seal_id = str(uuid4())

    response = await client.get(f"{SEALS_URL}/{fake_seal_id}/image")

    assert response.status_code == 401


# Delete tests
@pytest.mark.anyio
async def test_delete_seal(
    authenticated_client: AsyncClient,
) -> None:
    """Test deleting a seal."""
    png_data = create_png_bytes()

    # Upload seal
    upload_response = await authenticated_client.post(
        SEALS_URL,
        data={"name": "Delete Test"},
        files={"file": ("test.png", BytesIO(png_data), "image/png")},
    )
    assert upload_response.status_code == 201
    seal_id = upload_response.json()["id"]

    # Delete seal
    delete_response = await authenticated_client.delete(f"{SEALS_URL}/{seal_id}")

    assert delete_response.status_code == 204

    # Verify seal is deleted
    list_response = await authenticated_client.get(SEALS_URL)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 0


@pytest.mark.anyio
async def test_delete_nonexistent_seal(
    authenticated_client: AsyncClient,
) -> None:
    """Test deleting non-existent seal."""
    fake_seal_id = str(uuid4())

    response = await authenticated_client.delete(f"{SEALS_URL}/{fake_seal_id}")

    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_other_users_seal(
    client: AsyncClient,
) -> None:
    """Test that users cannot delete other users' seals."""
    png_data = create_png_bytes()

    # Admin uploads a seal
    admin_response = await client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={
            "email": settings.admin_email or "admin@example.com",
            "password": settings.admin_password or "AdminPass123!",
        },
    )
    admin_token = admin_response.json()["access_token"]

    client.headers["Authorization"] = f"Bearer {admin_token}"
    upload_response = await client.post(
        SEALS_URL,
        data={"name": "Admin Seal"},
        files={"file": ("admin.png", BytesIO(png_data), "image/png")},
    )
    assert upload_response.status_code == 201
    admin_seal_id = upload_response.json()["id"]

    # Create and login as test user
    session_factory = get_session_factory()
    async with session_factory() as session:
        await create_user(
            session=session,
            email="otheruser3@example.com",
            password="TestPass123!",
            role=UserRole.USER,
        )

    user_response = await client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": "otheruser3@example.com", "password": "TestPass123!"},
    )
    user_token = user_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {user_token}"

    delete_response = await client.delete(f"{SEALS_URL}/{admin_seal_id}")

    assert delete_response.status_code == 403

    # Verify seal still exists
    client.headers["Authorization"] = f"Bearer {admin_token}"
    list_response = await client.get(SEALS_URL)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1


@pytest.mark.anyio
async def test_delete_seal_without_authentication(client: AsyncClient) -> None:
    """Test deleting seal fails without authentication."""
    fake_seal_id = str(uuid4())

    response = await client.delete(f"{SEALS_URL}/{fake_seal_id}")

    assert response.status_code == 401
