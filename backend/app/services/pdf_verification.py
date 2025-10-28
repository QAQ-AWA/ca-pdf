"""Service for validating PDF signatures using pyHanko."""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from asn1crypto import x509 as asn1_x509  # type: ignore[import-untyped]
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko.sign.validation.errors import SignatureValidationError
from pyhanko.sign.validation.pdf_embedded import EmbeddedPdfSignature
from pyhanko.sign.validation.status import ModificationLevel, PdfSignatureStatus, TimestampSignatureStatus
from pyhanko_certvalidator.context import ValidationContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.certificate_authority import (
    CertificateAuthorityService,
    CertificateAuthorityError,
    RootCANotFoundError,
)


class PDFVerificationError(Exception):
    """Base error raised when signature verification fails."""


class PDFVerificationInputError(PDFVerificationError):
    """Raised when the supplied PDF payload is not valid."""


class PDFVerificationRootCAError(PDFVerificationError):
    """Raised when the managed root certificate authority is unavailable."""


@dataclass(slots=True)
class SignatureVerificationDetails:
    """Detailed outcome for a single embedded signature."""

    field_name: str
    valid: bool
    trusted: bool
    docmdp_ok: bool | None
    modification_level: str | None
    signing_time: datetime | None
    signer_common_name: str | None
    signer_serial_number: str | None
    summary: str
    timestamp_trusted: bool | None
    timestamp_time: datetime | None
    timestamp_summary: str | None
    error: str | None = None


@dataclass(slots=True)
class PDFVerificationReport:
    """Aggregated verification summary for a PDF document."""

    total_signatures: int
    valid_signatures: int
    trusted_signatures: int
    signatures: list[SignatureVerificationDetails]


class PDFVerificationService:
    """High-level service encapsulating PDF signature verification logic."""

    def __init__(self, ca_service: CertificateAuthorityService | None = None) -> None:
        self._ca_service = ca_service or CertificateAuthorityService()

    async def verify_pdf(self, *, session: AsyncSession, pdf_data: bytes) -> PDFVerificationReport:
        """Validate signatures embedded in the supplied PDF payload."""

        if not pdf_data:
            raise PDFVerificationInputError("PDF data is empty")
        if not pdf_data.startswith(b"%PDF-"):
            raise PDFVerificationInputError("Invalid PDF header")

        try:
            reader = PdfFileReader(io.BytesIO(pdf_data))
        except Exception as exc:  # pragma: no cover - defensive branch
            raise PDFVerificationInputError(f"Unable to parse PDF document: {exc}") from exc

        signatures = list(reader.embedded_signatures)
        if not signatures:
            raise PDFVerificationInputError("PDF does not contain any signatures")

        trust_roots = await self._load_trust_roots(session=session)

        reports: list[SignatureVerificationDetails] = []
        valid_count = 0
        trusted_count = 0

        for embedded_signature in signatures:
            details = await self._process_signature(
                embedded_signature=embedded_signature,
                trust_roots=trust_roots,
            )
            reports.append(details)
            if details.valid:
                valid_count += 1
            if details.trusted:
                trusted_count += 1

        return PDFVerificationReport(
            total_signatures=len(reports),
            valid_signatures=valid_count,
            trusted_signatures=trusted_count,
            signatures=reports,
        )

    async def _load_trust_roots(self, *, session: AsyncSession) -> Sequence[asn1_x509.Certificate]:
        """Return ASN.1 certificates that should be trusted for chain validation."""

        try:
            root_pem = await self._ca_service.export_root_certificate(session=session)
        except RootCANotFoundError as exc:
            raise PDFVerificationRootCAError("Root certificate authority has not been generated") from exc
        except CertificateAuthorityError as exc:
            raise PDFVerificationRootCAError(f"Unable to load root certificate: {exc}") from exc

        try:
            root_cert = x509.load_pem_x509_certificate(root_pem.encode("utf-8"))
            root_asn1 = asn1_x509.Certificate.load(root_cert.public_bytes(serialization.Encoding.DER))
        except Exception as exc:  # pragma: no cover - defensive branch
            raise PDFVerificationRootCAError("Stored root certificate is invalid") from exc

        return (root_asn1,)

    async def _process_signature(
        self,
        *,
        embedded_signature: EmbeddedPdfSignature,
        trust_roots: Sequence[asn1_x509.Certificate],
    ) -> SignatureVerificationDetails:
        """Verify a single embedded signature and return structured details."""

        context = ValidationContext(trust_roots=trust_roots, allow_fetching=False)

        try:
            status = validate_pdf_signature(
                embedded_signature,
                signer_validation_context=context,
                ts_validation_context=context,
            )
        except SignatureValidationError as exc:
            return self._build_error_details(
                embedded_signature=embedded_signature,
                reason=str(exc),
            )
        except Exception as exc:  # pragma: no cover - defensive branch
            return self._build_error_details(
                embedded_signature=embedded_signature,
                reason=f"Unexpected validation error: {exc}",
            )

        signer_cert = status.signing_cert or embedded_signature.signer_cert
        signer_common_name: str | None = None
        signer_serial: str | None = None
        if signer_cert is not None:
            try:
                subject = signer_cert.subject.native
                signer_common_name = subject.get("common_name")
            except Exception:  # pragma: no cover - defensive branch
                signer_common_name = None
            try:
                signer_serial = f"{signer_cert.serial_number:X}"
            except Exception:  # pragma: no cover - defensive branch
                signer_serial = None

        timestamp_status = status.timestamp_validity
        timestamp_trusted: bool | None = None
        timestamp_time: datetime | None = None
        timestamp_summary: str | None = None
        if isinstance(timestamp_status, TimestampSignatureStatus):
            timestamp_trusted = bool(timestamp_status.trusted)
            timestamp_time = timestamp_status.timestamp
            timestamp_summary = timestamp_status.summary

        modification_level: str | None = None
        if isinstance(status.modification_level, ModificationLevel):
            modification_level = status.modification_level.name.lower()
        elif status.modification_level is not None:
            modification_level = str(status.modification_level)

        return SignatureVerificationDetails(
            field_name=embedded_signature.field_name,
            valid=bool(status.valid),
            trusted=bool(status.trusted),
            docmdp_ok=status.docmdp_ok,
            modification_level=modification_level,
            signing_time=status.signer_reported_dt,
            signer_common_name=signer_common_name,
            signer_serial_number=signer_serial,
            summary=status.summary,
            timestamp_trusted=timestamp_trusted,
            timestamp_time=timestamp_time,
            timestamp_summary=timestamp_summary,
            error=None,
        )

    def _build_error_details(
        self,
        *,
        embedded_signature: EmbeddedPdfSignature,
        reason: str,
    ) -> SignatureVerificationDetails:
        """Return a structured error result when validation fails unexpectedly."""

        return SignatureVerificationDetails(
            field_name=embedded_signature.field_name,
            valid=False,
            trusted=False,
            docmdp_ok=None,
            modification_level=None,
            signing_time=None,
            signer_common_name=None,
            signer_serial_number=None,
            summary=reason,
            timestamp_trusted=None,
            timestamp_time=None,
            timestamp_summary=None,
            error=reason,
        )
