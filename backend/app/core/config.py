from __future__ import annotations

import base64
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

from cryptography.fernet import Fernet
from pydantic import EmailStr, Field, PrivateAttr, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class StorageEncryptionAlgorithm(str, Enum):
    """Supported algorithms for the encrypted storage layer."""

    FERNET = "fernet"
    AES_GCM = "aes-gcm"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        case_sensitive=False,
    )

    app_name: str = Field(default="Monorepo API", alias="APP_NAME")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    uvicorn_host: str = Field(default="0.0.0.0", alias="UVICORN_HOST")
    uvicorn_port: int = Field(default=8000, alias="UVICORN_PORT")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/backend",
        alias="DATABASE_URL",
    )
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")

    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_minutes: int = Field(default=60 * 24 * 3, alias="REFRESH_TOKEN_EXPIRE_MINUTES")

    backend_cors_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        alias="BACKEND_CORS_ORIGINS",
    )

    auth_rate_limit_requests: int = Field(default=5, alias="AUTH_RATE_LIMIT_REQUESTS")
    auth_rate_limit_window_seconds: int = Field(default=60, alias="AUTH_RATE_LIMIT_WINDOW_SECONDS")

    admin_email: EmailStr | None = Field(default=None, alias="ADMIN_EMAIL")
    admin_password: str | None = Field(default=None, alias="ADMIN_PASSWORD")
    admin_role: str = Field(default="admin", alias="ADMIN_ROLE")

    encrypted_storage_algorithm: StorageEncryptionAlgorithm = Field(
        default=StorageEncryptionAlgorithm.FERNET,
        alias="ENCRYPTED_STORAGE_ALGORITHM",
    )
    encrypted_storage_master_key: SecretStr | None = Field(
        default=None,
        alias="ENCRYPTED_STORAGE_MASTER_KEY",
    )
    encrypted_storage_master_key_path: Path | None = Field(
        default=None,
        alias="ENCRYPTED_STORAGE_MASTER_KEY_PATH",
    )
    private_key_max_bytes: int = Field(default=8192, alias="PRIVATE_KEY_MAX_BYTES")
    seal_image_max_bytes: int = Field(default=1024 * 1024, alias="SEAL_IMAGE_MAX_BYTES")
    seal_image_allowed_content_types: list[str] = Field(
        default_factory=lambda: ["image/png", "image/svg+xml"],
        alias="SEAL_IMAGE_ALLOWED_CONTENT_TYPES",
    )

    pdf_max_bytes: int = Field(default=50 * 1024 * 1024, alias="PDF_MAX_BYTES")
    pdf_allowed_content_types: list[str] = Field(
        default_factory=lambda: ["application/pdf"],
        alias="PDF_ALLOWED_CONTENT_TYPES",
    )
    pdf_batch_max_count: int = Field(default=10, alias="PDF_BATCH_MAX_COUNT")
    tsa_url: str | None = Field(default=None, alias="TSA_URL")
    tsa_username: str | None = Field(default=None, alias="TSA_USERNAME")
    tsa_password: SecretStr | None = Field(default=None, alias="TSA_PASSWORD")

    _master_key_bytes: bytes = PrivateAttr(default=b"")
    _raw_master_key: str = PrivateAttr(default="")

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def _assemble_cors_origins(cls, value: Any) -> list[str]:
        parsed = cls._normalize_sequence(value)
        return parsed or ["*"]

    @field_validator("seal_image_allowed_content_types", mode="before")
    @classmethod
    def _assemble_content_types(cls, value: Any) -> list[str]:
        parsed = cls._normalize_sequence(value)
        if not parsed:
            raise ValueError("At least one seal image content type must be configured")
        return parsed

    @field_validator("admin_role", mode="before")
    @classmethod
    def _normalize_admin_role(cls, value: str) -> str:
        return value.lower()

    @field_validator("database_url", mode="after")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        return cls._transform_database_driver(value, ensure_async=True)

    @field_validator("private_key_max_bytes", "seal_image_max_bytes", "pdf_max_bytes", "pdf_batch_max_count")
    @classmethod
    def _validate_positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Sizes must be positive integers")
        return value

    @field_validator("pdf_allowed_content_types", mode="before")
    @classmethod
    def _assemble_pdf_content_types(cls, value: Any) -> list[str]:
        parsed = cls._normalize_sequence(value)
        if not parsed:
            raise ValueError("At least one PDF content type must be configured")
        return parsed

    @model_validator(mode="after")
    def _resolve_master_key(self) -> Settings:
        raw_value: str | None = None
        if self.encrypted_storage_master_key is not None:
            candidate = self.encrypted_storage_master_key.get_secret_value().strip()
            if candidate:
                raw_value = candidate
        if self.encrypted_storage_master_key_path is not None:
            try:
                file_value = self.encrypted_storage_master_key_path.read_text(encoding="utf-8").strip()
            except FileNotFoundError as exc:
                raise ValueError(
                    f"Encrypted storage master key path does not exist: {self.encrypted_storage_master_key_path}",
                ) from exc
            if file_value:
                raw_value = file_value
        if not raw_value:
            raise ValueError(
                "Encrypted storage master key is not configured. Set ENCRYPTED_STORAGE_MASTER_KEY or "
                "ENCRYPTED_STORAGE_MASTER_KEY_PATH.",
            )

        self._raw_master_key = raw_value

        if self.encrypted_storage_algorithm is StorageEncryptionAlgorithm.FERNET:
            key_bytes = raw_value.encode("utf-8")
            try:
                Fernet(key_bytes)
            except Exception as exc:  # pragma: no cover - defensive validation branch
                raise ValueError("Invalid Fernet master key provided") from exc
            self._master_key_bytes = key_bytes
        else:
            try:
                decoded = base64.urlsafe_b64decode(raw_value)
            except Exception as exc:  # pragma: no cover - defensive validation branch
                raise ValueError("Invalid AES-GCM master key encoding; expected URL-safe base64") from exc
            if len(decoded) not in (16, 24, 32):
                raise ValueError("AES-GCM master key must be 128, 192, or 256 bits in length")
            self._master_key_bytes = decoded

        return self

    @property
    def async_database_url(self) -> str:
        """Return the database URL suitable for async SQLAlchemy engines."""

        return self.database_url

    @property
    def sync_database_url(self) -> str:
        """Return the database URL using a synchronous driver (for Alembic)."""

        return self._transform_database_driver(self.database_url, ensure_async=False)

    def storage_master_key_bytes(self) -> bytes:
        """Return the resolved encryption master key material."""

        return self._master_key_bytes

    def storage_master_key_raw(self) -> str:
        """Return the raw (pre-processed) master key string for diagnostics."""

        return self._raw_master_key

    @staticmethod
    def _normalize_sequence(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            if not value:
                return []
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, Sequence):
            return [str(item).strip() for item in value if str(item).strip()]
        raise ValueError("Invalid iterable configuration value")

    @staticmethod
    def _transform_database_driver(value: str, *, ensure_async: bool) -> str:
        url = make_url(value)
        driver = url.drivername
        if ensure_async:
            if driver == "postgresql":
                url = url.set(drivername="postgresql+asyncpg")
            elif driver == "postgresql+psycopg":
                url = url.set(drivername="postgresql+asyncpg")
            elif driver == "sqlite":
                url = url.set(drivername="sqlite+aiosqlite")
        else:
            if driver == "postgresql+asyncpg":
                url = url.set(drivername="postgresql+psycopg")
            elif driver == "sqlite+aiosqlite":
                url = url.set(drivername="sqlite")
        return url.render_as_string(hide_password=False)


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()


def reload_settings() -> Settings:
    """Refresh and return application settings."""

    get_settings.cache_clear()
    new_settings = get_settings()
    globals()["settings"] = new_settings
    return new_settings


settings = get_settings()
