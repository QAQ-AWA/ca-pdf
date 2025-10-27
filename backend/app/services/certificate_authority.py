"""Domain services for private certificate authority operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Sequence
from uuid import UUID, uuid4

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import audit_log as audit_log_crud
from app.crud import ca_artifact as ca_artifact_crud
from app.crud import certificate as certificate_crud
from app.models.ca_artifact import CAArtifact, CAArtifactType
from app.models.certificate import Certificate, CertificateStatus
from app.services.storage import EncryptedStorageService, StorageError

RootPrivateKey = rsa.RSAPrivateKey | ec.EllipticCurvePrivateKey
LeafPrivateKey = rsa.RSAPrivateKey | ec.EllipticCurvePrivateKey


class CertificateAuthorityError(Exception):
    """Base error for certificate authority operations."""


class RootCAAlreadyExistsError(CertificateAuthorityError):
    """Raised when attempting to generate a root CA while one already exists."""


class RootCANotFoundError(CertificateAuthorityError):
    """Raised when root CA material is requested but not available."""


class CertificateIssuanceError(CertificateAuthorityError):
    """Raised when a certificate cannot be issued."""


class CertificateImportError(CertificateAuthorityError):
    """Raised when an external certificate bundle cannot be imported."""


class CertificateRevocationError(CertificateAuthorityError):
    """Raised when revocation cannot be performed."""


class CRLGenerationError(CertificateAuthorityError):
    """Raised when a certificate revocation list cannot be generated."""


class RootKeyAlgorithm(str, Enum):
    """Supported private key algorithms for the root certificate authority."""

    RSA_4096 = "rsa-4096"
    EC_P256 = "ec-p256"


class LeafKeyAlgorithm(str, Enum):
    """Supported private key algorithms for issued leaf certificates."""

    RSA_2048 = "rsa-2048"
    EC_P256 = "ec-p256"


@dataclass(slots=True)
class RootCAResult:
    """Material returned after generating a root certificate authority."""

    artifact: CAArtifact
    certificate: x509.Certificate
    certificate_pem: str
    algorithm: RootKeyAlgorithm


@dataclass(slots=True)
class IssuedCertificateResult:
    """Material describing an issued certificate."""

    certificate: Certificate
    certificate_pem: str
    p12_bytes: bytes
    passphrase: str | None


@dataclass(slots=True)
class ImportedCertificateResult:
    """Result returned after importing an external certificate."""

    certificate: Certificate
    certificate_pem: str


@dataclass(slots=True)
class CRLResult:
    """Information about a generated certificate revocation list."""

    artifact: CAArtifact
    crl_pem: str
    revoked_serials: Sequence[str]


@dataclass(slots=True)
class RootMaterial:
    """Loaded root CA material used for signing operations."""

    artifact: CAArtifact
    certificate: x509.Certificate
    private_key: RootPrivateKey


class CertificateAuthorityService:
    """High level operations for managing the private certificate authority."""

    def __init__(self, storage_service: EncryptedStorageService | None = None) -> None:
        self._storage = storage_service or EncryptedStorageService()

    async def generate_root_ca(
        self,
        *,
        session: AsyncSession,
        algorithm: RootKeyAlgorithm,
        common_name: str,
        organization: str | None,
        actor_id: int | None,
        validity_days: int = 3650,
    ) -> RootCAResult:
        """Generate a new self-signed root certificate authority."""

        if validity_days <= 0:
            raise CertificateAuthorityError("Root CA validity period must be positive")

        existing = await ca_artifact_crud.get_latest_artifact_by_type(
            session=session,
            artifact_type=CAArtifactType.ROOT_CERTIFICATE,
        )
        if existing is not None:
            raise RootCAAlreadyExistsError("A root certificate authority is already present")

        private_key = self._generate_root_private_key(algorithm)
        now = datetime.now(timezone.utc)
        serial_number = x509.random_serial_number()

        subject_attributes = [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
        if organization:
            subject_attributes.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization))
        subject = x509.Name(subject_attributes)

        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(private_key.public_key())
            .serial_number(serial_number)
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=validity_days))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=False,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()), critical=False
            )
        )
        builder = builder.add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(private_key.public_key()),
            critical=False,
        )
        certificate = builder.sign(private_key=private_key, algorithm=hashes.SHA256())

        certificate_pem = certificate.public_bytes(serialization.Encoding.PEM).decode("utf-8")
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        cert_filename = f"root-ca-{uuid4().hex}.pem"
        key_filename = f"root-ca-key-{uuid4().hex}.pem"

        cert_file, _ = await self._storage.store_certificate_pem(
            session=session,
            pem=certificate_pem,
            owner_id=actor_id,
            filename=cert_filename,
        )
        _, private_key_secret = await self._storage.store_private_key(
            session=session,
            pem=private_key_pem,
            owner_id=actor_id,
            filename=key_filename,
        )

        serial_hex = f"{serial_number:x}".upper()
        artifact = await ca_artifact_crud.create_artifact(
            session=session,
            name=f"root-ca-{serial_hex}",
            artifact_type=CAArtifactType.ROOT_CERTIFICATE,
            description=f"Root CA generated with {algorithm.value}",
            file_id=cert_file.id,
            secret_id=private_key_secret.id,
            commit=False,
        )

        await audit_log_crud.create_audit_log(
            session=session,
            actor_id=actor_id,
            event_type="ca.root.created",
            resource="root-ca",
            metadata={
                "artifact_id": str(artifact.id),
                "algorithm": algorithm.value,
                "serial_number": serial_hex,
            },
        )
        await session.commit()
        await session.refresh(artifact)

        return RootCAResult(
            artifact=artifact,
            certificate=certificate,
            certificate_pem=certificate_pem,
            algorithm=algorithm,
        )

    async def export_root_certificate(self, *, session: AsyncSession) -> str:
        """Return the PEM encoded root certificate."""

        root_material = await self._load_root_material(session=session)
        return root_material.certificate.public_bytes(serialization.Encoding.PEM).decode("utf-8")

    async def issue_certificate(
        self,
        *,
        session: AsyncSession,
        owner_id: int,
        common_name: str,
        organization: str | None,
        algorithm: LeafKeyAlgorithm,
        actor_id: int | None,
        validity_days: int = 365,
        p12_passphrase: str | None = None,
    ) -> IssuedCertificateResult:
        """Issue a new end-entity certificate for a user."""

        if validity_days <= 0:
            raise CertificateIssuanceError("Certificate validity must be positive")

        root_material = await self._load_root_material(session=session)
        leaf_private_key = self._generate_leaf_private_key(algorithm)
        now = datetime.now(timezone.utc)
        serial_number = x509.random_serial_number()

        subject_attributes = [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
        if organization:
            subject_attributes.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization))
        subject = x509.Name(subject_attributes)

        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(root_material.certificate.subject)
            .public_key(leaf_private_key.public_key())
            .serial_number(serial_number)
            .not_valid_before(now - timedelta(minutes=1))
            .not_valid_after(now + timedelta(days=validity_days))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(leaf_private_key.public_key()),
                critical=False,
            )
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(
                    root_material.private_key.public_key()
                ),
                critical=False,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=algorithm is LeafKeyAlgorithm.RSA_2048,
                    data_encipherment=False,
                    key_agreement=algorithm is LeafKeyAlgorithm.EC_P256,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage(
                    [
                        ExtendedKeyUsageOID.CLIENT_AUTH,
                        ExtendedKeyUsageOID.SERVER_AUTH,
                    ]
                ),
                critical=False,
            )
        )

        certificate = builder.sign(private_key=root_material.private_key, algorithm=hashes.SHA256())
        certificate_pem = certificate.public_bytes(serialization.Encoding.PEM).decode("utf-8")
        private_key_pem = leaf_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        key_filename = f"cert-key-{uuid4().hex}.pem"
        bundle_filename = f"cert-{uuid4().hex}.p12"

        _, private_key_secret = await self._storage.store_private_key(
            session=session,
            pem=private_key_pem,
            owner_id=owner_id,
            filename=key_filename,
        )

        passphrase_bytes = p12_passphrase.encode("utf-8") if p12_passphrase else None
        if passphrase_bytes is not None:
            encryption_algorithm = serialization.BestAvailableEncryption(passphrase_bytes)
        else:
            encryption_algorithm = serialization.NoEncryption()

        p12_bytes = pkcs12.serialize_key_and_certificates(
            name=common_name.encode("utf-8"),
            key=leaf_private_key,
            cert=certificate,
            cas=[root_material.certificate],
            encryption_algorithm=encryption_algorithm,
        )
        bundle_file, _ = await self._storage.store_encrypted_asset(
            session=session,
            data=p12_bytes,
            content_type="application/x-pkcs12",
            owner_id=owner_id,
            filename=bundle_filename,
        )

        serial_hex = f"{serial_number:x}".upper()
        certificate_record = await certificate_crud.create_certificate(
            session=session,
            owner_id=owner_id,
            serial_number=serial_hex,
            subject_common_name=common_name,
            subject_organization=organization,
            issued_at=now,
            expires_at=self._ensure_utc(certificate.not_valid_after),
            certificate_pem=certificate_pem,
            certificate_file_id=bundle_file.id,
            private_key_secret_id=private_key_secret.id,
            commit=False,
        )

        await audit_log_crud.create_audit_log(
            session=session,
            actor_id=actor_id,
            event_type="ca.certificate.issued",
            resource="certificate",
            metadata={
                "certificate_id": str(certificate_record.id),
                "owner_id": owner_id,
                "serial_number": serial_hex,
                "algorithm": algorithm.value,
            },
        )
        await session.commit()
        await session.refresh(certificate_record)

        return IssuedCertificateResult(
            certificate=certificate_record,
            certificate_pem=certificate_pem,
            p12_bytes=p12_bytes,
            passphrase=p12_passphrase,
        )

    async def import_certificate_from_p12(
        self,
        *,
        session: AsyncSession,
        owner_id: int,
        bundle_bytes: bytes,
        passphrase: str | None,
        actor_id: int | None,
    ) -> ImportedCertificateResult:
        """Import an externally generated PKCS#12 bundle."""

        root_material = await self._load_root_material(session=session)

        try:
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                bundle_bytes,
                passphrase.encode("utf-8") if passphrase else None,
            )
        except ValueError as exc:  # Raised for invalid P12 structures or passphrases
            raise CertificateImportError("Unable to parse PKCS#12 bundle") from exc

        if certificate is None or private_key is None:
            raise CertificateImportError("PKCS#12 bundle is missing a certificate or private key")

        if certificate.issuer != root_material.certificate.subject:
            raise CertificateImportError(
                "Imported certificate is not signed by the managed root CA"
            )

        serial_hex = f"{certificate.serial_number:x}".upper()
        existing = await certificate_crud.get_certificate_by_serial(
            session=session, serial_number=serial_hex
        )
        if existing is not None:
            raise CertificateImportError("A certificate with this serial number already exists")

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        certificate_pem = certificate.public_bytes(serialization.Encoding.PEM).decode("utf-8")

        key_filename = f"cert-import-key-{uuid4().hex}.pem"
        bundle_filename = f"cert-import-{uuid4().hex}.p12"

        _, private_key_secret = await self._storage.store_private_key(
            session=session,
            pem=private_key_pem,
            owner_id=owner_id,
            filename=key_filename,
        )
        bundle_file, _ = await self._storage.store_encrypted_asset(
            session=session,
            data=bundle_bytes,
            content_type="application/x-pkcs12",
            owner_id=owner_id,
            filename=bundle_filename,
        )

        certificate_record = await certificate_crud.create_certificate(
            session=session,
            owner_id=owner_id,
            serial_number=serial_hex,
            subject_common_name=self._resolve_common_name(certificate),
            subject_organization=self._resolve_organization(certificate),
            issued_at=self._ensure_utc(certificate.not_valid_before),
            expires_at=self._ensure_utc(certificate.not_valid_after),
            certificate_pem=certificate_pem,
            certificate_file_id=bundle_file.id,
            private_key_secret_id=private_key_secret.id,
            commit=False,
        )

        await audit_log_crud.create_audit_log(
            session=session,
            actor_id=actor_id,
            event_type="ca.certificate.imported",
            resource="certificate",
            metadata={
                "certificate_id": str(certificate_record.id),
                "owner_id": owner_id,
                "serial_number": serial_hex,
                "additional_chain": len(additional_certs or []),
            },
        )
        await session.commit()
        await session.refresh(certificate_record)

        return ImportedCertificateResult(
            certificate=certificate_record, certificate_pem=certificate_pem
        )

    async def revoke_certificate(
        self,
        *,
        session: AsyncSession,
        certificate: Certificate,
        actor_id: int | None,
    ) -> Certificate:
        """Revoke a previously issued certificate."""

        if certificate.status == CertificateStatus.REVOKED.value:
            raise CertificateRevocationError("Certificate has already been revoked")
        if certificate.status == CertificateStatus.EXPIRED.value:
            raise CertificateRevocationError("Expired certificates cannot be revoked")

        certificate = await certificate_crud.mark_certificate_revoked(
            session=session,
            certificate=certificate,
            commit=False,
        )

        await audit_log_crud.create_audit_log(
            session=session,
            actor_id=actor_id,
            event_type="ca.certificate.revoked",
            resource="certificate",
            metadata={
                "certificate_id": str(certificate.id),
                "serial_number": certificate.serial_number,
            },
        )
        await session.commit()
        await session.refresh(certificate)
        return certificate

    async def generate_crl(
        self,
        *,
        session: AsyncSession,
        actor_id: int | None,
        next_update_days: int = 7,
    ) -> CRLResult:
        """Generate a certificate revocation list signed by the root CA."""

        if next_update_days <= 0:
            raise CRLGenerationError("CRL next update interval must be positive")

        root_material = await self._load_root_material(session=session)
        revoked_certificates = await certificate_crud.list_revoked_certificates(session=session)
        now = datetime.now(timezone.utc)

        builder = (
            x509.CertificateRevocationListBuilder()
            .issuer_name(root_material.certificate.subject)
            .last_update(now)
            .next_update(now + timedelta(days=next_update_days))
        )

        revoked_serials: list[str] = []
        for revoked in revoked_certificates:
            try:
                serial_int = int(revoked.serial_number, 16)
            except ValueError as exc:
                raise CRLGenerationError("Stored certificate serial number is invalid") from exc
            revocation_source = revoked.updated_at or now
            revocation_date = self._ensure_utc(revocation_source)
            revoked_entry = (
                x509.RevokedCertificateBuilder()
                .serial_number(serial_int)
                .revocation_date(revocation_date)
                .build()
            )
            builder = builder.add_revoked_certificate(revoked_entry)
            revoked_serials.append(revoked.serial_number)

        crl = builder.sign(private_key=root_material.private_key, algorithm=hashes.SHA256())
        crl_pem = crl.public_bytes(serialization.Encoding.PEM).decode("utf-8")

        filename = f"crl-{now.strftime('%Y%m%d%H%M%S')}.pem"
        crl_file, _ = await self._storage.store_encrypted_asset(
            session=session,
            data=crl_pem.encode("utf-8"),
            content_type="application/pkix-crl",
            owner_id=actor_id,
            filename=filename,
        )

        artifact = await ca_artifact_crud.create_artifact(
            session=session,
            name=f"crl-{uuid4().hex}",
            artifact_type=CAArtifactType.CRL,
            description="Certificate revocation list",
            file_id=crl_file.id,
            commit=False,
        )

        await audit_log_crud.create_audit_log(
            session=session,
            actor_id=actor_id,
            event_type="ca.crl.generated",
            resource="crl",
            metadata={
                "artifact_id": str(artifact.id),
                "revoked_serials": revoked_serials,
            },
        )
        await session.commit()
        await session.refresh(artifact)

        return CRLResult(artifact=artifact, crl_pem=crl_pem, revoked_serials=revoked_serials)

    async def list_crls(self, *, session: AsyncSession) -> Sequence[CAArtifact]:
        """Return CRL artifacts ordered from newest to oldest."""

        return await ca_artifact_crud.list_artifacts(
            session=session,
            artifact_type=CAArtifactType.CRL,
        )

    async def load_crl_pem(self, *, session: AsyncSession, artifact_id: UUID) -> str:
        """Load the PEM encoded CRL for the supplied artifact."""

        artifact = await ca_artifact_crud.get_artifact_by_id(
            session=session, artifact_id=artifact_id
        )
        if artifact is None or artifact.file_id is None:
            raise CRLGenerationError("CRL artifact was not found")
        payload = await self._storage.load_certificate_pem(
            session=session, file_id=artifact.file_id
        )
        return payload

    async def load_certificate_bundle(
        self, *, session: AsyncSession, certificate: Certificate
    ) -> bytes:
        """Return the stored PKCS#12 bundle for a certificate."""

        if certificate.certificate_file_id is None:
            raise CertificateAuthorityError("Certificate bundle is not stored")
        return await self._storage.load_file_bytes(
            session=session, file_id=certificate.certificate_file_id
        )

    async def _load_root_material(self, *, session: AsyncSession) -> RootMaterial:
        artifact = await ca_artifact_crud.get_latest_artifact_by_type(
            session=session,
            artifact_type=CAArtifactType.ROOT_CERTIFICATE,
        )
        if artifact is None:
            raise RootCANotFoundError("Root certificate authority has not been generated")
        if artifact.file_id is None or artifact.secret_id is None:
            raise CertificateAuthorityError("Root CA artifact is missing stored material")

        try:
            certificate_pem = await self._storage.load_certificate_pem(
                session=session, file_id=artifact.file_id
            )
            private_key_pem = await self._storage.load_private_key(
                session=session, secret_id=artifact.secret_id
            )
        except StorageError as exc:
            raise CertificateAuthorityError("Unable to load root CA material") from exc

        try:
            certificate = x509.load_pem_x509_certificate(certificate_pem.encode("utf-8"))
        except ValueError as exc:
            raise CertificateAuthorityError("Stored root certificate is invalid") from exc

        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode("utf-8"), password=None
            )
        except ValueError as exc:
            raise CertificateAuthorityError("Stored root private key is invalid") from exc

        return RootMaterial(
            artifact=artifact,
            certificate=certificate,
            private_key=private_key,
        )

    @staticmethod
    def _ensure_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _generate_root_private_key(algorithm: RootKeyAlgorithm) -> RootPrivateKey:
        if algorithm is RootKeyAlgorithm.RSA_4096:
            return rsa.generate_private_key(public_exponent=65537, key_size=4096)
        if algorithm is RootKeyAlgorithm.EC_P256:
            return ec.generate_private_key(ec.SECP256R1())
        raise CertificateAuthorityError(f"Unsupported root key algorithm: {algorithm}")

    @staticmethod
    def _generate_leaf_private_key(algorithm: LeafKeyAlgorithm) -> LeafPrivateKey:
        if algorithm is LeafKeyAlgorithm.RSA_2048:
            return rsa.generate_private_key(public_exponent=65537, key_size=2048)
        if algorithm is LeafKeyAlgorithm.EC_P256:
            return ec.generate_private_key(ec.SECP256R1())
        raise CertificateAuthorityError(f"Unsupported leaf key algorithm: {algorithm}")

    @staticmethod
    def _resolve_common_name(certificate: x509.Certificate) -> str:
        attributes = certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        if not attributes:
            return certificate.subject.rfc4514_string()
        return attributes[0].value

    @staticmethod
    def _resolve_organization(certificate: x509.Certificate) -> str | None:
        attributes = certificate.subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
        if not attributes:
            return None
        return attributes[0].value
