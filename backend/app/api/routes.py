import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.api.endpoints import audit, auth, ca, pdf_signing, seals, users
from app.core.config import settings
from app.db.session import get_engine

logger = logging.getLogger(__name__)

router = APIRouter()
api_router = APIRouter(prefix=settings.api_v1_prefix)

api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(audit.router)
api_router.include_router(ca.router)
api_router.include_router(pdf_signing.router)
api_router.include_router(seals.router)
api_router.include_router(users.router, prefix="/users")
router.include_router(api_router)


@router.get("/ping", tags=["health"])
async def ping_check() -> dict[str, str]:
    """Minimal ping endpoint for load balancer health checks."""
    return {"status": "pong", "service": settings.app_name}


@router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint for uptime monitoring."""
    try:
        return {"status": "ok", "service": settings.app_name}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/health/db", tags=["health"])
async def health_check_db() -> dict[str, str]:
    """Database connectivity health check endpoint."""
    try:
        from sqlalchemy import text

        engine = get_engine()
        # Test database connectivity with a simple query
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "service": settings.app_name,
            "database": "connected",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database connectivity failed")
    except Exception as e:
        logger.error(f"Unexpected database health check error: {e}")
        raise HTTPException(status_code=503, detail="Database health check failed")
