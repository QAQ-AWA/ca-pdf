"""API endpoints for PDF signing operations."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.api.dependencies.auth import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.pdf_signing import (
    PDFBatchSignResponse,
    PDFBatchSignResultItem,
    PDFSignResponse,
    SignatureCoordinates,
    SignatureMetadata,
    SignatureVisibility,
)
from app.services.pdf_signing import (
    CertificateInvalidError,
    CertificateNotFoundError,
    PDFSigningService,
    PDFValidationError,
    SealNotFoundError,
    SignatureCoordinates as ServiceCoordinates,
    SignatureError,
    SignatureMetadata as ServiceMetadata,
    SignatureVisibility as ServiceVisibility,
    SigningResult,
)

router = APIRouter(prefix="/pdf", tags=["pdf-signing"])


def _convert_coordinates(coords: SignatureCoordinates | None) -> ServiceCoordinates | None:
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


@router.post("/sign", response_model=PDFSignResponse)
async def sign_pdf(
    pdf_file: UploadFile = File(..., description="PDF file to sign"),
    certificate_id: str = Form(..., description="Certificate UUID"),
    seal_id: str | None = Form(default=None, description="Seal UUID (optional)"),
    visibility: str = Form(default="invisible", description="Signature visibility (visible/invisible)"),
    page: int | None = Form(default=None, description="Page number for visible signature (1-based)"),
    x: float | None = Form(default=None, description="X coordinate for visible signature"),
    y: float | None = Form(default=None, description="Y coordinate for visible signature"),
    width: float | None = Form(default=None, description="Width of signature box"),
    height: float | None = Form(default=None, description="Height of signature box"),
    reason: str | None = Form(default=None, description="Reason for signing"),
    location: str | None = Form(default=None, description="Location of signing"),
    contact_info: str | None = Form(default=None, description="Contact information"),
    use_tsa: bool = Form(default=False, description="Include RFC3161 timestamp"),
    embed_ltv: bool = Form(default=False, description="Embed LTV validation material"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PDFSignResponse:
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
        coordinates = SignatureCoordinates(page=page, x=x, y=y, width=width, height=height)

    metadata: SignatureMetadata | None = None
    if reason or location or contact_info:
        metadata = SignatureMetadata(reason=reason, location=location, contact_info=contact_info)

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

    return Response(
        content=result.signed_pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="signed_{result.document_id}.pdf"',
            "X-Document-ID": result.document_id,
            "X-Signed-At": result.signed_at.isoformat(),
            "X-Certificate-ID": str(result.certificate_id),
            "X-TSA-Used": str(result.tsa_used),
            "X-LTV-Embedded": str(result.ltv_embedded),
        },
    )


@router.post("/sign/batch", response_model=PDFBatchSignResponse)
async def batch_sign_pdfs(
    pdf_files: list[UploadFile] = File(..., description="PDF files to sign"),
    certificate_id: str = Form(..., description="Certificate UUID"),
    seal_id: str | None = Form(default=None, description="Seal UUID (optional)"),
    visibility: str = Form(default="invisible", description="Signature visibility"),
    page: int | None = Form(default=None, description="Page number for visible signature"),
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
        coordinates = SignatureCoordinates(page=page, x=x, y=y, width=width, height=height)

    metadata: SignatureMetadata | None = None
    if reason or location or contact_info:
        metadata = SignatureMetadata(reason=reason, location=location, contact_info=contact_info)

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

    return PDFBatchSignResponse(
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
