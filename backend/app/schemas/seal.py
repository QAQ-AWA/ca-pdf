"""Pydantic schemas for seal management operations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SealCreate(BaseModel):
    """Request payload for creating a new seal."""

    name: str = Field(..., min_length=1, max_length=120, description="Name of the seal")
    description: str | None = Field(
        default=None, max_length=1000, description="Optional description"
    )


class SealResponse(BaseModel):
    """Response payload for a seal."""

    id: UUID = Field(description="Seal identifier")
    name: str = Field(description="Name of the seal")
    description: str | None = Field(description="Optional description")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class SealListResponse(BaseModel):
    """Response payload for listing seals with pagination."""

    items: list[SealResponse] = Field(description="List of seals")
    total: int = Field(description="Total number of seals")
    skip: int = Field(description="Number of items skipped")
    limit: int = Field(description="Maximum items returned")
