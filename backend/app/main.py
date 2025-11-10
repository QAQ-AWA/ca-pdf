from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.db.init_db import bootstrap_admin, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    # Startup
    await init_db()
    await bootstrap_admin()
    yield
    # Shutdown (if needed)


def create_application() -> FastAPI:
    """Create and configure FastAPI application instance."""

    application = FastAPI(title=settings.app_name, lifespan=lifespan)

    cors_origins = settings.backend_cors_origins or ["*"]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(router)

    return application


app = create_application()