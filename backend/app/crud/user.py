"""CRUD operations related to user entities."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole


def get_user_by_email(*, session: Session, email: str) -> User | None:
    """Retrieve a user object by its email."""

    statement = select(User).where(User.email == email)
    return session.scalar(statement)


def get_user_by_id(*, session: Session, user_id: int) -> User | None:
    """Retrieve a user object by its identifier."""

    statement = select(User).where(User.id == user_id)
    return session.scalar(statement)


def create_user(*, session: Session, email: str, password: str, role: UserRole = UserRole.USER) -> User:
    """Create a new user with the supplied credentials."""

    hashed_password = get_password_hash(password)
    user = User(email=email, hashed_password=hashed_password, role=role.value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(*, session: Session, email: str, password: str) -> User | None:
    """Return the user if the provided credentials are valid."""

    user = get_user_by_email(session=session, email=email)
    if user is None:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def ensure_admin_user(*, session: Session, email: str, password: str, role: str) -> User:
    """Create or update the initial administrator account."""

    try:
        normalized_role = UserRole(role.lower())
    except ValueError:
        normalized_role = UserRole.ADMIN

    user = get_user_by_email(session=session, email=email)
    hashed_password = get_password_hash(password)

    if user is None:
        user = User(
            email=email,
            hashed_password=hashed_password,
            role=normalized_role.value,
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    needs_commit = False

    if not verify_password(password, user.hashed_password):
        user.hashed_password = hashed_password
        needs_commit = True

    if user.role != normalized_role.value:
        user.role = normalized_role.value
        needs_commit = True

    if not user.is_active:
        user.is_active = True
        needs_commit = True

    if needs_commit:
        session.add(user)
        session.commit()
        session.refresh(user)

    return user
