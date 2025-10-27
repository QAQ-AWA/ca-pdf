"""Tests for PDF signing service and API endpoints."""

from __future__ import annotations

import io
from uuid import uuid4

import pytest
from httpx import AsyncClient
from pypdf import PdfReader, PdfWriter
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import certificate as certificate_crud
from app.crud import seal as seal_crud
from app.db.session import get_db
from app.services.certificate_authority import (
    CertificateAuthorityService,
    LeafKeyAlgorithm,
    RootKeyAlgorithm,
)
from app.services.pdf_signing import (
    CertificateInvalidError,
    CertificateNotFoundError,
    PDFSigningService,
    PDFValidationError,
    SealNotFoundError,
    SignatureCoordinates,
    SignatureMetadata,
    SignatureVisibility,
)
from app.services.pdf_verification import PDFVerificationInputError, PDFVerificationService
from app.services.storage import EncryptedStorageService


def create_minimal_pdf() -> bytes:
    """Create a minimal valid PDF for testing."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def create_multipage_pdf(pages: int = 3) -> bytes:
    """Create a multi-page PDF for testing."""
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.fixture
async def db_session() -> AsyncSession:
    """Provide a database session for testing."""
    async for session in get_db():
        return session


@pytest.fixture
async def ca_service() -> CertificateAuthorityService:
    """Provide a certificate authority service instance."""
    return CertificateAuthorityService()


@pytest.fixture
async def pdf_service() -> PDFSigningService:
    """Provide a PDF signing service instance."""
    return PDFSigningService()


@pytest.fixture
async def verification_service() -> PDFVerificationService:
    """Provide a PDF verification service instance."""
    return PDFVerificationService()


@pytest.fixture
async def root_ca(ca_service: CertificateAuthorityService, db_session: AsyncSession) -> None:
    """Generate a root CA for testing."""
    await ca_service.generate_root_ca(
        session=db_session,
        algorithm=RootKeyAlgorithm.EC_P256,
        common_name="Test Root CA",
        organization="Test Org",
        actor_id=None,
        validity_days=365,
    )


@pytest.fixture
async def user_certificate(
    ca_service: CertificateAuthorityService,
    db_session: AsyncSession,
    root_ca: None,
) -> tuple[str, int]:
    """Issue a user certificate for testing."""
    result = await ca_service.issue_certificate(
        session=db_session,
        owner_id=1,
        common_name="Test User",
        organization="Test Org",
        algorithm=LeafKeyAlgorithm.EC_P256,
        actor_id=None,
        validity_days=365,
    )
    return str(result.certificate.id), result.certificate.owner_id


@pytest.fixture
async def seal_image(db_session: AsyncSession) -> str:
    """Create a seal image for testing."""
    storage = EncryptedStorageService()
    png_data = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
        b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    file_metadata, secret = await storage.store_seal_image(
        session=db_session,
        data=png_data,
        content_type="image/png",
        owner_id=1,
        filename="test-seal.png",
    )
    seal = await seal_crud.create_seal(
        session=db_session,
        owner_id=1,
        name="Test Seal",
        description="Test seal image",
        image_file_id=file_metadata.id,
        image_secret_id=secret.id,
    )
    return str(seal.id)


class TestPDFValidation:
    """Tests for PDF validation."""

    async def test_validate_empty_pdf(self, pdf_service: PDFSigningService) -> None:
        """Test that empty PDF data is rejected."""
        with pytest.raises(PDFValidationError, match="empty"):
            pdf_service._validate_pdf(b"")

    async def test_validate_invalid_header(self, pdf_service: PDFSigningService) -> None:
        """Test that invalid PDF headers are rejected."""
        with pytest.raises(PDFValidationError, match="header"):
            pdf_service._validate_pdf(b"Not a PDF file")

    async def test_validate_oversized_pdf(self, pdf_service: PDFSigningService) -> None:
        """Test that oversized PDFs are rejected."""
        large_pdf = b"%PDF-1.4\n" + b"x" * (60 * 1024 * 1024)
        with pytest.raises(PDFValidationError, match="exceeds maximum"):
            pdf_service._validate_pdf(large_pdf)

    async def test_validate_valid_pdf(self, pdf_service: PDFSigningService) -> None:
        """Test that valid PDFs pass validation."""
        pdf_data = create_minimal_pdf()
        pdf_service._validate_pdf(pdf_data)


class TestCertificateLoading:
    """Tests for certificate loading and validation."""

    async def test_load_nonexistent_certificate(
        self,
        pdf_service: PDFSigningService,
        db_session: AsyncSession,
    ) -> None:
        """Test loading a non-existent certificate."""
        with pytest.raises(CertificateNotFoundError):
            await pdf_service._load_certificate(
                session=db_session,
                certificate_id=uuid4(),
                user_id=1,
            )

    async def test_load_certificate_wrong_owner(
        self,
        pdf_service: PDFSigningService,
        db_session: AsyncSession,
        user_certificate: tuple[str, int],
    ) -> None:
        """Test loading a certificate owned by another user."""
        cert_id, _ = user_certificate
        with pytest.raises(CertificateInvalidError, match="does not belong"):
            await pdf_service._load_certificate(
                session=db_session,
                certificate_id=cert_id,
                user_id=999,
            )

    async def test_load_valid_certificate(
        self,
        pdf_service: PDFSigningService,
        db_session: AsyncSession,
        user_certificate: tuple[str, int],
    ) -> None:
        """Test loading a valid certificate."""
        cert_id, owner_id = user_certificate
        certificate = await pdf_service._load_certificate(
            session=db_session,
            certificate_id=cert_id,
            user_id=owner_id,
        )
        assert certificate is not None
        assert certificate.owner_id == owner_id


class TestSealLoading:
    """Tests for seal image loading."""

    async def test_load_nonexistent_seal(
        self,
        pdf_service: PDFSigningService,
        db_session: AsyncSession,
    ) -> None:
        """Test loading a non-existent seal."""
        with pytest.raises(SealNotFoundError):
            await pdf_service._load_seal_image(
                session=db_session,
                seal_id=uuid4(),
                user_id=1,
            )

    async def test_load_seal_wrong_owner(
        self,
        pdf_service: PDFSigningService,
        db_session: AsyncSession,
        seal_image: str,
    ) -> None:
        """Test loading a seal owned by another user."""
        with pytest.raises(SealNotFoundError, match="does not belong"):
            await pdf_service._load_seal_image(
                session=db_session,
                seal_id=seal_image,
                user_id=999,
            )

    async def test_load_valid_seal(
        self,
        pdf_service: PDFSigningService,
        db_session: AsyncSession,
        seal_image: str,
    ) -> None:
        """Test loading a valid seal image."""
        image_data = await pdf_service._load_seal_image(
            session=db_session,
            seal_id=seal_image,
            user_id=1,
        )
        assert image_data is not None
        assert image_data.startswith(b"\x89PNG")


class TestPDFSigning:
    """Tests for PDF signing operations."""

    async def test_sign_pdf_invisible(
        self,
        pdf_service: PDFSigningService,
        db_session: AsyncSession,
        user_certificate: tuple[str, int],
    ) -> None:
        """Test signing a PDF with an invisible signature."""
        cert_id, owner_id = user_certificate
        pdf_data = create_minimal_pdf()

        result = await pdf_service.sign_pdf(
            session=db_session,
            pdf_data=pdf_data,
            certificate_id=cert_id,
            user_id=owner_id,
            visibility=SignatureVisibility.INVISIBLE,
        )

        assert result.signed_pdf is not None
        assert len(result.signed_pdf) > len(pdf_data)
        assert result.certificate_id == cert_id
        assert result.visibility == SignatureVisibility.INVISIBLE
        assert result.file_size == len(result.signed_pdf)

        reader = PdfReader(io.BytesIO(result.signed_pdf))
        assert len(reader.pages) == 1

    async def test_sign_pdf_visible(
        self,
        pdf_service: PDFSigningService,
        db_session: AsyncSession,
        user_certificate: tuple[str, int],
    ) -> None:
        """Test signing a PDF with a visible signature."""
        cert_id, owner_id = user_certificate
        pdf_data = create_minimal_pdf()

        coordinates = SignatureCoordinates(
            page=1,
            x=100,
            y=100,
            width=200,
            height=50,
        )

        result = await pdf_service.sign_pdf(
            session=db_session,
            pdf_data=pdf_data,
            certificate_id=cert_id,
            user_id=owner_id,
            visibility=SignatureVisibility.VISIBLE,
            coordinates=coordinates,
        )

        assert result.signed_pdf is not None
        assert result.visibility == SignatureVisibility.VISIBLE

    async def test_sign_pdf_with_seal(
        self,
        pdf_service: PDFSigningService,
        db_session: AsyncSession,
        user_certificate: tuple[str, int],
        seal_image: str,
    ) -> None:
        """Test signing a PDF with a seal image."""
        cert_id, owner_id = user_certificate
        pdf_data = create_minimal_pdf()

        coordinates = SignatureCoordinates(
            page=1,
            x=100,
            y=100,
            width=200,
            height=50,
        )

        result = await pdf_service.sign_pdf(
            session=db_session,
            pdf_data=pdf_data,
            certificate_id=cert_id,
            user_id=owner_id,
            seal_id=seal_image,
            visibility=SignatureVisibility.VISIBLE,
            coordinates=coordinates,
        )

        assert result.signed_pdf is not None
        assert result.seal_id == seal_image

    async def test_sign_pdf_with_metadata(
        self,
        pdf_service: PDFSigningService,
        db_session: AsyncSession,
        user_certificate: tuple[str, int],
    ) -> None:
        """Test signing a PDF with metadata."""
        cert_id, owner_id = user_certificate
        pdf_data = create_minimal_pdf()

        metadata = SignatureMetadata(
            reason="Testing",
            location="Test Lab",
            contact_info="test@example.com",
        )

        result = await pdf_service.sign_pdf(
            session=db_session,
            pdf_data=pdf_data,
            certificate_id=cert_id,
            user_id=owner_id,
            metadata=metadata,
        )

        assert result.signed_pdf is not None


class TestPDFVerification:
    """Tests for PDF signature verification."""

    async def test_verify_signed_pdf(
        self,
        pdf_service: PDFSigningService,
        verification_service: PDFVerificationService,
        db_session: AsyncSession,
        user_certificate: tuple[str, int],
    ) -> None:
        """Ensure successfully signed PDFs validate correctly."""

        cert_id, owner_id = user_certificate
        pdf_data = create_minimal_pdf()

        sign_result = await pdf_service.sign_pdf(
            session=db_session,
            pdf_data=pdf_data,
            certificate_id=cert_id,
            user_id=owner_id,
            visibility=SignatureVisibility.INVISIBLE,
        )

        report = await verification_service.verify_pdf(
            session=db_session, pdf_data=sign_result.signed_pdf
        )

        assert report.total_signatures == 1
        assert report.valid_signatures == 1
        assert report.trusted_signatures == 1
        signature = report.signatures[0]
        assert signature.valid is True
        assert signature.trusted is True
        assert signature.error is None

    async def test_verify_pdf_without_signature(
        self,
        verification_service: PDFVerificationService,
        db_session: AsyncSession,
    ) -> None:
        """Ensure unsigned PDFs raise validation errors."""

        pdf_data = create_minimal_pdf()

        with pytest.raises(PDFVerificationInputError, match="signature"):
            await verification_service.verify_pdf(session=db_session, pdf_data=pdf_data)


class TestBatchSigning:
    """Tests for batch PDF signing operations."""

    async def test_batch_sign_multiple_pdfs(
        self,
        pdf_service: PDFSigningService,
        db_session: AsyncSession,
        user_certificate: tuple[str, int],
    ) -> None:
        """Test batch signing multiple PDFs."""
        cert_id, owner_id = user_certificate

        pdfs = [
            ("doc1.pdf", create_minimal_pdf()),
            ("doc2.pdf", create_minimal_pdf()),
            ("doc3.pdf", create_multipage_pdf(2)),
        ]

        results = await pdf_service.batch_sign_pdfs(
            session=db_session,
            pdfs=pdfs,
            certificate_id=cert_id,
            user_id=owner_id,
        )

        assert len(results) == 3
        for result in results:
            assert not isinstance(result, Exception)

    async def test_batch_sign_with_failures(
        self,
        pdf_service: PDFSigningService,
        db_session: AsyncSession,
        user_certificate: tuple[str, int],
    ) -> None:
        """Test batch signing with some invalid PDFs."""
        cert_id, owner_id = user_certificate

        pdfs = [
            ("valid.pdf", create_minimal_pdf()),
            ("invalid.pdf", b"Not a PDF"),
            ("valid2.pdf", create_minimal_pdf()),
        ]

        results = await pdf_service.batch_sign_pdfs(
            session=db_session,
            pdfs=pdfs,
            certificate_id=cert_id,
            user_id=owner_id,
        )

        assert len(results) == 3
        assert not isinstance(results[0], Exception)
        assert isinstance(results[1], Exception)
        assert not isinstance(results[2], Exception)

    async def test_batch_sign_exceeds_limit(
        self,
        pdf_service: PDFSigningService,
        db_session: AsyncSession,
        user_certificate: tuple[str, int],
    ) -> None:
        """Test that batch signing enforces size limits."""
        cert_id, owner_id = user_certificate

        pdfs = [(f"doc{i}.pdf", create_minimal_pdf()) for i in range(20)]

        with pytest.raises(PDFValidationError, match="exceeds maximum"):
            await pdf_service.batch_sign_pdfs(
                session=db_session,
                pdfs=pdfs,
                certificate_id=cert_id,
                user_id=owner_id,
            )


class TestAPIEndpoints:
    """Tests for PDF signing API endpoints."""

    async def test_sign_pdf_endpoint_unauthenticated(self, client: AsyncClient) -> None:
        """Test that unauthenticated requests are rejected."""
        pdf_data = create_minimal_pdf()

        response = await client.post(
            "/api/v1/pdf/sign",
            files={"pdf_file": ("test.pdf", pdf_data, "application/pdf")},
            data={"certificate_id": str(uuid4())},
        )

        assert response.status_code == 401

    async def test_sign_pdf_endpoint_invalid_content_type(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_certificate: tuple[str, int],
    ) -> None:
        """Test that invalid content types are rejected."""
        from app.core.security import create_token

        cert_id, _ = user_certificate
        token = create_token(subject=str(1), token_type="access")

        response = await client.post(
            "/api/v1/pdf/sign",
            headers={"Authorization": f"Bearer {token}"},
            files={"pdf_file": ("test.txt", b"Not a PDF", "text/plain")},
            data={"certificate_id": cert_id},
        )

        assert response.status_code == 400

    async def test_batch_sign_endpoint_unauthenticated(self, client: AsyncClient) -> None:
        """Test that unauthenticated batch requests are rejected."""
        pdf_data = create_minimal_pdf()

        response = await client.post(
            "/api/v1/pdf/sign/batch",
            files=[("pdf_files", ("test.pdf", pdf_data, "application/pdf"))],
            data={"certificate_id": str(uuid4())},
        )

        assert response.status_code == 401
