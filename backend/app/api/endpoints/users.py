"""User management API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user, require_admin
from app.core.config import settings
from app.core.errors import (
    AlreadyExistsError,
    ForbiddenError,
    InvalidStateError,
    NotFoundError,
    ValidationError,
)
from app.crud import audit_log as audit_log_crud
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.role import RoleSlug
from app.models.user import User
from app.schemas.user import (
    ResetPasswordRequest,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)

router = APIRouter()


@router.get(
    "/",
    response_model=UserListResponse,
    tags=["users"],
)
async def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    search: str = Query(default=""),
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> UserListResponse:
    """Get a paginated list of users.

    Only administrators can access this endpoint.
    Supports filtering by search term, role, and active status.
    """
    users, total_count = await user_crud.list_users(
        session=session,
        skip=skip,
        limit=limit,
        search=search if search else None,
        role=role,
        is_active=is_active,
    )

    items = [UserResponse.model_validate(user) for user in users]
    return UserListResponse(
        items=items,
        total_count=total_count,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["users"],
)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Create a new user.

    Only administrators can create users.
    Validates that username and email are unique.
    """
    # Check username uniqueness
    existing_user = await user_crud.get_user_by_username(
        session=session, username=user_data.username
    )
    if existing_user:
        raise AlreadyExistsError("User", user_data.username)

    # Check email uniqueness
    existing_email = await user_crud.get_user_by_email(
        session=session, email=user_data.email
    )
    if existing_email:
        raise AlreadyExistsError("User", user_data.email)

    # Create the user
    new_user = await user_crud.create_user(
        session=session,
        email=user_data.email,
        password=user_data.password,
        username=user_data.username,
        role=RoleSlug(user_data.role),
        is_active=user_data.is_active,
    )

    # Record audit log
    await audit_log_crud.create_audit_log(
        session=session,
        actor_id=current_user.id,
        event_type="user_created",
        resource="user",
        meta={"user_id": new_user.id, "username": new_user.username},
        message=f"User {new_user.username} created",
        commit=True,
    )

    return UserResponse.model_validate(new_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    tags=["users"],
)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Get details of a specific user.

    Administrators can view any user.
    Regular users can only view their own information.
    """
    user = await user_crud.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise NotFoundError("User", str(user_id))

    # Check permissions
    is_admin = current_user.role == "admin"
    if not is_admin and current_user.id != user_id:
        raise ForbiddenError("You can only view your own user information")

    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    tags=["users"],
)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update user information.

    Administrators can update any user.
    Regular users can only update their own email.
    """
    user = await user_crud.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise NotFoundError("User", str(user_id))

    # Check permissions
    is_admin = current_user.role == "admin"
    if not is_admin and current_user.id != user_id:
        raise ForbiddenError("You can only update your own user information")

    # Non-admin users can only update their email
    if not is_admin:
        if user_update.role is not None or user_update.is_active is not None:
            raise ForbiddenError("You do not have permission to modify those fields")

    # If email is being updated, check uniqueness
    if user_update.email and user_update.email != user.email:
        existing_email = await user_crud.get_user_by_email(
            session=session, email=user_update.email
        )
        if existing_email:
            raise AlreadyExistsError("Email", user_update.email)

    # Update the user
    updated_user = await user_crud.update_user(
        session=session,
        user=user,
        email=user_update.email,
        role=user_update.role,
        is_active=user_update.is_active,
    )

    # Record audit log
    changes: dict[str, Any] = {}
    if user_update.email and user_update.email != user.email:
        changes["email"] = user_update.email
    if user_update.role and user_update.role != user.role:
        changes["role"] = user_update.role
    if user_update.is_active is not None and user_update.is_active != user.is_active:
        changes["is_active"] = user_update.is_active

    if changes:
        await audit_log_crud.create_audit_log(
            session=session,
            actor_id=current_user.id,
            event_type="user_updated",
            resource="user",
            meta={"user_id": user_id, "changes": changes},
            message=f"User {user.username} updated",
            commit=True,
        )

    return UserResponse.model_validate(updated_user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["users"],
    response_model=None,
)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete a user.

    Only administrators can delete users.
    Cannot delete self.
    Cannot delete the last active admin.
    """
    user = await user_crud.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise NotFoundError("User", str(user_id))

    # Cannot delete self
    if user.id == current_user.id:
        raise ForbiddenError("You cannot delete your own account")

    # Cannot delete last active admin
    if user.role == "admin" and user.is_active:
        active_admin_count = await user_crud.count_active_admin_users(session=session)
        if active_admin_count <= 1:
            raise InvalidStateError(
                "Cannot delete the last active administrator",
                "There must be at least one active admin user",
            )

    # Delete the user
    await user_crud.delete_user(session=session, user_id=user_id)

    # Record audit log
    await audit_log_crud.create_audit_log(
        session=session,
        actor_id=current_user.id,
        event_type="user_deleted",
        resource="user",
        meta={"user_id": user_id, "username": user.username},
        message=f"User {user.username} deleted",
        commit=True,
    )


@router.post(
    "/{user_id}/reset-password",
    response_model=UserResponse,
    tags=["users"],
)
async def reset_password(
    user_id: int,
    reset_data: ResetPasswordRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Reset a user's password.

    Administrators can reset any user's password.
    Regular users can only reset their own password.
    """
    user = await user_crud.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise NotFoundError("User", str(user_id))

    # Check permissions
    is_admin = current_user.role == "admin"
    if not is_admin and current_user.id != user_id:
        raise ForbiddenError("You can only reset your own password")

    # Update password
    updated_user = await user_crud.update_user_password(
        session=session,
        user=user,
        new_password=reset_data.new_password,
    )

    # Record audit log
    await audit_log_crud.create_audit_log(
        session=session,
        actor_id=current_user.id,
        event_type="password_reset",
        resource="user",
        meta={"user_id": user_id},
        message=f"Password reset for user {user.username}",
        commit=True,
    )

    return UserResponse.model_validate(updated_user)


@router.post(
    "/{user_id}/toggle-active",
    response_model=UserResponse,
    tags=["users"],
)
async def toggle_active(
    user_id: int,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Toggle the active status of a user.

    Only administrators can toggle user status.
    Cannot toggle self.
    Cannot disable the last active admin.
    """
    user = await user_crud.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise NotFoundError("User", str(user_id))

    # Cannot toggle self
    if user.id == current_user.id:
        raise ForbiddenError("You cannot disable your own account")

    # Cannot disable the last active admin
    if user.is_active and user.role == "admin":
        active_admin_count = await user_crud.count_active_admin_users(session=session)
        if active_admin_count <= 1:
            raise InvalidStateError(
                "Cannot disable the last active administrator",
                "There must be at least one active admin user",
            )

    # Toggle status
    new_is_active = not user.is_active
    updated_user = await user_crud.update_user(
        session=session,
        user=user,
        is_active=new_is_active,
    )

    # Record audit log
    await audit_log_crud.create_audit_log(
        session=session,
        actor_id=current_user.id,
        event_type="user_status_toggled",
        resource="user",
        meta={"user_id": user_id, "new_status": new_is_active},
        message=f"User {user.username} status changed to {'active' if new_is_active else 'inactive'}",
        commit=True,
    )

    return UserResponse.model_validate(updated_user)
