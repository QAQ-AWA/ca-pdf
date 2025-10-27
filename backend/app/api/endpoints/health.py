"""Health and readiness endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db

router = APIRouter(tags=["health"])


def _base_payload() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@router.get("/health", tags=["health"])
async def health_root() -> dict[str, Any]:
    """Return basic liveness information."""

    payload = _base_payload()
    payload["checks"] = {"live": {"status": "ok"}}
    return payload


@router.get("/health/live", tags=["health"])
async def health_live() -> dict[str, str]:
    """Return minimal liveness probe information."""

    return _base_payload()


@router.get("/health/ready", tags=["health"])
async def health_ready(session: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return readiness information including database connectivity."""

    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - defensive readiness branch
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connectivity check failed",
        ) from exc

    payload = _base_payload()
    payload["checks"] = {
        "live": {"status": "ok"},
        "database": {"status": "ok"},
    }
    return payload
