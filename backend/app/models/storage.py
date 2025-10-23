from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from app.models.ca_artifact import CAArtifact
    from app.models.certificate import Certificate
    from app.models.seal import Seal
    from app.models.user import User


class FileMetadata(Base):
    """Metadata describing stored binary assets."""

    __tablename__ = "file_metadata"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(32), nullable=False, default="database")
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
    encrypted_payload: Mapped[Optional["EncryptedSecret"]] = relationship(
        "EncryptedSecret",
        back_populates="file",
        uselist=False,
        cascade="all, delete-orphan",
    )
    certificates: Mapped[list["Certificate"]] = relationship("Certificate", back_populates="certificate_file")
    seals: Mapped[list["Seal"]] = relationship("Seal", back_populates="image_file")
    ca_artifacts: Mapped[list["CAArtifact"]] = relationship("CAArtifact", back_populates="file")


class EncryptedSecret(Base):
    """Encrypted payload stored at rest and associated with file metadata."""

    __tablename__ = "encrypted_secrets"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    file_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("file_metadata.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    algorithm: Mapped[str] = mapped_column(String(20), nullable=False)
    key_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    nonce: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    tag: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
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

    file: Mapped[FileMetadata] = relationship("FileMetadata", back_populates="encrypted_payload")
