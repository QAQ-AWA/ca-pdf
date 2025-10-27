from __future__ import annotations

import hashlib
import os
from typing import Iterable
from uuid import UUID, uuid4

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import StorageEncryptionAlgorithm, settings
from app.crud import audit_log as audit_log_crud
from app.models.storage import EncryptedSecret, FileMetadata


class StorageError(Exception):
    """Base error raised by the encrypted storage service."""


class StorageValidationError(StorageError):
    """Raised when input payloads fail validation requirements."""


class StorageNotFoundError(StorageError):
    """Raised when attempting to access a non-existent storage record."""


class StorageCorruptionError(StorageError):
    """Raised when the stored payload cannot be decrypted with the active key."""


class EncryptedStorageService:
    """Provides encrypted-at-rest storage for sensitive binary assets."""

    def __init__(self) -> None:
        self._algorithm = settings.encrypted_storage_algorithm
        self._master_key = settings.storage_master_key_bytes()
        self._private_key_max_bytes = settings.private_key_max_bytes
        self._seal_image_max_bytes = settings.seal_image_max_bytes
        self._allowed_image_content_types = {
            content_type.lower() for content_type in settings.seal_image_allowed_content_types
        }

        if self._algorithm is StorageEncryptionAlgorithm.FERNET:
            self._fernet = Fernet(self._master_key)
            self._aesgcm = None
        else:
            self._fernet = None
            self._aesgcm = AESGCM(self._master_key)

    async def store_private_key(
        self,
        session: AsyncSession,
        *,
        pem: str,
        owner_id: int | None,
        filename: str | None = None,
    ) -> tuple[FileMetadata, EncryptedSecret]:
        payload = pem.encode("utf-8")
        self._validate_private_key(payload)
        return await self._store_binary(
            session=session,
            owner_id=owner_id,
            filename=filename or f"private-key-{uuid4().hex}.pem",
            content_type="application/x-pem-file",
            data=payload,
        )

    async def store_certificate_pem(
        self,
        session: AsyncSession,
        *,
        pem: str,
        owner_id: int | None,
        filename: str | None = None,
    ) -> tuple[FileMetadata, EncryptedSecret]:
        payload = pem.strip().encode("utf-8")
        return await self._store_binary(
            session=session,
            owner_id=owner_id,
            filename=filename or f"certificate-{uuid4().hex}.pem",
            content_type="application/x-pem-file",
            data=payload,
        )

    async def store_seal_image(
        self,
        session: AsyncSession,
        *,
        data: bytes,
        content_type: str,
        owner_id: int | None,
        filename: str | None = None,
        audit_actor_id: int | None = None,
    ) -> tuple[FileMetadata, EncryptedSecret]:
        normalized_type = content_type.lower().strip()
        self._validate_seal_image(data, normalized_type)
        file_metadata, secret = await self._store_binary(
            session=session,
            owner_id=owner_id,
            filename=filename or f"seal-{uuid4().hex}",
            content_type=normalized_type,
            data=data,
        )
        if audit_actor_id is not None:
            await audit_log_crud.create_audit_log(
                session=session,
                actor_id=audit_actor_id,
                event_type="seal.uploaded",
                resource="seal",
                metadata={
                    "file_id": str(file_metadata.id),
                    "secret_id": str(secret.id),
                    "content_type": normalized_type,
                    "size_bytes": file_metadata.size_bytes,
                    "owner_id": owner_id,
                    "filename": file_metadata.filename,
                },
                commit=True,
            )
        return file_metadata, secret

    async def store_encrypted_asset(
        self,
        session: AsyncSession,
        *,
        data: bytes,
        content_type: str,
        owner_id: int | None,
        filename: str | None = None,
    ) -> tuple[FileMetadata, EncryptedSecret]:
        normalized_type = content_type.lower().strip()
        return await self._store_binary(
            session=session,
            owner_id=owner_id,
            filename=filename or f"asset-{uuid4().hex}",
            content_type=normalized_type,
            data=data,
        )

    async def retrieve_secret(self, session: AsyncSession, secret_id: UUID) -> bytes:
        secret = await session.get(EncryptedSecret, secret_id)
        if secret is None:
            raise StorageNotFoundError(f"Encrypted secret {secret_id} was not found")
        return self._decrypt_secret(secret)

    async def delete_file(self, session: AsyncSession, file_id: UUID) -> None:
        file_metadata = await session.get(FileMetadata, file_id)
        if file_metadata is None:
            return
        await session.delete(file_metadata)
        await session.commit()

    async def load_private_key(self, session: AsyncSession, secret_id: UUID) -> str:
        payload = await self.retrieve_secret(session, secret_id)
        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise StorageCorruptionError("Stored private key payload is not valid UTF-8") from exc

    async def load_file_bytes(self, session: AsyncSession, file_id: UUID) -> bytes:
        file_metadata = await session.get(FileMetadata, file_id)
        if file_metadata is None:
            raise StorageNotFoundError(f"File metadata {file_id} was not found")
        secret = file_metadata.encrypted_payload
        if secret is None:
            raise StorageCorruptionError("Stored file is missing encrypted payload")
        return await self.retrieve_secret(session, secret.id)

    async def load_certificate_pem(self, session: AsyncSession, file_id: UUID) -> str:
        payload = await self.load_file_bytes(session, file_id)
        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise StorageCorruptionError("Stored certificate payload is not valid UTF-8") from exc

    async def load_seal_image(self, session: AsyncSession, secret_id: UUID) -> bytes:
        return await self.retrieve_secret(session, secret_id)

    async def _store_binary(
        self,
        *,
        session: AsyncSession,
        owner_id: int | None,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> tuple[FileMetadata, EncryptedSecret]:
        checksum = hashlib.sha256(data).hexdigest()
        file_metadata = FileMetadata(
            owner_id=owner_id,
            filename=filename,
            content_type=content_type,
            size_bytes=len(data),
            checksum=checksum,
            storage_backend="encrypted-db",
        )
        session.add(file_metadata)
        await session.flush()

        ciphertext, nonce, tag = self._encrypt_payload(data)

        secret = EncryptedSecret(
            file_id=file_metadata.id,
            algorithm=self._algorithm.value,
            key_version=1,
            nonce=nonce,
            tag=tag,
            ciphertext=ciphertext,
        )
        session.add(secret)
        await session.commit()
        await session.refresh(file_metadata)
        await session.refresh(secret)
        return file_metadata, secret

    def _encrypt_payload(self, data: bytes) -> tuple[bytes, bytes | None, bytes | None]:
        if self._algorithm is StorageEncryptionAlgorithm.FERNET:
            assert self._fernet is not None  # For type checkers
            token = self._fernet.encrypt(data)
            return token, None, None

        assert self._aesgcm is not None  # For type checkers
        nonce = os.urandom(12)
        encrypted = self._aesgcm.encrypt(nonce, data, associated_data=None)
        ciphertext, tag = encrypted[:-16], encrypted[-16:]
        return ciphertext, nonce, tag

    def _decrypt_secret(self, secret: EncryptedSecret) -> bytes:
        try:
            algorithm = StorageEncryptionAlgorithm(secret.algorithm)
        except ValueError as exc:  # pragma: no cover - defensive branch
            raise StorageCorruptionError("Unknown encryption algorithm") from exc

        if algorithm is StorageEncryptionAlgorithm.FERNET:
            if self._fernet is None:
                raise StorageCorruptionError("Fernet master key is unavailable")
            try:
                return self._fernet.decrypt(secret.ciphertext)
            except InvalidToken as exc:
                raise StorageCorruptionError("Unable to decrypt payload with Fernet key") from exc

        if secret.nonce is None or secret.tag is None:
            raise StorageCorruptionError("AES-GCM secret is missing nonce or authentication tag")
        if self._aesgcm is None:
            raise StorageCorruptionError("AES-GCM master key is unavailable")
        combined = secret.ciphertext + secret.tag
        try:
            return self._aesgcm.decrypt(secret.nonce, combined, associated_data=None)
        except Exception as exc:  # pragma: no cover - defensive branch
            raise StorageCorruptionError("Unable to decrypt payload with AES-GCM key") from exc

    def _validate_private_key(self, payload: bytes) -> None:
        if len(payload) > self._private_key_max_bytes:
            raise StorageValidationError("Private key exceeds configured size limit")
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise StorageValidationError("Private key must be valid UTF-8 text") from exc
        normalized = text.strip()
        if not (normalized.startswith("-----BEGIN") and normalized.endswith("END PRIVATE KEY-----")):
            raise StorageValidationError("Private key must be PEM encoded")

    def _validate_seal_image(self, payload: bytes, content_type: str) -> None:
        if len(payload) > self._seal_image_max_bytes:
            raise StorageValidationError("Seal image exceeds configured size limit")
        if content_type not in self._allowed_image_content_types:
            allowed = ", ".join(sorted(self._allowed_image_content_types)) or "none"
            raise StorageValidationError(f"Seal image content type '{content_type}' is not allowed (allowed: {allowed})")
        if content_type == "image/png" and not payload.startswith(b"\x89PNG\r\n\x1a\n"):
            raise StorageValidationError("PNG signature mismatch")
        if content_type == "image/svg+xml":
            try:
                text = payload.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise StorageValidationError("SVG content must be UTF-8 text") from exc
            if "<svg" not in text.lower():
                raise StorageValidationError("SVG payload is missing <svg> root element")

    @staticmethod
    def allowed_image_types() -> Iterable[str]:
        return tuple(settings.seal_image_allowed_content_types)
