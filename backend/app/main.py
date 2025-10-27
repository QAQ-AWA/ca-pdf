"""Application entrypoint and FastAPI factory."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exception_handlers import (
    http_exception_handler as fastapi_http_exception_handler,
    request_validation_exception_handler as fastapi_request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.proxy_headers import ProxyHeadersMiddleware
from starlette.middleware.security import SecurityMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette_exporter import PrometheusMiddleware, handle_metrics

from app.api.routes import router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import RequestLoggingMiddleware
from app.db.init_db import bootstrap_admin, init_db

error_logger = logging.getLogger("app.errors")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    configure_logging(settings.log_level)

    application = FastAPI(title=settings.app_name)

    if settings.enable_proxy_headers:
        trusted_proxies = settings.proxy_trusted_hosts or ["*"]
        application.add_middleware(
            ProxyHeadersMiddleware,
            trusted_hosts=trusted_proxies,
        )

    if settings.trusted_hosts:
        application.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

    if settings.security_headers_enabled:
        security_kwargs: dict[str, Any] = {
            "content_type_nosniff": True,
            "frame_deny": True,
            "sts_seconds": max(settings.security_hsts_seconds, 0),
            "sts_include_subdomains": settings.security_hsts_include_subdomains,
            "sts_preload": settings.security_hsts_preload,
        }
        if settings.security_referrer_policy:
            security_kwargs["referrer_policy"] = settings.security_referrer_policy
        if settings.security_permissions_policy:
            security_kwargs["permissions_policy"] = settings.security_permissions_policy
        if settings.security_cross_origin_opener_policy:
            security_kwargs["cross_origin_opener_policy"] = (
                settings.security_cross_origin_opener_policy
            )
        if settings.security_cross_origin_embedder_policy:
            security_kwargs["cross_origin_embedder_policy"] = (
                settings.security_cross_origin_embedder_policy
            )
        if settings.security_cross_origin_resource_policy:
            security_kwargs["cross_origin_resource_policy"] = (
                settings.security_cross_origin_resource_policy
            )
        application.add_middleware(SecurityMiddleware, **security_kwargs)

    if settings.force_https_redirect:
        application.add_middleware(HTTPSRedirectMiddleware)

    metrics_endpoint = settings.metrics_endpoint
    application.add_middleware(
        PrometheusMiddleware,
        app_name=settings.app_name,
        prefix="http",
        group_paths=True,
        skip_paths={metrics_endpoint},
    )

    application.add_middleware(RequestLoggingMiddleware)

    if settings.enable_cors:
        cors_origins = settings.backend_cors_origins or ["*"]
        allow_credentials = settings.cors_allow_credentials
        if "*" in cors_origins and allow_credentials:
            allow_credentials = False

        allow_methods = settings.cors_allow_methods or ["*"]
        allow_headers = settings.cors_allow_headers or ["*"]
        expose_headers = list(dict.fromkeys(settings.cors_expose_headers or []))
        lower_expose = {header.lower() for header in expose_headers}
        if "x-request-id" not in lower_expose:
            expose_headers.append("X-Request-ID")

        application.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=allow_credentials,
            allow_methods=allow_methods,
            allow_headers=allow_headers,
            expose_headers=expose_headers,
            max_age=settings.cors_max_age,
        )

    application.include_router(router)
    application.add_route(metrics_endpoint, handle_metrics)

    @application.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        error_logger.warning(
            {
                "event": "http_error",
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": request.url.path,
                "request_id": getattr(request.state, "request_id", None),
            }
        )
        return await fastapi_http_exception_handler(request, exc)

    @application.exception_handler(RequestValidationError)
    async def _validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        error_logger.warning(
            {
                "event": "request_validation_error",
                "errors": exc.errors(),
                "path": request.url.path,
                "request_id": getattr(request.state, "request_id", None),
            }
        )
        return await fastapi_request_validation_exception_handler(request, exc)

    @application.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        error_logger.exception(
            {
                "event": "unhandled_exception",
                "error": repr(exc),
                "path": request.url.path,
                "request_id": getattr(request.state, "request_id", None),
            }
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal Server Error"},
        )

    @application.on_event("startup")
    async def _on_startup() -> None:
        await init_db()
        await bootstrap_admin()

    return application


app = create_application()
