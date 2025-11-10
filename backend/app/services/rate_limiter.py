"""Simple in-memory rate limiter for FastAPI dependencies."""

from __future__ import annotations

import asyncio
from collections import deque
from time import monotonic

from fastapi import HTTPException, Request, status


class RateLimiter:
    """An asynchronous dependency implementing a token bucket style rate limit."""

    def __init__(self, *, requests: int, window_seconds: int) -> None:
        self._requests = requests
        self._window_seconds = float(window_seconds)
        self._attempts: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, request: Request) -> None:
        """Check rate limit for the given request."""
        identifier = self._build_identifier(request)
        now = monotonic()

        async with self._lock:
            attempts = self._attempts.setdefault(identifier, deque())
            while attempts and now - attempts[0] > self._window_seconds:
                attempts.popleft()

            if len(attempts) >= self._requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many authentication attempts. Please try again later.",
                )

            attempts.append(now)

    async def reset(self) -> None:
        """Clear tracked attempts. Primarily useful for automated tests."""

        async with self._lock:
            self._attempts.clear()

    @staticmethod
    def _build_identifier(request: Request) -> str:
        client_host = request.client.host if request.client else "unknown"
        return f"{client_host}:{request.url.path}"