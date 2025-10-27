"""API endpoints for managing the private certificate authority."""

from __future__ import annotations

import base64
import binascii
from datetime import datetime, timezone
from uuid import UUID

from cryptography.hazmat.primitives import hashes
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user, require_roles
from app.crud import certificate as certificate_crud
from app.db.session import get_db
from app.models.certificate import Certificate, CertificateStatus
from app.models.user import User, UserRole
from app.schemas.ca import (
    CertificateImportRequest,
    CertificateImportResponse,
    CertificateIssueRequest,
    CertificateIssueResponse,
    CertificateListResponse,
    CertificateRevokeResponse,
    CertificateSummary,
    CRLGenerateResponse,
    CRLListResponse,
    CRLMetadata,
    RootCACreateRequest,
    RootCAResponse,
    RootCertificateExportResponse,
)
from app.services.certificate_authority import (
    CertificateAuthorityError,
    CertificateAuthorityService,
    CertificateImportError,
    CertificateIssuanceError,
    CertificateRevocationError,
    RootCAAlreadyExistsError,
    RootCANotFoundError,
)

router = APIRouter(prefix="/ca", tags=["certificate-authority"])
ca_service = CertificateAuthorityService()


@router.post(
    "/root", response_model=RootCAResponse, status_code=status.HTTP_201_CREATED
)
async def generate_root_ca(
    payload: RootCACreateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_db),
) -> RootCAResponse:
    """Generate the primary root certificate authority."""

    try:
        result = await ca_service.generate_root_ca(
            session=session,
            algorithm=payload.algorithm,
            common_name=payload.common_name,
            organization=payload.organization,
            actor_id=current_user.id,
            validity_days=payload.validity_days,
        )
    except RootCAAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except CertificateAuthorityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    fingerprint = result.certificate.fingerprint(hashes.SHA256()).hex().upper()
    serial_hex = f"{result.certificate.serial_number:x}".upper()
    issued_at = _ensure_utc(result.certificate.not_valid_before)
    expires_at = _ensure_utc(result.certificate.not_valid_after)

    return RootCAResponse(
        artifact_id=result.artifact.id,
        algorithm=result.algorithm,
        serial_number=serial_hex,
        subject=result.certificate.subject.rfc4514_string(),
        fingerprint_sha256=fingerprint,
        issued_at=issued_at,
        expires_at=expires_at,
    )


@router.get("/root/certificate", response_model=RootCertificateExportResponse)
async def export_root_certificate(
    session: AsyncSession = Depends(get_db),
) -> RootCertificateExportResponse:
    """Return the PEM encoded root certificate."""

    try:
        certificate_pem = await ca_service.export_root_certificate(session=session)
    except RootCANotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return RootCertificateExportResponse(certificate_pem=certificate_pem)


@router.post("/certificates/issue", response_model=CertificateIssueResponse)
async def issue_certificate(
    payload: CertificateIssueRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CertificateIssueResponse:
    """Issue a certificate for the authenticated user."""

    try:
        result = await ca_service.issue_certificate(
            session=session,
            owner_id=current_user.id,
            common_name=payload.common_name,
            organization=payload.organization,
            algorithm=payload.algorithm,
            validity_days=payload.validity_days,
            p12_passphrase=payload.p12_passphrase,
            actor_id=current_user.id,
        )
    except RootCANotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except CertificateIssuanceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except CertificateAuthorityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    encoded_bundle = base64.b64encode(result.p12_bytes).decode("utf-8")
    status_enum = CertificateStatus(result.certificate.status)

    return CertificateIssueResponse(
        certificate_id=result.certificate.id,
        serial_number=result.certificate.serial_number,
        status=status_enum,
        issued_at=result.certificate.issued_at,
        expires_at=result.certificate.expires_at,
        certificate_pem=result.certificate_pem,
        p12_bundle=encoded_bundle,
    )


@router.post("/certificates/import", response_model=CertificateImportResponse)
async def import_certificate(
    payload: CertificateImportRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CertificateImportResponse:
    """Import an externally issued PKCS#12 bundle."""

    try:
        bundle_bytes = base64.b64decode(payload.p12_bundle, validate=True)
    except binascii.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PKCS#12 bundle encoding",
        ) from exc

    try:
        result = await ca_service.import_certificate_from_p12(
            session=session,
            owner_id=current_user.id,
            bundle_bytes=bundle_bytes,
            passphrase=payload.passphrase,
            actor_id=current_user.id,
        )
    except CertificateImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except CertificateAuthorityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    status_enum = CertificateStatus(result.certificate.status)

    return CertificateImportResponse(
        certificate_id=result.certificate.id,
        serial_number=result.certificate.serial_number,
        status=status_enum,
        issued_at=result.certificate.issued_at,
        expires_at=result.certificate.expires_at,
        certificate_pem=result.certificate_pem,
        p12_bundle=None,
    )


@router.get("/certificates", response_model=CertificateListResponse)
async def list_certificates(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CertificateListResponse:
    """Return the authenticated user's certificates."""

    certificates = await certificate_crud.list_certificates_for_owner(
        session=session,
        owner_id=current_user.id,
    )
    summaries = [
        CertificateSummary(
            certificate_id=cert.id,
            serial_number=cert.serial_number,
            status=CertificateStatus(cert.status),
            issued_at=cert.issued_at,
            expires_at=cert.expires_at,
            subject_common_name=cert.subject_common_name,
        )
        for cert in certificates
    ]
    return CertificateListResponse(certificates=summaries)


@router.post(
    "/certificates/{certificate_id}/revoke", response_model=CertificateRevokeResponse
)
async def revoke_certificate(
    certificate_id: UUID,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_db),
) -> CertificateRevokeResponse:
    """Revoke a certificate by identifier."""

    certificate = await _load_certificate_or_404(
        session=session, certificate_id=certificate_id
    )

    try:
        revoked = await ca_service.revoke_certificate(
            session=session,
            certificate=certificate,
            actor_id=current_user.id,
        )
    except CertificateRevocationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    status_enum = CertificateStatus(revoked.status)
    revoked_at = revoked.updated_at

    return CertificateRevokeResponse(
        certificate_id=revoked.id,
        status=status_enum,
        revoked_at=revoked_at,
    )


@router.post("/crl", response_model=CRLGenerateResponse)
async def generate_crl(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_db),
) -> CRLGenerateResponse:
    """Generate a new certificate revocation list."""

    try:
        result = await ca_service.generate_crl(
            session=session, actor_id=current_user.id
        )
    except CertificateAuthorityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return CRLGenerateResponse(
        artifact_id=result.artifact.id,
        name=result.artifact.name,
        created_at=result.artifact.created_at,
        crl_pem=result.crl_pem,
        revoked_serials=list(result.revoked_serials),
    )


@router.get("/crl", response_model=CRLListResponse)
async def list_crls(session: AsyncSession = Depends(get_db)) -> CRLListResponse:
    """Return a list of published certificate revocation lists."""

    artifacts = await ca_service.list_crls(session=session)
    entries = [
        CRLMetadata(
            artifact_id=artifact.id,
            name=artifact.name,
            created_at=artifact.created_at,
        )
        for artifact in artifacts
    ]
    return CRLListResponse(crls=entries)


@router.get("/crl/{artifact_id}", response_class=PlainTextResponse)
async def download_crl(
    artifact_id: UUID, session: AsyncSession = Depends(get_db)
) -> PlainTextResponse:
    """Download the specified certificate revocation list."""

    try:
        crl_pem = await ca_service.load_crl_pem(
            session=session, artifact_id=artifact_id
        )
    except CertificateAuthorityError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return PlainTextResponse(content=crl_pem, media_type="application/pkix-crl")


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def _load_certificate_or_404(
    *, session: AsyncSession, certificate_id: UUID
) -> Certificate:
    certificate = await certificate_crud.get_certificate_by_id(
        session=session, certificate_id=certificate_id
    )
    if certificate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found"
        )
    return certificate
