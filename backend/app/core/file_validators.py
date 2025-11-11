from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import magic

from app.core.config import settings

_MAGIC_DETECTOR: Any = None
_MAGIC_DETECTOR_FAILED = False


def _normalize_mime_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore").strip().lower()
    return str(value).strip().lower()


def _detect_mime(buffer: bytes) -> str | None:
    """Detect the MIME type of a payload using python-magic."""

    global _MAGIC_DETECTOR, _MAGIC_DETECTOR_FAILED

    try:
        detected = magic.from_buffer(buffer, mime=True)
    except AttributeError:
        if _MAGIC_DETECTOR_FAILED:
            return None
        if _MAGIC_DETECTOR is None:
            try:
                _MAGIC_DETECTOR = magic.Magic(mime=True)
            except Exception:
                _MAGIC_DETECTOR_FAILED = True
                return None
        try:
            detected = _MAGIC_DETECTOR.from_buffer(buffer)
        except Exception:
            return None
    except Exception:
        return None

    return _normalize_mime_value(detected)


class FileValidator:
    """Base class for file validators."""

    MAX_FILE_SIZE: int = 0

    @classmethod
    def validate(cls, file_content: bytes, filename: str) -> tuple[bool, str | None]:
        raise NotImplementedError


class PDFValidator(FileValidator):
    """Validator for PDF documents."""

    ALLOWED_MIME_TYPES = {mime.lower() for mime in settings.pdf_allowed_content_types}
    MAX_FILE_SIZE = settings.pdf_max_bytes

    @classmethod
    def validate(cls, file_content: bytes, filename: str) -> tuple[bool, str | None]:
        if len(file_content) == 0:
            return False, "PDF file is empty"

        if len(file_content) > cls.MAX_FILE_SIZE:
            max_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File size exceeds {max_mb:.0f}MB limit"

        if not filename.lower().endswith(".pdf"):
            return False, "File must be a PDF (*.pdf)"

        mime = _detect_mime(file_content)
        if mime is None or mime not in cls.ALLOWED_MIME_TYPES:
            expected = ", ".join(sorted(cls.ALLOWED_MIME_TYPES)) or "application/pdf"
            return (
                False,
                f"Invalid MIME type: {mime or 'unknown'}. Expected: {expected}",
            )

        if not file_content.startswith(b"%PDF"):
            return False, "Invalid PDF file: missing PDF header"

        try:
            from pypdf import PdfReader
            from pypdf.errors import PdfReadError
        except ImportError as exc:  # pragma: no cover - defensive branch
            return False, f"PDF validation dependency missing: {exc}"

        try:
            reader = PdfReader(BytesIO(file_content))
            if len(reader.pages) == 0:
                return False, "PDF file appears to be empty"
        except PdfReadError as exc:
            return False, f"PDF file is corrupted or invalid: {exc}"
        except Exception as exc:  # pragma: no cover - defensive branch
            return False, f"PDF file is corrupted or invalid: {exc}"

        return True, None


class SealImageValidator(FileValidator):
    """Validator for seal image uploads."""

    ALLOWED_MIME_TYPES = {"image/png", "image/svg+xml"}
    ALLOWED_EXTENSIONS = {".png", ".svg"}
    MIN_DIMENSIONS = (100, 100)
    MAX_DIMENSIONS = (2000, 2000)
    MAX_FILE_SIZE = settings.seal_image_max_bytes

    @classmethod
    def validate(cls, file_content: bytes, filename: str) -> tuple[bool, str | None]:
        if len(file_content) == 0:
            return False, "Seal image file is empty"

        if len(file_content) > cls.MAX_FILE_SIZE:
            max_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"Seal image size exceeds {max_mb:.0f}MB limit"

        extension = Path(filename).suffix.lower()
        if extension not in cls.ALLOWED_EXTENSIONS:
            return (
                False,
                f"Seal image must be PNG or SVG. Got: {extension or 'unknown'}",
            )

        mime = _detect_mime(file_content)
        if mime is None or mime not in cls.ALLOWED_MIME_TYPES:
            expected = ", ".join(sorted(cls.ALLOWED_MIME_TYPES))
            return (
                False,
                f"Invalid MIME type: {mime or 'unknown'}. Expected: {expected}",
            )

        if extension == ".png":
            try:
                from PIL import Image
            except ImportError as exc:  # pragma: no cover - defensive branch
                return False, f"PNG validation dependency missing: {exc}"

            try:
                with Image.open(BytesIO(file_content)) as img:
                    width, height = img.size
            except Exception as exc:
                return False, f"Invalid PNG file: {exc}"

            min_width, min_height = cls.MIN_DIMENSIONS
            max_width, max_height = cls.MAX_DIMENSIONS

            if width < min_width or height < min_height:
                return (
                    False,
                    f"Seal image too small. Minimum: {min_width}x{min_height}px",
                )
            if width > max_width or height > max_height:
                return (
                    False,
                    f"Seal image too large. Maximum: {max_width}x{max_height}px",
                )

        if extension == ".svg":
            try:
                import xml.etree.ElementTree as ET

                root = ET.fromstring(file_content)
            except Exception as exc:
                return False, f"Invalid SVG file: {exc}"

            tag = root.tag.lower()
            if not (tag == "svg" or tag.endswith("}svg")):
                return False, "Invalid SVG file: root element is not <svg>"

        return True, None


class CertificateValidator(FileValidator):
    """Validator for PKCS#12 certificate bundles."""

    ALLOWED_EXTENSIONS = {".p12", ".pfx"}
    MAX_FILE_SIZE = 10 * 1024 * 1024

    @classmethod
    def validate(
        cls,
        file_content: bytes,
        filename: str,
        password: str | bytes | None = None,
    ) -> tuple[bool, str | None]:
        if len(file_content) == 0:
            return False, "Certificate file is empty"

        if len(file_content) > cls.MAX_FILE_SIZE:
            max_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"Certificate file size exceeds {max_mb:.0f}MB limit"

        extension = Path(filename).suffix.lower()
        if extension not in cls.ALLOWED_EXTENSIONS:
            return (
                False,
                f"Certificate must be P12 or PFX. Got: {extension or 'unknown'}",
            )

        if password is None:
            return False, "Certificate password is required"

        password_bytes = (
            password.encode("utf-8") if isinstance(password, str) else password
        )

        try:
            from cryptography.hazmat.primitives.serialization import pkcs12
        except ImportError as exc:  # pragma: no cover - defensive branch
            return False, f"Certificate validation dependency missing: {exc}"

        try:
            private_key, certificate, _additional = pkcs12.load_key_and_certificates(
                file_content,
                password_bytes,
            )
        except ValueError as exc:
            message = str(exc)
            if "mac check failed" in message.lower():
                return False, "Incorrect certificate password"
            return False, f"Invalid certificate file: {message}"
        except Exception as exc:  # pragma: no cover - defensive branch
            return False, f"Failed to parse certificate: {exc}"

        if private_key is None:
            return False, "Certificate does not contain a private key"

        if certificate is None:
            return False, "Certificate does not contain a certificate"

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        not_valid_before = getattr(certificate, "not_valid_before_utc", None)
        if not_valid_before is None:
            not_valid_before = certificate.not_valid_before
            if not_valid_before.tzinfo is None:
                not_valid_before = not_valid_before.replace(tzinfo=timezone.utc)
            else:
                not_valid_before = not_valid_before.astimezone(timezone.utc)

        not_valid_after = getattr(certificate, "not_valid_after_utc", None)
        if not_valid_after is None:
            not_valid_after = certificate.not_valid_after
            if not_valid_after.tzinfo is None:
                not_valid_after = not_valid_after.replace(tzinfo=timezone.utc)
            else:
                not_valid_after = not_valid_after.astimezone(timezone.utc)

        if not_valid_before > now:
            return (
                False,
                f"Certificate is not yet valid (valid from {not_valid_before})",
            )

        if not_valid_after < now:
            return False, f"Certificate has expired (expired on {not_valid_after})"

        return True, None
