from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from app.models.storage import EncryptedSecret, FileMetadata
    from app.models.user import User


class Seal(Base):
    """Digital seal owned by a user and backed by encrypted storage."""

    __tablename__ = "seals"
    __table_args__ = (UniqueConstraint("owner_id", "name", name="uq_seals_owner_name"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_file_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("file_metadata.id", ondelete="SET NULL"),
        nullable=True,
    )
    image_secret_id: Mapped[UUID | None] = mapped_column(
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
    image_file: Mapped[Optional["FileMetadata"]] = relationship(
        "FileMetadata",
        back_populates="seals",
    )
    image_secret: Mapped[Optional["EncryptedSecret"]] = relationship("EncryptedSecret")
