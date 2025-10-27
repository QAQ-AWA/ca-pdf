from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from app.models.storage import EncryptedSecret, FileMetadata
    from app.models.user import User


class CertificateStatus(str, Enum):
    """Lifecycle states for a digital certificate."""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    PENDING = "pending"


class Certificate(Base):
    """Represents an X.509 certificate and optional encrypted private key."""

    __tablename__ = "certificates"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL")
    )
    serial_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    subject_common_name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CertificateStatus.ACTIVE.value
    )
    certificate_pem: Mapped[str] = mapped_column(Text, nullable=False)
    certificate_file_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("file_metadata.id", ondelete="SET NULL"),
        nullable=True,
    )
    private_key_secret_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("encrypted_secrets.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    owner: Mapped[Optional["User"]] = relationship("User")
    certificate_file: Mapped[Optional["FileMetadata"]] = relationship(
        "FileMetadata",
        back_populates="certificates",
    )
    private_key_secret: Mapped[Optional["EncryptedSecret"]] = relationship(
        "EncryptedSecret"
    )
