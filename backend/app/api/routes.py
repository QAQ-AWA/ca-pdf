from fastapi import APIRouter

from app.api.endpoints import auth
from app.core.config import settings

router = APIRouter()
api_router = APIRouter(prefix=settings.api_v1_prefix)

api_router.include_router(auth.router, prefix="/auth")
router.include_router(api_router)


@router.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Basic health check endpoint for uptime monitoring."""

    return {"status": "ok", "service": settings.app_name}
