from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Basic health check endpoint for uptime monitoring."""

    return {"status": "ok", "service": settings.app_name}
