"""Pydantic schemas for certificate authority operations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.certificate import CertificateStatus
from app.services.certificate_authority import LeafKeyAlgorithm, RootKeyAlgorithm


class RootCACreateRequest(BaseModel):
    """Request payload for generating the root certificate authority."""

    common_name: str = Field(min_length=3, max_length=255)
    organization: str | None = Field(default=None, max_length=255)
    algorithm: RootKeyAlgorithm = Field(default=RootKeyAlgorithm.RSA_4096)
    validity_days: int = Field(default=3650, ge=1, le=3650)


class RootCAResponse(BaseModel):
    """Response payload describing the generated root CA."""

    model_config = ConfigDict(use_enum_values=True)

    artifact_id: UUID
    algorithm: RootKeyAlgorithm
    serial_number: str
    subject: str
    fingerprint_sha256: str
    issued_at: datetime
    expires_at: datetime


class RootCertificateExportResponse(BaseModel):
    """Response containing the PEM encoded root certificate."""

    certificate_pem: str


class CertificateIssueRequest(BaseModel):
    """Request payload for issuing a new certificate."""

    common_name: str = Field(min_length=3, max_length=255)
    organization: str | None = Field(default=None, max_length=255)
    algorithm: LeafKeyAlgorithm = Field(default=LeafKeyAlgorithm.RSA_2048)
    validity_days: int = Field(default=365, ge=1, le=1825)
    p12_passphrase: str | None = Field(default=None, max_length=256)


class CertificateBaseResponse(BaseModel):
    """Shared response fields for certificate operations."""

    model_config = ConfigDict(use_enum_values=True)

    certificate_id: UUID
    serial_number: str
    status: CertificateStatus
    issued_at: datetime
    expires_at: datetime
    certificate_pem: str


class CertificateIssueResponse(CertificateBaseResponse):
    """Response returned after issuing a new certificate."""

    p12_bundle: str | None = None


class CertificateImportRequest(BaseModel):
    """Request payload for importing an external PKCS#12 bundle."""

    p12_bundle: str = Field(min_length=1)
    passphrase: str | None = Field(default=None, max_length=256)


class CertificateImportResponse(CertificateBaseResponse):
    """Response returned after importing a certificate."""

    p12_bundle: str | None = None


class CertificateSummary(BaseModel):
    """Summary of a certificate for list views."""

    model_config = ConfigDict(use_enum_values=True)

    certificate_id: UUID
    serial_number: str
    status: CertificateStatus
    issued_at: datetime
    expires_at: datetime
    subject_common_name: str


class CertificateListResponse(BaseModel):
    """Response containing the caller's certificates."""

    certificates: list[CertificateSummary]


class CertificateRevokeResponse(BaseModel):
    """Response returned after revoking a certificate."""

    certificate_id: UUID
    status: CertificateStatus
    revoked_at: datetime


class CRLGenerateResponse(BaseModel):
    """Response describing a newly generated CRL."""

    artifact_id: UUID
    name: str
    created_at: datetime
    crl_pem: str
    revoked_serials: list[str]


class CRLMetadata(BaseModel):
    """Metadata for an existing CRL artifact."""

    artifact_id: UUID
    name: str
    created_at: datetime


class CRLListResponse(BaseModel):
    """Response containing CRL metadata entries."""

    crls: list[CRLMetadata]
