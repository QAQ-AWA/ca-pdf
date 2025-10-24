"""Pydantic schemas for PDF signing operations."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class SignatureVisibility(str, Enum):
    """Visibility mode for PDF signatures."""

    VISIBLE = "visible"
    INVISIBLE = "invisible"


class SignatureCoordinates(BaseModel):
    """Coordinates for visible signature placement."""

    page: int = Field(ge=1, description="Page number (1-based)")
    x: float = Field(ge=0, description="X coordinate from bottom-left")
    y: float = Field(ge=0, description="Y coordinate from bottom-left")
    width: float = Field(gt=0, description="Width of signature box")
    height: float = Field(gt=0, description="Height of signature box")


class SignatureMetadata(BaseModel):
    """Optional metadata for signatures."""

    reason: str | None = Field(default=None, max_length=256, description="Reason for signing")
    location: str | None = Field(default=None, max_length=256, description="Location of signing")
    contact_info: str | None = Field(default=None, max_length=256, description="Contact information")


class PDFSignRequest(BaseModel):
    """Request payload for signing a single PDF document."""

    certificate_id: UUID = Field(description="Certificate to use for signing")
    seal_id: UUID | None = Field(default=None, description="Optional seal image to embed")
    visibility: SignatureVisibility = Field(default=SignatureVisibility.INVISIBLE)
    coordinates: SignatureCoordinates | None = Field(
        default=None,
        description="Required for visible signatures",
    )
    metadata: SignatureMetadata | None = Field(default=None)
    use_tsa: bool = Field(default=False, description="Include RFC3161 timestamp")
    embed_ltv: bool = Field(default=False, description="Embed validation material for LTV")


class PDFSignResponse(BaseModel):
    """Response returned after signing a PDF."""

    document_id: str = Field(description="Unique identifier for the signed document")
    signed_at: datetime = Field(description="Timestamp of signing operation")
    certificate_id: UUID = Field(description="Certificate used for signing")
    seal_id: UUID | None = Field(default=None)
    visibility: SignatureVisibility
    tsa_used: bool = Field(description="Whether TSA timestamp was included")
    ltv_embedded: bool = Field(description="Whether LTV material was embedded")
    file_size: int = Field(description="Size of signed PDF in bytes")


class PDFBatchSignRequest(BaseModel):
    """Request payload for batch signing multiple PDF documents."""

    certificate_id: UUID = Field(description="Certificate to use for signing all documents")
    seal_id: UUID | None = Field(default=None, description="Optional seal image to embed")
    visibility: SignatureVisibility = Field(default=SignatureVisibility.INVISIBLE)
    coordinates: SignatureCoordinates | None = Field(
        default=None,
        description="Applied to all documents if visible",
    )
    metadata: SignatureMetadata | None = Field(default=None)
    use_tsa: bool = Field(default=False, description="Include RFC3161 timestamp")
    embed_ltv: bool = Field(default=False, description="Embed validation material for LTV")


class PDFBatchSignResultItem(BaseModel):
    """Result for a single document in batch signing."""

    filename: str
    success: bool
    document_id: str | None = None
    signed_at: datetime | None = None
    file_size: int | None = None
    error: str | None = None


class PDFBatchSignResponse(BaseModel):
    """Response returned after batch signing PDFs."""

    total: int = Field(description="Total documents submitted")
    successful: int = Field(description="Number of successfully signed documents")
    failed: int = Field(description="Number of failed documents")
    results: list[PDFBatchSignResultItem]
    certificate_id: UUID
    seal_id: UUID | None = None
    visibility: SignatureVisibility
    tsa_used: bool
    ltv_embedded: bool
