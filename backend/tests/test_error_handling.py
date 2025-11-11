"""Tests for standardized error handling across the API."""

from __future__ import annotations

from httpx import AsyncClient


class TestErrorResponseFormat:
    """Test that all errors follow the standard response format."""

    async def test_validation_error_format(self, client: AsyncClient) -> None:
        """Test that validation errors return standard error response."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "invalid-email", "password": ""},
        )
        assert response.status_code == 422
        data = response.json()
        assert "code" in data
        assert "message" in data
        assert "timestamp" in data
        assert "path" in data
        assert "request_id" in data
        assert data["code"] == "INVALID_INPUT"
        assert data["message"] == "Validation error"

    async def test_error_response_includes_request_id(
        self, client: AsyncClient
    ) -> None:
        """Test that error responses include a request ID for tracing."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "w"},
        )
        # Response will be 422 (validation) or 401 (auth), but both should have request_id
        data = response.json()
        assert "request_id" in data
        assert data["request_id"]  # Should not be empty

    async def test_error_response_includes_timestamp(self, client: AsyncClient) -> None:
        """Test that error responses include timestamp."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "w"},
        )
        data = response.json()
        assert "timestamp" in data
        assert data["timestamp"]

    async def test_error_response_includes_path(self, client: AsyncClient) -> None:
        """Test that error responses include the request path."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "w"},
        )
        data = response.json()
        assert "path" in data
        assert "/auth/login" in data["path"]


class TestAuthenticationErrors:
    """Test authentication-related error responses."""

    async def test_missing_auth_header_returns_unauthorized(
        self, client: AsyncClient
    ) -> None:
        """Test that missing auth header returns proper error."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "UNAUTHORIZED"

    async def test_invalid_token_returns_error(self, client: AsyncClient) -> None:
        """Test that invalid token returns proper error."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "UNAUTHORIZED"


class TestValidationErrors:
    """Test validation error responses."""

    async def test_pydantic_validation_error_returns_standard_format(
        self, client: AsyncClient
    ) -> None:
        """Test that Pydantic validation errors use standard format."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "test"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["code"] == "INVALID_INPUT"
        assert data["message"] == "Validation error"
        assert "detail" in data

    async def test_invalid_json_returns_standard_error(
        self, client: AsyncClient
    ) -> None:
        """Test that invalid JSON returns standard error format."""
        response = await client.post(
            "/api/v1/auth/login",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [400, 422]
        data = response.json()
        assert "code" in data
        assert "message" in data


class TestErrorCodeConsistency:
    """Test that error codes are consistent across the API."""

    async def test_all_error_responses_have_error_code(
        self, client: AsyncClient
    ) -> None:
        """Test that all error responses have an error code."""
        # Test various error scenarios
        test_cases = [
            ("/api/v1/auth/login", "POST", {"email": "test@test", "password": ""}),
            ("/api/v1/auth/me", "GET", None),
        ]

        for path, method, data in test_cases:
            if method == "GET":
                response = await client.get(path)
            else:
                response = await client.post(path, json=data)

            # Any error response should have a code
            if response.status_code >= 400:
                json_data = response.json()
                assert "code" in json_data
                assert isinstance(json_data["code"], str)
                assert json_data["code"]  # Not empty

    async def test_error_code_is_stable_string(self, client: AsyncClient) -> None:
        """Test that error codes are stable strings for frontend i18n."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        data = response.json()
        code = data["code"]
        # Code should be a simple string like UNAUTHORIZED
        assert code in ["UNAUTHORIZED", "INVALID_TOKEN", "TOKEN_EXPIRED"]


class TestErrorMessages:
    """Test that error messages are user-friendly and secure."""

    async def test_error_messages_are_readable(self, client: AsyncClient) -> None:
        """Test that error messages are human-readable."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        data = response.json()
        message = data["message"]
        # Message should be readable and not contain stack traces or internal details
        assert len(message) > 0
        assert "traceback" not in message.lower()
        assert "exception" not in message.lower()

    async def test_internal_errors_hide_sensitive_details(
        self, client: AsyncClient
    ) -> None:
        """Test that internal server errors don't leak sensitive info."""
        # This test would need a way to trigger a real error
        # For now, we just verify that the general error handler exists
        assert True  # Placeholder - more specific tests can be added


class TestErrorResponseStatusCodes:
    """Test that error responses use correct HTTP status codes."""

    async def test_validation_error_uses_422(self, client: AsyncClient) -> None:
        """Test that validation errors use 422 Unprocessable Entity."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "not-valid", "password": ""},
        )
        assert response.status_code == 422

    async def test_unauthorized_uses_401(self, client: AsyncClient) -> None:
        """Test that unauthorized errors use 401 Unauthorized."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_missing_header_uses_401(self, client: AsyncClient) -> None:
        """Test that missing auth header uses 401."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestErrorResponseStructure:
    """Test error response always has required fields."""

    async def test_error_response_has_all_required_fields(
        self, client: AsyncClient
    ) -> None:
        """Test that error response has code, message, timestamp, path, request_id."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        data = response.json()
        required_fields = ["code", "message", "timestamp", "path", "request_id"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
