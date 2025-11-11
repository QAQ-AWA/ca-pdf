import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import settings
from app.core.errors import APIException
from app.db.init_db import bootstrap_admin, init_db
from app.schemas.error import ErrorResponse

logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    application = FastAPI(title=settings.app_name)

    cors_origins = settings.backend_cors_origins or ["*"]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(router)

    @application.exception_handler(APIException)
    async def api_exception_handler(
        request: Request, exc: APIException
    ) -> JSONResponse:
        """Handle standardized API exceptions."""
        error_response = ErrorResponse(
            code=exc.code,
            message=exc.message,
            detail=exc.detail,
            timestamp=datetime.now(tz=timezone.utc),
            path=str(request.url.path),
            request_id=request.headers.get("X-Request-ID", str(uuid4())),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=json.loads(error_response.model_dump_json()),
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        error_response = ErrorResponse(
            code="INVALID_INPUT",
            message="Validation error",
            detail=str(exc.errors()),
            timestamp=datetime.now(tz=timezone.utc),
            path=str(request.url.path),
            request_id=request.headers.get("X-Request-ID", str(uuid4())),
        )
        return JSONResponse(
            status_code=422,
            content=json.loads(error_response.model_dump_json()),
        )

    @application.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        error_response = ErrorResponse(
            code="INTERNAL_ERROR",
            message="An internal server error occurred",
            detail="An unexpected error occurred",
            timestamp=datetime.now(tz=timezone.utc),
            path=str(request.url.path),
            request_id=request.headers.get("X-Request-ID", str(uuid4())),
        )
        return JSONResponse(
            status_code=500,
            content=json.loads(error_response.model_dump_json()),
        )

    @application.on_event("startup")
    async def _on_startup() -> None:
        await init_db()
        await bootstrap_admin()

    return application


app = create_application()
