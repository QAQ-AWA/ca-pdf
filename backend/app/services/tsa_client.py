"""RFC3161 timestamp authority client for PDF signing."""

from __future__ import annotations

from typing import Protocol

import requests
from pyhanko.sign.timestamps import HTTPTimeStamper

from app.core.config import settings


class TSAError(Exception):
    """Base error for timestamp authority operations."""


class TSAConnectionError(TSAError):
    """Raised when TSA cannot be reached."""


class TSAResponseError(TSAError):
    """Raised when TSA returns an invalid response."""


class TimeStamperProtocol(Protocol):
    """Protocol for time stamping operations."""

    async def async_request_tsa_response(
        self,
        req: bytes,
        timeout: int | None = None,
    ) -> bytes:
        """Request a timestamp token from the TSA."""
        ...


class TSAClient:
    """Client for RFC3161 timestamp authority operations."""

    def __init__(
        self,
        tsa_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self.tsa_url = tsa_url or settings.tsa_url
        self.username = username or settings.tsa_username
        self.password = password or (
            settings.tsa_password.get_secret_value() if settings.tsa_password else None
        )

    def is_configured(self) -> bool:
        """Check if TSA is configured and available."""
        return bool(self.tsa_url)

    def get_timestamper(self) -> HTTPTimeStamper | None:
        """Create and return a pyHanko HTTP timestamper instance."""
        if not self.is_configured():
            return None

        if not self.tsa_url:
            return None

        auth: tuple[str, str] | None = None
        if self.username and self.password:
            auth = (self.username, self.password)

        return HTTPTimeStamper(
            url=self.tsa_url,
            auth=auth,
            timeout=30,
        )

    def validate_tsa_connection(self) -> bool:
        """Validate that the TSA endpoint is reachable."""
        if not self.is_configured() or not self.tsa_url:
            return False

        try:
            auth: tuple[str, str] | None = None
            if self.username and self.password:
                auth = (self.username, self.password)

            response = requests.head(
                self.tsa_url,
                auth=auth,
                timeout=10,
            )
            return bool(response.status_code < 500)
        except requests.RequestException:
            return False
