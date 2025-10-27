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


class SignatureVerificationResult(BaseModel):
    """Verification outcome for a single embedded signature."""

    field_name: str = Field(description="Name of the signature field")
    valid: bool = Field(description="Whether the signature is cryptographically valid")
    trusted: bool = Field(description="Whether the signature chain is trusted")
    docmdp_ok: bool | None = Field(default=None, description="Whether document modifications are permitted")
    modification_level: str | None = Field(
        default=None,
        description="Permitted modification level detected for the document",
    )
    signing_time: datetime | None = Field(
        default=None,
        description="Signing time reported by the signer, if available",
    )
    signer_common_name: str | None = Field(default=None, description="Common name from the signer certificate")
    signer_serial_number: str | None = Field(default=None, description="Serial number of the signer certificate")
    summary: str = Field(description="Human-readable summary of the verification result")
    timestamp_trusted: bool | None = Field(
        default=None,
        description="Whether the associated timestamp token is trusted",
    )
    timestamp_time: datetime | None = Field(
        default=None,
        description="Timestamp recorded by the timestamp token, if available",
    )
    timestamp_summary: str | None = Field(
        default=None,
        description="Summary describing the timestamp validation",
    )
    error: str | None = Field(default=None, description="Error message recorded during validation, if any")


class PDFVerificationResponse(BaseModel):
    """Aggregated verification summary for a PDF document."""

    total_signatures: int = Field(description="Total number of signatures detected")
    valid_signatures: int = Field(description="Number of signatures that are valid")
    trusted_signatures: int = Field(description="Number of signatures that chain to a trusted root")
    all_signatures_valid: bool = Field(description="Whether all signatures are valid")
    all_signatures_trusted: bool = Field(description="Whether all signatures are trusted")
    signatures: list[SignatureVerificationResult] = Field(
        description="Per-signature verification details"
    )
