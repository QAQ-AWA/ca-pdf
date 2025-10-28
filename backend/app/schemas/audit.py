"""Pydantic schemas for audit log responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    """Representation of an audit log entry returned via the API."""

    id: UUID = Field(description="Unique identifier for the audit log entry")
    actor_id: int | None = Field(default=None, description="User responsible for the event")
    event_type: str = Field(description="Event type identifier")
    resource: str = Field(description="Name of the resource associated with the event")
    ip_address: str | None = Field(default=None, description="IP address recorded for the event")
    user_agent: str | None = Field(default=None, description="User agent associated with the event")
    meta: dict[str, Any] | None = Field(default=None, description="Structured metadata payload")
    message: str | None = Field(default=None, description="Optional human readable message")
    created_at: datetime = Field(description="Timestamp when the entry was created")


class AuditLogListResponse(BaseModel):
    """Paginated response containing audit log entries."""

    total: int = Field(description="Total number of log entries matching the filters")
    limit: int = Field(description="Maximum number of entries returned")
    offset: int = Field(description="Offset applied to the query")
    logs: list[AuditLogEntry] = Field(description="Audit log entries for the current page")
