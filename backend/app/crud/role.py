"""CRUD helpers for role management."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role, RoleSlug


async def get_role(*, session: AsyncSession, slug: RoleSlug) -> Role | None:
    statement = select(Role).where(Role.slug == slug.value)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def ensure_role(
    *,
    session: AsyncSession,
    slug: RoleSlug,
    name: str | None = None,
    description: str | None = None,
) -> Role:
    role = await get_role(session=session, slug=slug)
    display_name = name or _default_role_name(slug)

    if role is None:
        role = Role(slug=slug.value, name=display_name, description=description)
        session.add(role)
        await session.commit()
        await session.refresh(role)
        return role

    needs_update = False
    if role.name != display_name:
        role.name = display_name
        needs_update = True
    if description is not None and role.description != description:
        role.description = description
        needs_update = True

    if needs_update:
        session.add(role)
        await session.commit()
        await session.refresh(role)

    return role


async def ensure_default_roles(session: AsyncSession) -> None:
    for slug in RoleSlug:
        await ensure_role(session=session, slug=slug)


def _default_role_name(slug: RoleSlug) -> str:
    return slug.value.replace("-", " ").replace("_", " ").title()
