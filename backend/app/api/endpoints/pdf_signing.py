"""API endpoints for PDF signing operations."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.config import settings
from app.crud import audit_log as audit_log_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.pdf_signing import (
    PDFBatchSignResponse,
    PDFBatchSignResultItem,
    PDFSignResponse,
    PDFVerificationResponse,
    SignatureCoordinates,
    SignatureMetadata,
    SignatureVerificationResult,
    SignatureVisibility,
)
from app.services.pdf_signing import (
    CertificateInvalidError,
    CertificateNotFoundError,
    PDFSigningService,
    PDFValidationError,
    SealNotFoundError,
)
from app.services.pdf_signing import SignatureCoordinates as ServiceCoordinates
from app.services.pdf_signing import SignatureError
from app.services.pdf_signing import SignatureMetadata as ServiceMetadata
from app.services.pdf_signing import SignatureVisibility as ServiceVisibility
from app.services.pdf_signing import SigningResult
from app.services.pdf_verification import (
    PDFVerificationError,
    PDFVerificationInputError,
    PDFVerificationRootCAError,
    PDFVerificationService,
)

router = APIRouter(prefix="/pdf", tags=["pdf-signing"])


def _convert_coordinates(
    coords: SignatureCoordinates | None,
) -> ServiceCoordinates | None:
    """Convert API coordinates to service coordinates."""
    if coords is None:
        return None
    return ServiceCoordinates(
        page=coords.page,
        x=coords.x,
        y=coords.y,
        width=coords.width,
        height=coords.height,
    )


def _convert_metadata(metadata: SignatureMetadata | None) -> ServiceMetadata | None:
    """Convert API metadata to service metadata."""
    if metadata is None:
        return None
    return ServiceMetadata(
        reason=metadata.reason,
        location=metadata.location,
        contact_info=metadata.contact_info,
    )


def _convert_visibility(visibility: SignatureVisibility) -> ServiceVisibility:
    """Convert API visibility to service visibility."""
    return ServiceVisibility(visibility.value)


def _extract_client_ip(request: Request) -> str | None:
    """Determine the originating IP address from the incoming request."""

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    if request.client is not None:
        return request.client.host
    return None


async def _record_audit_event(
    *,
    session: AsyncSession,
    request: Request,
    actor_id: int,
    event_type: str,
    resource: str,
    meta: dict[str, Any] | None = None,
) -> None:
    """Persist an audit event capturing request metadata."""

    await audit_log_crud.create_audit_log(
        session=session,
        actor_id=actor_id,
        event_type=event_type,
        resource=resource,
        meta=meta,
        ip_address=_extract_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        commit=True,
    )


@router.post("/sign")
async def sign_pdf(
    request: Request,
    pdf_file: UploadFile = File(..., description="PDF file to sign"),
    certificate_id: str = Form(..., description="Certificate UUID"),
    seal_id: str | None = Form(default=None, description="Seal UUID (optional)"),
    visibility: str = Form(
        default="invisible", description="Signature visibility (visible/invisible)"
    ),
    page: int | None = Form(
        default=None, description="Page number for visible signature (1-based)"
    ),
    x: float | None = Form(
        default=None, description="X coordinate for visible signature"
    ),
    y: float | None = Form(
        default=None, description="Y coordinate for visible signature"
    ),
    width: float | None = Form(default=None, description="Width of signature box"),
    height: float | None = Form(default=None, description="Height of signature box"),
    reason: str | None = Form(default=None, description="Reason for signing"),
    location: str | None = Form(default=None, description="Location of signing"),
    contact_info: str | None = Form(default=None, description="Contact information"),
    use_tsa: bool = Form(default=False, description="Include RFC3161 timestamp"),
    embed_ltv: bool = Form(default=False, description="Embed LTV validation material"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Sign a single PDF document with a user's certificate."""

    if pdf_file.content_type not in settings.pdf_allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type: {pdf_file.content_type}",
        )

    try:
        pdf_data = await pdf_file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read PDF file: {exc}",
        ) from exc

    try:
        cert_uuid = UUID(certificate_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid certificate_id format",
        ) from exc

    seal_uuid: UUID | None = None
    if seal_id:
        try:
            seal_uuid = UUID(seal_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid seal_id format",
            ) from exc

    try:
        sig_visibility = SignatureVisibility(visibility)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid visibility value: {visibility}",
        ) from exc

    coordinates: SignatureCoordinates | None = None
    if sig_visibility == SignatureVisibility.VISIBLE:
        if page is None or x is None or y is None or width is None or height is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Visible signatures require page, x, y, width, and height",
            )
        coordinates = SignatureCoordinates(
            page=page, x=x, y=y, width=width, height=height
        )

    metadata: SignatureMetadata | None = None
    if reason or location or contact_info:
        metadata = SignatureMetadata(
            reason=reason, location=location, contact_info=contact_info
        )

    original_filename = pdf_file.filename or "document.pdf"
    base_name = Path(original_filename).stem or "document"
    sanitized_base = (
        base_name.replace("\\", "_").replace("/", "_").replace('"', "").strip()
        or "document"
    )
    signed_filename = f"{sanitized_base}-signed.pdf"

    service = PDFSigningService()

    try:
        result = await service.sign_pdf(
            session=session,
            pdf_data=pdf_data,
            certificate_id=cert_uuid,
            user_id=current_user.id,
            seal_id=seal_uuid,
            visibility=_convert_visibility(sig_visibility),
            coordinates=_convert_coordinates(coordinates),
            metadata=_convert_metadata(metadata),
            use_tsa=use_tsa,
            embed_ltv=embed_ltv,
        )
    except PDFValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except CertificateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (CertificateInvalidError, SealNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    await _record_audit_event(
        session=session,
        request=request,
        actor_id=current_user.id,
        event_type="pdf.signature.applied",
        resource="pdf",
        meta={
            "document_id": result.document_id,
            "certificate_id": str(result.certificate_id),
            "seal_id": str(result.seal_id) if result.seal_id else None,
            "visibility": result.visibility.value,
            "tsa_used": result.tsa_used,
            "ltv_embedded": result.ltv_embedded,
            "signed_at": result.signed_at.isoformat(),
            "file_size": result.file_size,
            "original_filename": original_filename,
            "signed_filename": signed_filename,
        },
    )

    quoted_filename = quote(signed_filename)
    content_disposition = f'attachment; filename="{signed_filename}"'
    if quoted_filename != signed_filename:
        content_disposition += f"; filename*=UTF-8''{quoted_filename}"

    headers: dict[str, str] = {
        "Content-Disposition": content_disposition,
        "X-Document-ID": result.document_id,
        "X-Signed-At": result.signed_at.isoformat(),
        "X-Certificate-ID": str(result.certificate_id),
        "X-Visibility": result.visibility.value,
        "X-TSA-Used": str(result.tsa_used).lower(),
        "X-LTV-Embedded": str(result.ltv_embedded).lower(),
        "X-Original-Filename": original_filename,
        "X-Signed-Filename": signed_filename,
    }
    if result.seal_id is not None:
        headers["X-Seal-Id"] = str(result.seal_id)

    pdf_stream = io.BytesIO(result.signed_pdf)
    return StreamingResponse(pdf_stream, media_type="application/pdf", headers=headers)


@router.post("/sign/batch", response_model=PDFBatchSignResponse)
async def batch_sign_pdfs(
    request: Request,
    pdf_files: list[UploadFile] = File(..., description="PDF files to sign"),
    certificate_id: str = Form(..., description="Certificate UUID"),
    seal_id: str | None = Form(default=None, description="Seal UUID (optional)"),
    visibility: str = Form(default="invisible", description="Signature visibility"),
    page: int | None = Form(
        default=None, description="Page number for visible signature"
    ),
    x: float | None = Form(default=None, description="X coordinate"),
    y: float | None = Form(default=None, description="Y coordinate"),
    width: float | None = Form(default=None, description="Width"),
    height: float | None = Form(default=None, description="Height"),
    reason: str | None = Form(default=None, description="Reason for signing"),
    location: str | None = Form(default=None, description="Location"),
    contact_info: str | None = Form(default=None, description="Contact info"),
    use_tsa: bool = Form(default=False, description="Use TSA"),
    embed_ltv: bool = Form(default=False, description="Embed LTV"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PDFBatchSignResponse:
    """Sign multiple PDF documents in batch with the same certificate and settings."""

    if len(pdf_files) > settings.pdf_batch_max_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size exceeds maximum of {settings.pdf_batch_max_count}",
        )

    try:
        cert_uuid = UUID(certificate_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid certificate_id format",
        ) from exc

    seal_uuid: UUID | None = None
    if seal_id:
        try:
            seal_uuid = UUID(seal_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid seal_id format",
            ) from exc

    try:
        sig_visibility = SignatureVisibility(visibility)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid visibility value: {visibility}",
        ) from exc

    coordinates: SignatureCoordinates | None = None
    if sig_visibility == SignatureVisibility.VISIBLE:
        if page is None or x is None or y is None or width is None or height is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Visible signatures require coordinates",
            )
        coordinates = SignatureCoordinates(
            page=page, x=x, y=y, width=width, height=height
        )

    metadata: SignatureMetadata | None = None
    if reason or location or contact_info:
        metadata = SignatureMetadata(
            reason=reason, location=location, contact_info=contact_info
        )

    pdfs: list[tuple[str, bytes]] = []
    for pdf_file in pdf_files:
        if pdf_file.content_type not in settings.pdf_allowed_content_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid content type for {pdf_file.filename}: {pdf_file.content_type}",
            )
        try:
            pdf_data = await pdf_file.read()
            pdfs.append((pdf_file.filename or "unknown.pdf", pdf_data))
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read {pdf_file.filename}: {exc}",
            ) from exc

    service = PDFSigningService()

    try:
        results = await service.batch_sign_pdfs(
            session=session,
            pdfs=pdfs,
            certificate_id=cert_uuid,
            user_id=current_user.id,
            seal_id=seal_uuid,
            visibility=_convert_visibility(sig_visibility),
            coordinates=_convert_coordinates(coordinates),
            metadata=_convert_metadata(metadata),
            use_tsa=use_tsa,
            embed_ltv=embed_ltv,
        )
    except PDFValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except CertificateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (CertificateInvalidError, SealNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    result_items: list[PDFBatchSignResultItem] = []
    successful = 0
    failed = 0

    for idx, result in enumerate(results):
        filename = pdfs[idx][0]
        if isinstance(result, SigningResult):
            result_items.append(
                PDFBatchSignResultItem(
                    filename=filename,
                    success=True,
                    document_id=result.document_id,
                    signed_at=result.signed_at,
                    file_size=result.file_size,
                    error=None,
                )
            )
            successful += 1
        else:
            result_items.append(
                PDFBatchSignResultItem(
                    filename=filename,
                    success=False,
                    document_id=None,
                    signed_at=None,
                    file_size=None,
                    error=str(result),
                )
            )
            failed += 1

    response_payload = PDFBatchSignResponse(
        total=len(pdfs),
        successful=successful,
        failed=failed,
        results=result_items,
        certificate_id=cert_uuid,
        seal_id=seal_uuid,
        visibility=sig_visibility,
        tsa_used=use_tsa,
        ltv_embedded=embed_ltv,
    )

    await _record_audit_event(
        session=session,
        request=request,
        actor_id=current_user.id,
        event_type="pdf.signature.batch_applied",
        resource="pdf",
        meta={
            "total": len(pdfs),
            "successful": successful,
            "failed": failed,
            "certificate_id": str(cert_uuid),
            "seal_id": str(seal_uuid) if seal_uuid else None,
            "visibility": sig_visibility.value,
            "tsa_used": use_tsa,
            "ltv_embedded": embed_ltv,
            "document_ids": [
                item.document_id for item in result_items if item.document_id
            ],
        },
    )

    return response_payload


@router.post("/verify", response_model=PDFVerificationResponse)
async def verify_pdf(
    request: Request,
    pdf_file: UploadFile = File(..., description="Signed PDF to verify"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PDFVerificationResponse:
    """Validate signatures embedded in a PDF document."""

    if pdf_file.content_type not in settings.pdf_allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type: {pdf_file.content_type}",
        )

    try:
        pdf_data = await pdf_file.read()
    except Exception as exc:  # pragma: no cover - defensive branch
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read PDF file: {exc}",
        ) from exc

    verification_service = PDFVerificationService()

    try:
        report = await verification_service.verify_pdf(
            session=session, pdf_data=pdf_data
        )
    except PDFVerificationInputError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except PDFVerificationRootCAError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except PDFVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    response_payload = PDFVerificationResponse(
        total_signatures=report.total_signatures,
        valid_signatures=report.valid_signatures,
        trusted_signatures=report.trusted_signatures,
        all_signatures_valid=report.valid_signatures == report.total_signatures,
        all_signatures_trusted=report.trusted_signatures == report.total_signatures,
        signatures=[
            SignatureVerificationResult(
                field_name=detail.field_name,
                valid=detail.valid,
                trusted=detail.trusted,
                docmdp_ok=detail.docmdp_ok,
                modification_level=detail.modification_level,
                signing_time=detail.signing_time,
                signer_common_name=detail.signer_common_name,
                signer_serial_number=detail.signer_serial_number,
                summary=detail.summary,
                timestamp_trusted=detail.timestamp_trusted,
                timestamp_time=detail.timestamp_time,
                timestamp_summary=detail.timestamp_summary,
                error=detail.error,
            )
            for detail in report.signatures
        ],
    )

    await _record_audit_event(
        session=session,
        request=request,
        actor_id=current_user.id,
        event_type="pdf.signature.verified",
        resource="pdf",
        meta={
            "total_signatures": report.total_signatures,
            "valid_signatures": report.valid_signatures,
            "trusted_signatures": report.trusted_signatures,
            "all_signatures_valid": response_payload.all_signatures_valid,
            "all_signatures_trusted": response_payload.all_signatures_trusted,
            "signature_fields": [detail.field_name for detail in report.signatures],
        },
    )

    return response_payload
