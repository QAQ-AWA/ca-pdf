"""CRUD helpers for recording and retrieving audit trail entries."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def create_audit_log(
    *,
    session: AsyncSession,
    actor_id: int | None,
    event_type: str,
    resource: str,
    meta: dict[str, Any] | None = None,
    message: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    commit: bool = False,
) -> AuditLog:
    """Persist a new audit log entry."""

    entry = AuditLog(
        actor_id=actor_id,
        event_type=event_type,
        resource=resource,
        meta=meta,
        message=message,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(entry)
    await session.flush()
    if commit:
        await session.commit()
        await session.refresh(entry)
    return entry


async def list_audit_logs(
    *,
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    event_type: str | None = None,
    resource: str | None = None,
    actor_id: int | None = None,
) -> tuple[list[AuditLog], int]:
    """Return paginated audit log entries with optional filtering."""

    if limit <= 0:
        raise ValueError("limit must be a positive integer")
    if offset < 0:
        raise ValueError("offset cannot be negative")

    conditions: list[Any] = []
    if event_type:
        conditions.append(AuditLog.event_type == event_type)
    if resource:
        conditions.append(AuditLog.resource == resource)
    if actor_id is not None:
        conditions.append(AuditLog.actor_id == actor_id)

    base_query: Select[Any] = select(AuditLog)
    if conditions:
        base_query = base_query.where(*conditions)

    count_stmt = select(func.count(AuditLog.id))
    if conditions:
        count_stmt = count_stmt.where(*conditions)

    base_query = base_query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    base_query = base_query.offset(offset).limit(limit)

    result = await session.execute(base_query)
    entries = list(result.scalars().all())

    total_result = await session.execute(count_stmt)
    total = int(total_result.scalar_one())

    return entries, total
