"""CRUD helpers for managing X.509 certificates."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.certificate import Certificate, CertificateStatus


async def create_certificate(
    *,
    session: AsyncSession,
    owner_id: int | None,
    serial_number: str,
    subject_common_name: str,
    subject_organization: str | None,
    issued_at: datetime,
    expires_at: datetime,
    certificate_pem: str,
    certificate_file_id: UUID | None,
    private_key_secret_id: UUID | None,
    commit: bool = True,
) -> Certificate:
    """Persist a new certificate record."""

    certificate = Certificate(
        owner_id=owner_id,
        serial_number=serial_number,
        subject_common_name=subject_common_name,
        subject_organization=subject_organization,
        issued_at=issued_at,
        expires_at=expires_at,
        certificate_pem=certificate_pem,
        certificate_file_id=certificate_file_id,
        private_key_secret_id=private_key_secret_id,
        status=CertificateStatus.ACTIVE.value,
    )
    session.add(certificate)
    await session.flush()
    if commit:
        await session.commit()
        await session.refresh(certificate)
    return certificate


async def get_certificate_by_id(*, session: AsyncSession, certificate_id: UUID) -> Certificate | None:
    """Return a certificate by its identifier."""

    statement = select(Certificate).where(Certificate.id == certificate_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_certificate_by_serial(*, session: AsyncSession, serial_number: str) -> Certificate | None:
    """Return a certificate by its serial number."""

    statement = select(Certificate).where(Certificate.serial_number == serial_number)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def list_certificates_for_owner(
    *,
    session: AsyncSession,
    owner_id: int,
    include_inactive: bool = True,
) -> list[Certificate]:
    """Return certificates associated with a user."""

    statement = select(Certificate).where(Certificate.owner_id == owner_id)
    if not include_inactive:
        statement = statement.where(Certificate.status == CertificateStatus.ACTIVE.value)
    statement = statement.order_by(Certificate.created_at.desc())
    statement = statement.options(selectinload(Certificate.certificate_file))
    result = await session.execute(statement)
    return list(result.scalars().all())


async def list_revoked_certificates(*, session: AsyncSession) -> list[Certificate]:
    """Return all revoked certificates."""

    statement = select(Certificate).where(Certificate.status == CertificateStatus.REVOKED.value)
    statement = statement.order_by(Certificate.updated_at.desc())
    result = await session.execute(statement)
    return list(result.scalars().all())


async def mark_certificate_revoked(
    *,
    session: AsyncSession,
    certificate: Certificate,
    commit: bool = True,
) -> Certificate:
    """Mark a certificate as revoked if it is not already."""

    if certificate.status == CertificateStatus.REVOKED.value:
        return certificate
    certificate.status = CertificateStatus.REVOKED.value
    session.add(certificate)
    await session.flush()
    if commit:
        await session.commit()
        await session.refresh(certificate)
    return certificate
