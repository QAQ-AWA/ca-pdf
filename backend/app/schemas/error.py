"""Error response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response format for all API errors."""

    code: str = Field(..., description="Error code identifying the error type")
    message: str = Field(..., description="User-friendly error message")
    detail: Optional[str] = Field(
        default=None, description="Technical details (optional)"
    )
    timestamp: datetime = Field(..., description="When the error occurred")
    path: str = Field(..., description="The request path")
    request_id: str = Field(..., description="Unique request identifier for tracing")

    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "INVALID_INPUT",
                "message": "Validation failed",
                "detail": "Field 'email' is required",
                "timestamp": "2024-01-01T12:00:00Z",
                "path": "/api/v1/auth/login",
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
    }
