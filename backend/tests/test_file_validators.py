from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import BytesIO

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from PIL import Image
from pypdf import PdfWriter

from app.core.file_validators import (
    CertificateValidator,
    PDFValidator,
    SealImageValidator,
)


def _build_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _build_png(size: tuple[int, int]) -> bytes:
    image = Image.new("RGBA", size, (255, 0, 0, 255))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _build_pkcs12_bundle(
    *,
    password: str,
    valid_from: datetime,
    valid_to: datetime,
) -> tuple[bytes, x509.Certificate]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test Certificate")])

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(valid_from)
        .not_valid_after(valid_to)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
    )

    certificate = builder.sign(private_key=private_key, algorithm=hashes.SHA256())

    bundle_bytes = pkcs12.serialize_key_and_certificates(
        name=b"test",
        key=private_key,
        cert=certificate,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(
            password.encode("utf-8")
        ),
    )

    return bundle_bytes, certificate


class TestPDFValidator:
    def test_accepts_valid_pdf(self) -> None:
        pdf_bytes = _build_pdf()

        is_valid, error = PDFValidator.validate(pdf_bytes, "document.pdf")

        assert is_valid is True
        assert error is None

    def test_rejects_invalid_extension(self) -> None:
        pdf_bytes = _build_pdf()

        is_valid, error = PDFValidator.validate(pdf_bytes, "document.txt")

        assert is_valid is False
        assert error is not None and "PDF" in error

    def test_rejects_corrupted_pdf(self) -> None:
        pdf_bytes = b"not-a-valid-pdf"

        is_valid, error = PDFValidator.validate(pdf_bytes, "corrupted.pdf")

        assert is_valid is False
        assert error is not None
        assert "invalid" in error.lower() or "corrupt" in error.lower()

    def test_rejects_oversized_pdf(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(PDFValidator, "MAX_FILE_SIZE", 100)
        pdf_bytes = _build_pdf()

        is_valid, error = PDFValidator.validate(pdf_bytes, "large.pdf")

        assert is_valid is False
        assert error is not None
        assert "exceeds" in error.lower()


class TestSealImageValidator:
    def test_accepts_valid_png(self) -> None:
        png_bytes = _build_png((150, 150))

        is_valid, error = SealImageValidator.validate(png_bytes, "seal.png")

        assert is_valid is True
        assert error is None

    def test_rejects_small_png(self) -> None:
        png_bytes = _build_png((50, 50))

        is_valid, error = SealImageValidator.validate(png_bytes, "small.png")

        assert is_valid is False
        assert error is not None
        assert "too small" in error.lower()

    def test_accepts_valid_svg(self) -> None:
        svg_bytes = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"></svg>'
        )

        is_valid, error = SealImageValidator.validate(svg_bytes, "seal.svg")

        assert is_valid is True
        assert error is None

    def test_rejects_invalid_svg(self) -> None:
        svg_bytes = b"<xml><invalid /></xml>"

        is_valid, error = SealImageValidator.validate(svg_bytes, "invalid.svg")

        assert is_valid is False
        assert error is not None
        assert "svg" in error.lower()

    def test_rejects_wrong_extension(self) -> None:
        png_bytes = _build_png((150, 150))

        is_valid, error = SealImageValidator.validate(png_bytes, "seal.jpg")

        assert is_valid is False
        assert error is not None
        assert "png or svg" in error.lower()


class TestCertificateValidator:
    def test_accepts_valid_certificate(self) -> None:
        now = datetime.now(timezone.utc)
        bundle_bytes, _ = _build_pkcs12_bundle(
            password="secret",
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=365),
        )

        is_valid, error = CertificateValidator.validate(
            bundle_bytes, "bundle.p12", password="secret"
        )

        assert is_valid is True
        assert error is None

    def test_rejects_expired_certificate(self) -> None:
        now = datetime.now(timezone.utc)
        bundle_bytes, _ = _build_pkcs12_bundle(
            password="secret",
            valid_from=now - timedelta(days=365),
            valid_to=now - timedelta(days=1),
        )

        is_valid, error = CertificateValidator.validate(
            bundle_bytes, "expired.p12", password="secret"
        )

        assert is_valid is False
        assert error is not None
        assert "expired" in error.lower()

    def test_rejects_incorrect_password(self) -> None:
        now = datetime.now(timezone.utc)
        bundle_bytes, _ = _build_pkcs12_bundle(
            password="secret",
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=365),
        )

        is_valid, error = CertificateValidator.validate(
            bundle_bytes, "bundle.p12", password="wrong"
        )

        assert is_valid is False
        assert error is not None
        assert "password" in error.lower()

    def test_requires_password(self) -> None:
        now = datetime.now(timezone.utc)
        bundle_bytes, _ = _build_pkcs12_bundle(
            password="secret",
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=365),
        )

        is_valid, error = CertificateValidator.validate(
            bundle_bytes, "bundle.p12", password=None
        )

        assert is_valid is False
        assert error is not None
        assert "password" in error.lower()
