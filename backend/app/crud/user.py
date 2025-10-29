"""CRUD operations related to user entities."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.role import RoleSlug
from app.models.user import User, UserRole


async def get_user_by_email(*, session: AsyncSession, email: str) -> User | None:
    """Retrieve a user object by its email."""

    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_user_by_id(*, session: AsyncSession, user_id: int) -> User | None:
    """Retrieve a user object by its identifier."""

    statement = select(User).where(User.id == user_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def create_user(
    *,
    session: AsyncSession,
    email: str,
    password: str,
    role: UserRole = UserRole.USER,
) -> User:
    """Create a new user with the supplied credentials."""

    hashed_password = hash_password(password)
    user = User(email=email, hashed_password=hashed_password)
    user.role = role
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(
    *, session: AsyncSession, email: str, password: str
) -> User | None:
    """Return the user if the provided credentials are valid."""

    user = await get_user_by_email(session=session, email=email)
    if user is None:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def ensure_admin_user(
    *, session: AsyncSession, email: str, password: str, role: str
) -> User:
    """Create or update the initial administrator account."""

    try:
        normalized_role = RoleSlug(role.lower())
    except ValueError:
        normalized_role = RoleSlug.ADMIN

    user = await get_user_by_email(session=session, email=email)
    hashed_password = hash_password(password)

    if user is None:
        user = User(
            email=email,
            hashed_password=hashed_password,
            is_active=True,
        )
        user.role = normalized_role
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    needs_commit = False

    if not verify_password(password, user.hashed_password):
        user.hashed_password = hashed_password
        needs_commit = True

    if user.role != normalized_role.value:
        user.role = normalized_role
        needs_commit = True

    if not user.is_active:
        user.is_active = True
        needs_commit = True

    if needs_commit:
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user
