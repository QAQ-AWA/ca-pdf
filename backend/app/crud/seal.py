"""CRUD helpers for managing digital seals."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seal import Seal


async def create_seal(
    *,
    session: AsyncSession,
    owner_id: int | None,
    name: str,
    description: str | None,
    image_file_id: UUID | None,
    image_secret_id: UUID | None,
    commit: bool = True,
) -> Seal:
    """Persist a new seal record."""

    seal = Seal(
        owner_id=owner_id,
        name=name,
        description=description,
        image_file_id=image_file_id,
        image_secret_id=image_secret_id,
    )
    session.add(seal)
    await session.flush()
    if commit:
        await session.commit()
        await session.refresh(seal)
    return seal


async def get_seal_by_id(*, session: AsyncSession, seal_id: UUID) -> Seal | None:
    """Return a seal by its identifier."""

    statement = select(Seal).where(Seal.id == seal_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def list_seals_for_owner(
    *,
    session: AsyncSession,
    owner_id: int,
) -> list[Seal]:
    """Return seals associated with a user."""

    statement = select(Seal).where(Seal.owner_id == owner_id)
    statement = statement.order_by(Seal.created_at.desc())
    result = await session.execute(statement)
    return list(result.scalars().all())


async def delete_seal(
    *,
    session: AsyncSession,
    seal: Seal,
    commit: bool = True,
) -> None:
    """Delete a seal record."""

    await session.delete(seal)
    if commit:
        await session.commit()
