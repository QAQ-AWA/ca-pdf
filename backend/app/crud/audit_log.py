"""CRUD helpers for recording audit trail entries."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def create_audit_log(
    *,
    session: AsyncSession,
    actor_id: int | None,
    event_type: str,
    resource: str,
    metadata: dict[str, Any] | None = None,
    message: str | None = None,
    commit: bool = False,
) -> AuditLog:
    """Persist a new audit log entry."""

    entry = AuditLog(
        actor_id=actor_id,
        event_type=event_type,
        resource=resource,
        metadata=metadata,
        message=message,
    )
    session.add(entry)
    await session.flush()
    if commit:
        await session.commit()
        await session.refresh(entry)
    return entry
