"""API endpoints for retrieving audit logs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_roles
from app.crud import audit_log as audit_log_crud
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.audit import AuditLogEntry, AuditLogListResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    *,
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of entries to return"),
    offset: int = Query(default=0, ge=0, description="Number of entries to skip"),
    event_type: str | None = Query(default=None, description="Filter by event type"),
    resource: str | None = Query(default=None, description="Filter by resource name"),
    actor_id: int | None = Query(default=None, description="Filter by actor identifier"),
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_db),
) -> AuditLogListResponse:
    """Return paginated audit log entries for administrative review."""

    entries, total = await audit_log_crud.list_audit_logs(
        session=session,
        limit=limit,
        offset=offset,
        event_type=event_type,
        resource=resource,
        actor_id=actor_id,
    )

    return AuditLogListResponse(
        total=total,
        limit=limit,
        offset=offset,
        logs=[
            AuditLogEntry(
                id=entry.id,
                actor_id=entry.actor_id,
                event_type=entry.event_type,
                resource=entry.resource,
                ip_address=entry.ip_address,
                user_agent=entry.user_agent,
                meta=entry.meta,
                message=entry.message,
                created_at=entry.created_at,
            )
            for entry in entries
        ],
    )
