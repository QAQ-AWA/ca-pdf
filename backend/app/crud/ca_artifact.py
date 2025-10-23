"""CRUD helpers for certificate authority artifacts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ca_artifact import CAArtifact, CAArtifactType


async def get_latest_artifact_by_type(
    *,
    session: AsyncSession,
    artifact_type: CAArtifactType,
) -> CAArtifact | None:
    """Return the most recently created artifact for the supplied type."""

    statement: Select[CAArtifact] = (
        select(CAArtifact)
        .where(CAArtifact.artifact_type == artifact_type.value)
        .order_by(CAArtifact.created_at.desc())
        .limit(1)
        .options(
            selectinload(CAArtifact.file),
            selectinload(CAArtifact.secret),
        )
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def create_artifact(
    *,
    session: AsyncSession,
    name: str,
    artifact_type: CAArtifactType,
    description: str | None = None,
    file_id: UUID | None = None,
    secret_id: UUID | None = None,
    commit: bool = True,
) -> CAArtifact:
    """Persist a new certificate authority artifact."""

    artifact = CAArtifact(
        name=name,
        artifact_type=artifact_type.value,
        description=description,
        file_id=file_id,
        secret_id=secret_id,
    )
    session.add(artifact)
    await session.flush()
    if commit:
        await session.commit()
        await session.refresh(artifact)
    return artifact


async def list_artifacts(
    *,
    session: AsyncSession,
    artifact_type: CAArtifactType | None = None,
    limit: int | None = None,
) -> list[CAArtifact]:
    """Return artifacts ordered from newest to oldest."""

    statement: Select[CAArtifact] = select(CAArtifact).order_by(CAArtifact.created_at.desc())
    if artifact_type is not None:
        statement = statement.where(CAArtifact.artifact_type == artifact_type.value)
    if limit is not None:
        statement = statement.limit(limit)
    statement = statement.options(selectinload(CAArtifact.file))
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_artifact_by_id(*, session: AsyncSession, artifact_id: UUID) -> CAArtifact | None:
    """Retrieve a certificate authority artifact by its identifier."""

    statement: Select[CAArtifact] = (
        select(CAArtifact)
        .where(CAArtifact.id == artifact_id)
        .options(
            selectinload(CAArtifact.file),
            selectinload(CAArtifact.secret),
        )
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()
