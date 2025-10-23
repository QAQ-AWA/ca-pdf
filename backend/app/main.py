from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.db.init_db import bootstrap_admin, init_db


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

    @application.on_event("startup")
    async def _on_startup() -> None:
        await init_db()
        await bootstrap_admin()

    return application


app = create_application()
