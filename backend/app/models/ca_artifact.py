from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from app.models.storage import EncryptedSecret, FileMetadata


class CAArtifactType(str, Enum):
    """Categories of certificate authority artifacts."""

    ROOT_CERTIFICATE = "root-certificate"
    INTERMEDIATE_CERTIFICATE = "intermediate-certificate"
    CRL = "certificate-revocation-list"
    OCSP_RESPONSE = "ocsp-response"


class CAArtifact(Base):
    """Artifacts produced by the certificate authority (e.g. CRL, OCSP)."""

    __tablename__ = "ca_artifacts"
    __table_args__ = (UniqueConstraint("name", name="uq_ca_artifacts_name"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("file_metadata.id", ondelete="SET NULL"),
        nullable=True,
    )
    secret_id: Mapped[UUID | None] = mapped_column(
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

    file: Mapped[Optional["FileMetadata"]] = relationship(
        "FileMetadata",
        back_populates="ca_artifacts",
    )
    secret: Mapped[Optional["EncryptedSecret"]] = relationship("EncryptedSecret")
