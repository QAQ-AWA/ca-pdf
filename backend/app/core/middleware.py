"""Custom ASGI middleware utilities."""

from __future__ import annotations

import logging
import time
from typing import Any, Awaitable, Callable
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

__all__ = ["RequestLoggingMiddleware"]


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Emit structured logs for each incoming request."""

    def __init__(self, app: ASGIApp, *, logger: logging.Logger | None = None) -> None:
        super().__init__(app)
        self._logger = logger or logging.getLogger("app.request")

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("x-request-id") or uuid4().hex
        request.state.request_id = request_id

        start_time = time.perf_counter()
        self._logger.info(
            {
                "event": "request.start",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": request.url.query or None,
                "scheme": request.url.scheme,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )

        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover - defensive logging branch
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self._logger.exception(
                {
                    "event": "request.exception",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "elapsed_ms": elapsed_ms,
                    "error": repr(exc),
                }
            )
            raise

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers.setdefault("X-Request-ID", request_id)

        log_payload: dict[str, Any] = {
            "event": "request.complete",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "content_length": response.headers.get("content-length"),
        }
        self._logger.info(log_payload)
        return response
