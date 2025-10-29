"""PDF signing service using pyHanko with certificate and seal support."""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import BinaryIO
from uuid import UUID, uuid4

from asn1crypto import keys as asn1_keys
from asn1crypto import x509 as asn1_x509  # type: ignore[import-untyped]
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers
from pyhanko.sign.fields import SigSeedSubFilter
from pyhanko_certvalidator.registry import SimpleCertificateStore
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud import certificate as certificate_crud
from app.crud import seal as seal_crud
from app.models.certificate import Certificate, CertificateStatus
from app.models.seal import Seal
from app.services.storage import EncryptedStorageService, StorageError
from app.services.tsa_client import TSAClient


class PDFSigningError(Exception):
    """Base error for PDF signing operations."""


class PDFValidationError(PDFSigningError):
    """Raised when PDF validation fails."""


class CertificateNotFoundError(PDFSigningError):
    """Raised when certificate is not found."""


class CertificateInvalidError(PDFSigningError):
    """Raised when certificate cannot be used for signing."""


class SealNotFoundError(PDFSigningError):
    """Raised when seal is not found."""


class SignatureError(PDFSigningError):
    """Raised when signature operation fails."""


class SignatureVisibility(str, Enum):
    """Visibility mode for PDF signatures."""

    VISIBLE = "visible"
    INVISIBLE = "invisible"


@dataclass(slots=True)
class SignatureCoordinates:
    """Coordinates for visible signature placement."""

    page: int
    x: float
    y: float
    width: float
    height: float


@dataclass(slots=True)
class SignatureMetadata:
    """Optional metadata for signatures."""

    reason: str | None = None
    location: str | None = None
    contact_info: str | None = None


@dataclass(slots=True)
class SigningResult:
    """Result of a PDF signing operation."""

    document_id: str
    signed_pdf: bytes
    signed_at: datetime
    certificate_id: UUID
    seal_id: UUID | None
    visibility: SignatureVisibility
    tsa_used: bool
    ltv_embedded: bool
    file_size: int


class PDFSigningService:
    """High-level service for signing PDF documents with pyHanko."""

    def __init__(
        self,
        storage_service: EncryptedStorageService | None = None,
        tsa_client: TSAClient | None = None,
    ) -> None:
        self._storage = storage_service or EncryptedStorageService()
        self._tsa = tsa_client or TSAClient()
        self._pdf_max_bytes = settings.pdf_max_bytes
        self._allowed_content_types = {
            ct.lower() for ct in settings.pdf_allowed_content_types
        }

    async def sign_pdf(
        self,
        *,
        session: AsyncSession,
        pdf_data: bytes,
        certificate_id: UUID,
        user_id: int,
        seal_id: UUID | None = None,
        visibility: SignatureVisibility = SignatureVisibility.INVISIBLE,
        coordinates: SignatureCoordinates | None = None,
        metadata: SignatureMetadata | None = None,
        use_tsa: bool = False,
        embed_ltv: bool = False,
    ) -> SigningResult:
        """Sign a single PDF document."""

        self._validate_pdf(pdf_data)

        certificate = await self._load_certificate(
            session=session,
            certificate_id=certificate_id,
            user_id=user_id,
        )

        seal_image: bytes | None = None
        if seal_id:
            seal_image = await self._load_seal_image(
                session=session,
                seal_id=seal_id,
                user_id=user_id,
            )

        signer = await self._create_signer(
            session=session,
            certificate=certificate,
            use_tsa=use_tsa,
        )

        signed_pdf = await self._apply_signature(
            pdf_data=pdf_data,
            signer=signer,
            visibility=visibility,
            coordinates=coordinates,
            seal_image=seal_image,
            metadata=metadata,
            embed_ltv=embed_ltv,
        )

        document_id = uuid4().hex
        signed_at = datetime.now(timezone.utc)

        return SigningResult(
            document_id=document_id,
            signed_pdf=signed_pdf,
            signed_at=signed_at,
            certificate_id=certificate_id,
            seal_id=seal_id,
            visibility=visibility,
            tsa_used=use_tsa and self._tsa.is_configured(),
            ltv_embedded=embed_ltv,
            file_size=len(signed_pdf),
        )

    async def batch_sign_pdfs(
        self,
        *,
        session: AsyncSession,
        pdfs: list[tuple[str, bytes]],
        certificate_id: UUID,
        user_id: int,
        seal_id: UUID | None = None,
        visibility: SignatureVisibility = SignatureVisibility.INVISIBLE,
        coordinates: SignatureCoordinates | None = None,
        metadata: SignatureMetadata | None = None,
        use_tsa: bool = False,
        embed_ltv: bool = False,
    ) -> list[SigningResult | Exception]:
        """Sign multiple PDF documents in batch."""

        if len(pdfs) > settings.pdf_batch_max_count:
            raise PDFValidationError(
                f"Batch size {len(pdfs)} exceeds maximum of {settings.pdf_batch_max_count}"
            )

        certificate = await self._load_certificate(
            session=session,
            certificate_id=certificate_id,
            user_id=user_id,
        )

        seal_image: bytes | None = None
        if seal_id:
            seal_image = await self._load_seal_image(
                session=session,
                seal_id=seal_id,
                user_id=user_id,
            )

        signer = await self._create_signer(
            session=session,
            certificate=certificate,
            use_tsa=use_tsa,
        )

        results: list[SigningResult | Exception] = []

        for filename, pdf_data in pdfs:
            try:
                self._validate_pdf(pdf_data)

                signed_pdf = await self._apply_signature(
                    pdf_data=pdf_data,
                    signer=signer,
                    visibility=visibility,
                    coordinates=coordinates,
                    seal_image=seal_image,
                    metadata=metadata,
                    embed_ltv=embed_ltv,
                )

                document_id = uuid4().hex
                signed_at = datetime.now(timezone.utc)

                results.append(
                    SigningResult(
                        document_id=document_id,
                        signed_pdf=signed_pdf,
                        signed_at=signed_at,
                        certificate_id=certificate_id,
                        seal_id=seal_id,
                        visibility=visibility,
                        tsa_used=use_tsa and self._tsa.is_configured(),
                        ltv_embedded=embed_ltv,
                        file_size=len(signed_pdf),
                    )
                )
            except Exception as exc:
                results.append(exc)

        return results

    def _validate_pdf(self, pdf_data: bytes) -> None:
        """Validate PDF content and size."""

        if len(pdf_data) == 0:
            raise PDFValidationError("PDF data is empty")

        if len(pdf_data) > self._pdf_max_bytes:
            raise PDFValidationError(
                f"PDF size {len(pdf_data)} bytes exceeds maximum of {self._pdf_max_bytes} bytes"
            )

        if not pdf_data.startswith(b"%PDF-"):
            raise PDFValidationError("Invalid PDF header")

    async def _load_certificate(
        self,
        *,
        session: AsyncSession,
        certificate_id: UUID,
        user_id: int,
    ) -> Certificate:
        """Load and validate a certificate for signing."""

        certificate = await certificate_crud.get_certificate_by_id(
            session=session,
            certificate_id=certificate_id,
        )

        if certificate is None:
            raise CertificateNotFoundError(f"Certificate {certificate_id} not found")

        if certificate.owner_id != user_id:
            raise CertificateInvalidError("Certificate does not belong to user")

        if certificate.status != CertificateStatus.ACTIVE.value:
            raise CertificateInvalidError(
                f"Certificate is not active (status: {certificate.status})"
            )

        now = datetime.now(timezone.utc)
        if certificate.expires_at < now:
            raise CertificateInvalidError("Certificate has expired")

        return certificate

    async def _load_seal_image(
        self,
        *,
        session: AsyncSession,
        seal_id: UUID,
        user_id: int,
    ) -> bytes:
        """Load a seal image from storage."""

        seal = await seal_crud.get_seal_by_id(session=session, seal_id=seal_id)

        if seal is None:
            raise SealNotFoundError(f"Seal {seal_id} not found")

        if seal.owner_id != user_id:
            raise SealNotFoundError("Seal does not belong to user")

        if seal.image_secret_id is None:
            raise SealNotFoundError("Seal has no image data")

        try:
            return await self._storage.load_seal_image(
                session=session,
                secret_id=seal.image_secret_id,
            )
        except StorageError as exc:
            raise SealNotFoundError(f"Failed to load seal image: {exc}") from exc

    async def _create_signer(
        self,
        *,
        session: AsyncSession,
        certificate: Certificate,
        use_tsa: bool,
    ) -> signers.SimpleSigner:
        """Create a pyHanko signer from certificate and key material."""

        if certificate.private_key_secret_id is None:
            raise CertificateInvalidError("Certificate has no associated private key")

        try:
            private_key_pem = await self._storage.load_private_key(
                session=session,
                secret_id=certificate.private_key_secret_id,
            )
        except StorageError as exc:
            raise CertificateInvalidError(f"Failed to load private key: {exc}") from exc

        try:
            asn1_cert = asn1_x509.Certificate.load(
                x509.load_pem_x509_certificate(
                    certificate.certificate_pem.encode("utf-8")
                ).public_bytes(serialization.Encoding.DER)
            )
        except Exception as exc:
            raise CertificateInvalidError(
                f"Failed to parse certificate: {exc}"
            ) from exc

        try:
            asn1_key = asn1_keys.PrivateKeyInfo.load(
                serialization.load_pem_private_key(
                    private_key_pem.encode("utf-8"),
                    password=None,
                ).private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        except Exception as exc:
            raise CertificateInvalidError(
                f"Failed to parse private key: {exc}"
            ) from exc

        cert_registry = SimpleCertificateStore()

        return signers.SimpleSigner(
            signing_cert=asn1_cert,
            signing_key=asn1_key,
            cert_registry=cert_registry,
            signature_mechanism=None,
        )

    async def _apply_signature(
        self,
        *,
        pdf_data: bytes,
        signer: signers.SimpleSigner,
        visibility: SignatureVisibility,
        coordinates: SignatureCoordinates | None,
        seal_image: bytes | None,
        metadata: SignatureMetadata | None,
        embed_ltv: bool,
    ) -> bytes:
        """Apply signature to PDF document."""

        try:
            input_stream = io.BytesIO(pdf_data)
            writer = IncrementalPdfFileWriter(input_stream)

            sig_meta = signers.PdfSignatureMetadata(
                field_name="Signature",
                md_algorithm="sha256",
                subfilter=SigSeedSubFilter.ADOBE_PKCS7_DETACHED,
                reason=metadata.reason if metadata else None,
                location=metadata.location if metadata else None,
                contact_info=metadata.contact_info if metadata else None,
                embed_validation_info=embed_ltv,
            )

            output = io.BytesIO()

            if visibility == SignatureVisibility.VISIBLE and coordinates:
                sig_field = fields.SigFieldSpec(
                    sig_field_name="Signature",
                    on_page=coordinates.page - 1,
                    box=(
                        int(coordinates.x),
                        int(coordinates.y),
                        int(coordinates.x + coordinates.width),
                        int(coordinates.y + coordinates.height),
                    ),
                )

                fields.append_signature_field(writer, sig_field)

                signers.sign_pdf(
                    writer,
                    signature_meta=sig_meta,
                    signer=signer,
                    existing_fields_only=True,
                    output=output,
                )
            else:
                signers.sign_pdf(
                    writer,
                    signature_meta=sig_meta,
                    signer=signer,
                    output=output,
                )

            return output.getvalue()

        except Exception as exc:
            raise SignatureError(f"Failed to sign PDF: {exc}") from exc
