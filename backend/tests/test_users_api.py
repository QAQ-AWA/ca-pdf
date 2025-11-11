"""Integration tests for user management API endpoints."""

from __future__ import annotations

import os

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.crud.user import create_user, get_user_by_id, get_user_by_username
from app.db.session import get_session_factory
from app.models.user import UserRole

USERS_URL = f"{settings.api_v1_prefix}/users"

ADMIN_EMAIL = settings.admin_email or os.environ.get("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = settings.admin_password or os.environ.get(
    "ADMIN_PASSWORD", "AdminPass123!"
)


class TestListUsers:
    """Tests for GET /api/v1/users endpoint."""

    @pytest.mark.anyio
    async def test_list_users_requires_admin(self, client: AsyncClient) -> None:
        """Only admins can list users."""
        response = await client.get(USERS_URL)
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_list_users_admin_access(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Admin can list users."""
        response = await client.get(
            USERS_URL,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_count" in data
        assert "skip" in data
        assert "limit" in data
        assert data["total_count"] >= 1

    @pytest.mark.anyio
    async def test_list_users_pagination(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Pagination works correctly."""
        response = await client.get(
            f"{USERS_URL}?skip=0&limit=5",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 5

    @pytest.mark.anyio
    async def test_list_users_search(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Search functionality works."""
        response = await client.get(
            f"{USERS_URL}?search=admin",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 0

    @pytest.mark.anyio
    async def test_list_users_filter_by_role(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Filter by role works."""
        response = await client.get(
            f"{USERS_URL}?role=admin",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["role"] == "admin"

    @pytest.mark.anyio
    async def test_list_users_filter_by_active_status(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Filter by active status works."""
        response = await client.get(
            f"{USERS_URL}?is_active=true",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["is_active"] is True


class TestCreateUser:
    """Tests for POST /api/v1/users endpoint."""

    @pytest.mark.anyio
    async def test_create_user_success(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Successfully create a new user."""
        new_user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "role": "user",
            "is_active": True,
        }
        response = await client.post(
            USERS_URL,
            json=new_user_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data

    @pytest.mark.anyio
    async def test_create_user_duplicate_username(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Cannot create user with duplicate username."""
        new_user_data = {
            "username": "admin",
            "email": "test@example.com",
            "password": "SecurePass123!",
        }
        response = await client.post(
            USERS_URL,
            json=new_user_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 409

    @pytest.mark.anyio
    async def test_create_user_duplicate_email(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Cannot create user with duplicate email."""
        new_user_data = {
            "username": "testuser",
            "email": ADMIN_EMAIL,
            "password": "SecurePass123!",
        }
        response = await client.post(
            USERS_URL,
            json=new_user_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 409

    @pytest.mark.anyio
    async def test_create_user_invalid_username(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Cannot create user with invalid username."""
        new_user_data = {
            "username": "test@invalid",
            "email": "test@example.com",
            "password": "SecurePass123!",
        }
        response = await client.post(
            USERS_URL,
            json=new_user_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_create_user_short_password(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Cannot create user with short password."""
        new_user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "short",
        }
        response = await client.post(
            USERS_URL,
            json=new_user_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_create_user_non_admin_denied(self, client: AsyncClient) -> None:
        """Non-admin users cannot create users."""
        # First create a regular user
        session_factory = get_session_factory()
        async with session_factory() as session:
            regular_user = await create_user(
                session=session,
                username="regularuser",
                email="regular@example.com",
                password="SecurePass123!",
                role=UserRole.USER,
            )

        # Login as regular user
        login_response = await client.post(
            f"{settings.api_v1_prefix}/auth/login",
            json={"email": "regular@example.com", "password": "SecurePass123!"},
        )
        regular_token = login_response.json()["access_token"]

        # Try to create a user
        new_user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "SecurePass123!",
        }
        response = await client.post(
            USERS_URL,
            json=new_user_data,
            headers={"Authorization": f"Bearer {regular_token}"},
        )
        assert response.status_code == 403


class TestGetUser:
    """Tests for GET /api/v1/users/{id} endpoint."""

    @pytest.mark.anyio
    async def test_get_user_admin_access(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Admin can get any user."""
        response = await client.get(
            f"{USERS_URL}/1",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "email" in data

    @pytest.mark.anyio
    async def test_get_user_not_found(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Getting nonexistent user returns 404."""
        response = await client.get(
            f"{USERS_URL}/99999",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_get_own_user_regular_user(self, client: AsyncClient) -> None:
        """Regular user can get own info."""
        # Create a regular user
        session_factory = get_session_factory()
        async with session_factory() as session:
            regular_user = await create_user(
                session=session,
                username="regularuser2",
                email="regular2@example.com",
                password="SecurePass123!",
                role=UserRole.USER,
            )
            user_id = regular_user.id

        # Login as regular user
        login_response = await client.post(
            f"{settings.api_v1_prefix}/auth/login",
            json={"email": "regular2@example.com", "password": "SecurePass123!"},
        )
        regular_token = login_response.json()["access_token"]

        # Get own user
        response = await client.get(
            f"{USERS_URL}/{user_id}",
            headers={"Authorization": f"Bearer {regular_token}"},
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_get_other_user_regular_user_denied(
        self, client: AsyncClient
    ) -> None:
        """Regular user cannot get other users."""
        # Create two regular users
        session_factory = get_session_factory()
        async with session_factory() as session:
            user1 = await create_user(
                session=session,
                username="user1",
                email="user1@example.com",
                password="SecurePass123!",
                role=UserRole.USER,
            )
            user2 = await create_user(
                session=session,
                username="user2",
                email="user2@example.com",
                password="SecurePass123!",
                role=UserRole.USER,
            )

        # Login as user1
        login_response = await client.post(
            f"{settings.api_v1_prefix}/auth/login",
            json={"email": "user1@example.com", "password": "SecurePass123!"},
        )
        token = login_response.json()["access_token"]

        # Try to get user2
        response = await client.get(
            f"{USERS_URL}/{user2.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestUpdateUser:
    """Tests for PATCH /api/v1/users/{id} endpoint."""

    @pytest.mark.anyio
    async def test_update_user_email_success(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Update user email successfully."""
        update_data = {"email": "newemail@example.com"}
        response = await client.patch(
            f"{USERS_URL}/1",
            json=update_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_update_user_duplicate_email(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Cannot update to duplicate email."""
        # Create another user first
        session_factory = get_session_factory()
        async with session_factory() as session:
            await create_user(
                session=session,
                username="another",
                email="another@example.com",
                password="SecurePass123!",
            )

        update_data = {"email": "another@example.com"}
        response = await client.patch(
            f"{USERS_URL}/1",
            json=update_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 409

    @pytest.mark.anyio
    async def test_update_user_role_admin_only(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Only admin can update role."""
        update_data = {"role": "admin"}
        response = await client.patch(
            f"{USERS_URL}/1",
            json=update_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_update_user_non_admin_cannot_change_role(
        self, client: AsyncClient
    ) -> None:
        """Non-admin cannot change role."""
        # Create a regular user
        session_factory = get_session_factory()
        async with session_factory() as session:
            regular_user = await create_user(
                session=session,
                username="regularuser3",
                email="regular3@example.com",
                password="SecurePass123!",
                role=UserRole.USER,
            )
            user_id = regular_user.id

        # Login as regular user
        login_response = await client.post(
            f"{settings.api_v1_prefix}/auth/login",
            json={"email": "regular3@example.com", "password": "SecurePass123!"},
        )
        regular_token = login_response.json()["access_token"]

        # Try to change own role
        update_data = {"role": "admin"}
        response = await client.patch(
            f"{USERS_URL}/{user_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {regular_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_update_nonexistent_user(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Updating nonexistent user returns 404."""
        update_data = {"email": "test@example.com"}
        response = await client.patch(
            f"{USERS_URL}/99999",
            json=update_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 404


class TestDeleteUser:
    """Tests for DELETE /api/v1/users/{id} endpoint."""

    @pytest.mark.anyio
    async def test_delete_user_success(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Delete a user successfully."""
        # Create a user to delete
        session_factory = get_session_factory()
        async with session_factory() as session:
            user_to_delete = await create_user(
                session=session,
                username="todelete",
                email="todelete@example.com",
                password="SecurePass123!",
                role=UserRole.USER,
            )
            user_id = user_to_delete.id

        # Delete the user
        response = await client.delete(
            f"{USERS_URL}/{user_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 204

        # Verify user is deleted
        session_factory = get_session_factory()
        async with session_factory() as session:
            deleted_user = await get_user_by_id(session=session, user_id=user_id)
            assert deleted_user is None

    @pytest.mark.anyio
    async def test_delete_user_cannot_delete_self(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Cannot delete own account."""
        response = await client.delete(
            f"{USERS_URL}/1",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_delete_user_nonexistent(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Deleting nonexistent user returns 404."""
        response = await client.delete(
            f"{USERS_URL}/99999",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_delete_last_active_admin_denied(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Cannot delete the last active admin."""
        # Get the admin user (created in fixtures)
        session_factory = get_session_factory()
        async with session_factory() as session:
            admin = await get_user_by_username(session=session, username="admin")
            assert admin is not None
            admin_id = admin.id

        # Try to delete the last active admin
        response = await client.delete(
            f"{USERS_URL}/{admin_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 400

    @pytest.mark.anyio
    async def test_delete_user_non_admin_denied(self, client: AsyncClient) -> None:
        """Non-admin cannot delete users."""
        # Create a regular user
        session_factory = get_session_factory()
        async with session_factory() as session:
            regular_user = await create_user(
                session=session,
                username="regularuser4",
                email="regular4@example.com",
                password="SecurePass123!",
                role=UserRole.USER,
            )

        # Login as regular user
        login_response = await client.post(
            f"{settings.api_v1_prefix}/auth/login",
            json={"email": "regular4@example.com", "password": "SecurePass123!"},
        )
        regular_token = login_response.json()["access_token"]

        # Try to delete a user
        response = await client.delete(
            f"{USERS_URL}/2",
            headers={"Authorization": f"Bearer {regular_token}"},
        )
        assert response.status_code == 403


class TestResetPassword:
    """Tests for POST /api/v1/users/{id}/reset-password endpoint."""

    @pytest.mark.anyio
    async def test_reset_password_admin(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Admin can reset any user password."""
        # Create a user
        session_factory = get_session_factory()
        async with session_factory() as session:
            user = await create_user(
                session=session,
                username="tochange",
                email="tochange@example.com",
                password="SecurePass123!",
            )
            user_id = user.id

        # Reset password
        reset_data = {"new_password": "NewSecurePass456!"}
        response = await client.post(
            f"{USERS_URL}/{user_id}/reset-password",
            json=reset_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_reset_own_password_regular_user(self, client: AsyncClient) -> None:
        """Regular user can reset own password."""
        # Create a regular user
        session_factory = get_session_factory()
        async with session_factory() as session:
            regular_user = await create_user(
                session=session,
                username="regularuser5",
                email="regular5@example.com",
                password="SecurePass123!",
                role=UserRole.USER,
            )
            user_id = regular_user.id

        # Login as regular user
        login_response = await client.post(
            f"{settings.api_v1_prefix}/auth/login",
            json={"email": "regular5@example.com", "password": "SecurePass123!"},
        )
        regular_token = login_response.json()["access_token"]

        # Reset own password
        reset_data = {"new_password": "NewSecurePass456!"}
        response = await client.post(
            f"{USERS_URL}/{user_id}/reset-password",
            json=reset_data,
            headers={"Authorization": f"Bearer {regular_token}"},
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_reset_other_password_regular_user_denied(
        self, client: AsyncClient
    ) -> None:
        """Regular user cannot reset other user's password."""
        # Create two regular users
        session_factory = get_session_factory()
        async with session_factory() as session:
            user1 = await create_user(
                session=session,
                username="user3",
                email="user3@example.com",
                password="SecurePass123!",
                role=UserRole.USER,
            )
            user2 = await create_user(
                session=session,
                username="user4",
                email="user4@example.com",
                password="SecurePass123!",
                role=UserRole.USER,
            )

        # Login as user1
        login_response = await client.post(
            f"{settings.api_v1_prefix}/auth/login",
            json={"email": "user3@example.com", "password": "SecurePass123!"},
        )
        token = login_response.json()["access_token"]

        # Try to reset user2's password
        reset_data = {"new_password": "NewSecurePass456!"}
        response = await client.post(
            f"{USERS_URL}/{user2.id}/reset-password",
            json=reset_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestToggleActive:
    """Tests for POST /api/v1/users/{id}/toggle-active endpoint."""

    @pytest.mark.anyio
    async def test_toggle_user_active(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Toggle user active status."""
        # Create a user
        session_factory = get_session_factory()
        async with session_factory() as session:
            user = await create_user(
                session=session,
                username="totoggle",
                email="totoggle@example.com",
                password="SecurePass123!",
                is_active=True,
            )
            user_id = user.id

        # Toggle status
        response = await client.post(
            f"{USERS_URL}/{user_id}/toggle-active",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    @pytest.mark.anyio
    async def test_toggle_cannot_disable_self(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Cannot disable own account."""
        response = await client.post(
            f"{USERS_URL}/1/toggle-active",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_toggle_last_active_admin_denied(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Cannot disable the last active admin."""
        # Get the admin user
        session_factory = get_session_factory()
        async with session_factory() as session:
            admin = await get_user_by_username(session=session, username="admin")
            assert admin is not None
            admin_id = admin.id

        # Try to toggle the last active admin
        response = await client.post(
            f"{USERS_URL}/{admin_id}/toggle-active",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 400

    @pytest.mark.anyio
    async def test_toggle_non_admin_denied(self, client: AsyncClient) -> None:
        """Non-admin cannot toggle user status."""
        # Create a regular user
        session_factory = get_session_factory()
        async with session_factory() as session:
            regular_user = await create_user(
                session=session,
                username="regularuser6",
                email="regular6@example.com",
                password="SecurePass123!",
                role=UserRole.USER,
            )

        # Login as regular user
        login_response = await client.post(
            f"{settings.api_v1_prefix}/auth/login",
            json={"email": "regular6@example.com", "password": "SecurePass123!"},
        )
        regular_token = login_response.json()["access_token"]

        # Try to toggle a user
        response = await client.post(
            f"{USERS_URL}/2/toggle-active",
            headers={"Authorization": f"Bearer {regular_token}"},
        )
        assert response.status_code == 403
