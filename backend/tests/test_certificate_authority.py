"""Integration tests for the certificate authority endpoints."""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from httpx import AsyncClient

from app.core.config import settings
from app.crud import ca_artifact as ca_artifact_crud
from app.crud import certificate as certificate_crud
from app.crud.user import create_user
from app.db.session import get_session_factory
from app.models.ca_artifact import CAArtifactType
from app.models.certificate import CertificateStatus
from app.models.user import User, UserRole
from app.services.storage import EncryptedStorageService

LOGIN_URL = f"{settings.api_v1_prefix}/auth/login"
ROOT_URL = f"{settings.api_v1_prefix}/ca/root"
ROOT_CERT_URL = f"{settings.api_v1_prefix}/ca/root/certificate"
CERT_ISSUE_URL = f"{settings.api_v1_prefix}/ca/certificates/issue"
CERT_IMPORT_URL = f"{settings.api_v1_prefix}/ca/certificates/import"
CERT_LIST_URL = f"{settings.api_v1_prefix}/ca/certificates"
CERT_REVOKE_URL = f"{settings.api_v1_prefix}/ca/certificates/{{certificate_id}}/revoke"
CRL_GENERATE_URL = f"{settings.api_v1_prefix}/ca/crl"
CRL_LIST_URL = f"{settings.api_v1_prefix}/ca/crl"
CRL_DOWNLOAD_URL = f"{settings.api_v1_prefix}/ca/crl/{{artifact_id}}"

ADMIN_EMAIL = settings.admin_email or "admin@example.com"
ADMIN_PASSWORD = settings.admin_password or "AdminPass123!"


@pytest.mark.anyio
async def test_generate_root_ca_and_export(client: AsyncClient) -> None:
    admin_token = await _login(client=client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)

    response = await client.post(
        ROOT_URL,
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"common_name": "Test Root CA", "algorithm": "rsa-4096", "validity_days": 3650},
    )
    assert response.status_code == 201
    data = response.json()
    assert UUID(data["artifact_id"]) is not None
    assert data["algorithm"] == "rsa-4096"
    assert data["subject"].startswith("CN=Test Root CA")

    certificate_response = await client.get(ROOT_CERT_URL)
    assert certificate_response.status_code == 200
    certificate_pem = certificate_response.json()["certificate_pem"]
    assert "BEGIN CERTIFICATE" in certificate_pem

    duplicate_response = await client.post(
        ROOT_URL,
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"common_name": "Another Root", "algorithm": "ec-p256"},
    )
    assert duplicate_response.status_code == 409


@pytest.mark.anyio
async def test_issue_certificate_returns_valid_pkcs12_bundle(client: AsyncClient) -> None:
    admin_token = await _login(client=client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
    await _ensure_root(client=client, admin_token=admin_token)

    user_email = "user1@example.com"
    user_password = "UserPassword123!"
    user = await _create_user(email=user_email, password=user_password, role=UserRole.USER)
    user_token = await _login(client=client, email=user_email, password=user_password)

    issue_response = await client.post(
        CERT_ISSUE_URL,
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "common_name": "User One",
            "organization": "Example Org",
            "algorithm": "rsa-2048",
            "p12_passphrase": "bundle-pass",
        },
    )
    assert issue_response.status_code == 200
    payload = issue_response.json()
    assert payload["status"] == CertificateStatus.ACTIVE.value

    bundle_bytes = base64.b64decode(payload["p12_bundle"])
    key, certificate, chain = pkcs12.load_key_and_certificates(bundle_bytes, b"bundle-pass")
    assert key is not None
    assert certificate is not None
    assert chain and isinstance(chain[0], x509.Certificate)
    assert certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value == "User One"

    session_factory = get_session_factory()
    async with session_factory() as session:
        stored = await certificate_crud.get_certificate_by_serial(
            session=session, serial_number=payload["serial_number"]
        )
    assert stored is not None
    assert stored.owner_id == user.id


@pytest.mark.anyio
async def test_import_certificate_from_pkcs12_bundle(client: AsyncClient) -> None:
    admin_token = await _login(client=client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
    await _ensure_root(client=client, admin_token=admin_token)

    user_email = "import@example.com"
    user_password = "ImportPassword123!"
    await _create_user(email=user_email, password=user_password, role=UserRole.USER)
    user_token = await _login(client=client, email=user_email, password=user_password)

    bundle_bytes, serial_hex = await _build_external_pkcs12_bundle()

    import_response = await client.post(
        CERT_IMPORT_URL,
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "p12_bundle": base64.b64encode(bundle_bytes).decode("utf-8"),
            "passphrase": "import-pass",
        },
    )
    assert import_response.status_code == 200
    data = import_response.json()
    assert data["serial_number"].upper() == serial_hex
    assert data["status"] == CertificateStatus.ACTIVE.value

    session_factory = get_session_factory()
    async with session_factory() as session:
        imported = await certificate_crud.get_certificate_by_serial(
            session=session, serial_number=serial_hex
        )
    assert imported is not None

    list_response = await client.get(
        CERT_LIST_URL,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert list_response.status_code == 200
    listed_serials = {
        item["serial_number"].upper() for item in list_response.json()["certificates"]
    }
    assert serial_hex in listed_serials


@pytest.mark.anyio
async def test_revoke_certificate_and_generate_crl(client: AsyncClient) -> None:
    admin_token = await _login(client=client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
    await _ensure_root(client=client, admin_token=admin_token)

    user_email = "revoker@example.com"
    user_password = "RevokerPass123!"
    await _create_user(email=user_email, password=user_password, role=UserRole.USER)
    user_token = await _login(client=client, email=user_email, password=user_password)

    issue_response = await client.post(
        CERT_ISSUE_URL,
        headers={"Authorization": f"Bearer {user_token}"},
        json={"common_name": "Revoked Cert", "algorithm": "ec-p256"},
    )
    assert issue_response.status_code == 200
    certificate_data = issue_response.json()
    certificate_id = certificate_data["certificate_id"]
    serial_number = certificate_data["serial_number"].upper()

    revoke_response = await client.post(
        CERT_REVOKE_URL.format(certificate_id=certificate_id),
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == CertificateStatus.REVOKED.value

    session_factory = get_session_factory()
    async with session_factory() as session:
        revoked_record = await certificate_crud.get_certificate_by_serial(
            session=session, serial_number=serial_number
        )
    assert revoked_record is not None
    assert revoked_record.status == CertificateStatus.REVOKED.value

    crl_response = await client.post(
        CRL_GENERATE_URL,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert crl_response.status_code == 200
    crl_payload = crl_response.json()
    assert serial_number in {s.upper() for s in crl_payload["revoked_serials"]}

    list_response = await client.get(CRL_LIST_URL)
    assert list_response.status_code == 200
    crl_entries = list_response.json()["crls"]
    assert any(entry["artifact_id"] == crl_payload["artifact_id"] for entry in crl_entries)

    download_response = await client.get(
        CRL_DOWNLOAD_URL.format(artifact_id=crl_payload["artifact_id"])
    )
    assert download_response.status_code == 200
    crl = x509.load_pem_x509_crl(download_response.text.encode("utf-8"))
    revoked_serials = {f"{entry.serial_number:x}".upper() for entry in crl}
    assert serial_number in revoked_serials


async def _login(*, client: AsyncClient, email: str, password: str) -> str:
    response = await client.post(LOGIN_URL, json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


async def _ensure_root(*, client: AsyncClient, admin_token: str) -> None:
    response = await client.post(
        ROOT_URL,
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"common_name": "Test Root", "algorithm": "rsa-4096"},
    )
    if response.status_code not in {201, 409}:
        pytest.fail(f"Unexpected response creating root CA: {response.status_code} {response.text}")


async def _create_user(*, email: str, password: str, role: UserRole) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        return await create_user(session=session, email=email, password=password, role=role)


async def _build_external_pkcs12_bundle() -> tuple[bytes, str]:
    session_factory = get_session_factory()
    storage = EncryptedStorageService()

    async with session_factory() as session:
        artifact = await ca_artifact_crud.get_latest_artifact_by_type(
            session=session,
            artifact_type=CAArtifactType.ROOT_CERTIFICATE,
        )
        assert (
            artifact is not None and artifact.file_id is not None and artifact.secret_id is not None
        )
        root_cert_pem = await storage.load_certificate_pem(
            session=session, file_id=artifact.file_id
        )
        root_key_pem = await storage.load_private_key(session=session, secret_id=artifact.secret_id)

    root_certificate = x509.load_pem_x509_certificate(root_cert_pem.encode("utf-8"))
    root_private_key = serialization.load_pem_private_key(
        root_key_pem.encode("utf-8"), password=None
    )

    leaf_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    validity = now + timedelta(days=365)

    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Imported Certificate")])
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(root_certificate.subject)
        .public_key(leaf_private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(validity)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage(
                [ExtendedKeyUsageOID.CLIENT_AUTH, ExtendedKeyUsageOID.SERVER_AUTH]
            ),
            critical=False,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(leaf_private_key.public_key()), critical=False
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(root_private_key.public_key()),
            critical=False,
        )
    )

    certificate = builder.sign(private_key=root_private_key, algorithm=hashes.SHA256())
    serial_hex = f"{certificate.serial_number:x}".upper()

    p12_bytes = pkcs12.serialize_key_and_certificates(
        name=b"imported",
        key=leaf_private_key,
        cert=certificate,
        cas=[root_certificate],
        encryption_algorithm=serialization.BestAvailableEncryption(b"import-pass"),
    )

    return p12_bytes, serial_hex
