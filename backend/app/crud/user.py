"""CRUD operations related to user entities."""

from __future__ import annotations

import operator
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.role import RoleSlug
from app.models.user import User, UserRole


async def get_user_by_email(*, session: AsyncSession, email: str) -> User | None:
    """Retrieve a user object by its email."""

    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_user_by_username(*, session: AsyncSession, username: str) -> User | None:
    """Retrieve a user object by its username."""

    statement = select(User).where(User.username == username)
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
    username: str | None = None,
    role: UserRole = UserRole.USER,
    is_active: bool = True,
) -> User:
    """Create a new user with the supplied credentials."""

    # Generate username from email if not provided
    if username is None:
        username = email.split("@")[0]

    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_active=is_active,
    )
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
    hashed_password = get_password_hash(password)

    if user is None:
        # Generate username from email for backward compatibility
        username = email.split("@")[0]
        user = User(
            username=username,
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


async def list_users(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[User], int]:
    """List users with optional filtering and pagination."""

    conditions: list[Any] = []

    if search:
        search_param = f"%{search}%"
        conditions.append(
            (User.username.ilike(search_param)) | (User.email.ilike(search_param))
        )

    if role:
        conditions.append(User._role_slug == role.lower())

    if is_active is not None:
        conditions.append(User.is_active == is_active)

    base_query = select(User)
    if conditions:
        combined_condition = conditions[0]
        for condition in conditions[1:]:
            combined_condition = operator.and_(combined_condition, condition)
        base_query = base_query.where(combined_condition)

    count_stmt = select(func.count(User.id))
    if conditions:
        combined_condition = conditions[0]
        for condition in conditions[1:]:
            combined_condition = operator.and_(combined_condition, condition)
        count_stmt = count_stmt.where(combined_condition)

    base_query = base_query.order_by(User.created_at.desc(), User.id.desc())
    base_query = base_query.offset(skip).limit(limit)

    result = await session.execute(base_query)
    users = list(result.scalars().all())

    total_result = await session.execute(count_stmt)
    total = int(total_result.scalar_one())

    return users, total


async def update_user(
    *,
    session: AsyncSession,
    user: User,
    email: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> User:
    """Update user details."""

    if email is not None:
        user.email = email

    if role is not None:
        user.role = role.lower()

    if is_active is not None:
        user.is_active = is_active

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(
    *,
    session: AsyncSession,
    user_id: int,
) -> None:
    """Delete a user."""

    user = await get_user_by_id(session=session, user_id=user_id)
    if user:
        session.delete(user)
        await session.commit()


async def update_user_password(
    *,
    session: AsyncSession,
    user: User,
    new_password: str,
) -> User:
    """Update user password."""

    user.hashed_password = get_password_hash(new_password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def count_active_admin_users(*, session: AsyncSession) -> int:
    """Count the number of active admin users."""

    statement = select(func.count(User.id)).where(
        (User._role_slug == RoleSlug.ADMIN.value) & (User.is_active == True)
    )
    result = await session.execute(statement)
    return int(result.scalar_one())
