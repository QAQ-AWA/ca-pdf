"""API endpoints for digital seal management operations."""

from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.config import settings
from app.core.errors import ForbiddenError, InvalidFileError, NotFoundError, OperationFailedError
from app.crud import audit_log as audit_log_crud
from app.crud import seal as seal_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.seal import SealCreate, SealListResponse, SealResponse
from app.services.storage import (
    EncryptedStorageService,
    StorageNotFoundError,
    StorageValidationError,
)

router = APIRouter(prefix="/pdf/seals", tags=["seals"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SealResponse,
)
async def upload_seal(
    *,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    name: str = Form(..., min_length=1, max_length=120),
    description: str | None = Form(default=None),
    file: UploadFile = File(...),
) -> SealResponse:
    """
    Upload a new digital seal.

    - **name**: Name of the seal (1-120 characters)
    - **description**: Optional description of the seal
    - **file**: Seal image file (PNG or SVG format, up to 5MB)

    Returns the created seal information.
    """
    if file.filename is None or file.content_type is None:
        raise InvalidFileError(
            "File and content type are required"
        )

    # Read the file content
    try:
        content = await file.read()
    except Exception as exc:
        raise InvalidFileError(
            "Failed to read uploaded file", str(exc)
        ) from exc

    # Validate the seal image
    storage_service = EncryptedStorageService()
    try:
        file_metadata, secret = await storage_service.store_seal_image(
            session=session,
            data=content,
            content_type=file.content_type,
            owner_id=current_user.id,
            filename=file.filename,
            audit_actor_id=current_user.id,
        )
    except StorageValidationError as exc:
        raise InvalidFileError(str(exc)) from exc

    # Create the seal record
    try:
        seal = await seal_crud.create_seal(
            session=session,
            owner_id=current_user.id,
            name=name,
            description=description,
            image_file_id=file_metadata.id,
            image_secret_id=secret.id,
            commit=True,
        )
    except Exception as exc:
        raise OperationFailedError(
            "Failed to create seal. Name might already exist for this user.", str(exc)
        ) from exc

    # Create audit log for seal creation
    await audit_log_crud.create_audit_log(
        session=session,
        actor_id=current_user.id,
        event_type="seal.created",
        resource="seal",
        meta={
            "seal_id": str(seal.id),
            "name": seal.name,
            "file_id": str(file_metadata.id),
            "size_bytes": file_metadata.size_bytes,
        },
        commit=True,
    )

    return SealResponse(
        id=seal.id,
        name=seal.name,
        description=seal.description,
        created_at=seal.created_at,
        updated_at=seal.updated_at,
    )


@router.get("", response_model=SealListResponse)
async def list_seals(
    *,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of items to return"
    ),
) -> SealListResponse:
    """
    List all seals belonging to the current user.

    - **skip**: Number of items to skip (default: 0)
    - **limit**: Maximum number of items to return (default: 10, max: 100)

    Returns a paginated list of seals.
    """
    seals = await seal_crud.list_seals_for_owner(
        session=session, owner_id=current_user.id
    )

    # Apply pagination
    total = len(seals)
    paginated_seals = seals[skip : skip + limit]

    return SealListResponse(
        items=[
            SealResponse(
                id=seal.id,
                name=seal.name,
                description=seal.description,
                created_at=seal.created_at,
                updated_at=seal.updated_at,
            )
            for seal in paginated_seals
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{seal_id}/image")
async def download_seal_image(
    *,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    seal_id: UUID,
) -> StreamingResponse:
    """
    Download the image file for a seal.

    - **seal_id**: UUID of the seal

    Returns the seal image as a binary stream.
    """
    seal = await seal_crud.get_seal_by_id(session=session, seal_id=seal_id)

    if seal is None:
        raise NotFoundError("Seal")

    # Verify ownership
    if seal.owner_id != current_user.id:
        raise ForbiddenError("You do not have permission to access this seal")

    if seal.image_file is None or seal.image_secret is None:
        raise NotFoundError("Seal image")

    # Retrieve the encrypted image
    storage_service = EncryptedStorageService()
    try:
        image_data = await storage_service.load_seal_image(
            session=session, secret_id=seal.image_secret.id
        )
    except StorageNotFoundError as exc:
        raise NotFoundError("Seal image") from exc

    # Determine the media type from the file metadata
    media_type = seal.image_file.content_type

    return StreamingResponse(
        iter([image_data]),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{seal.image_file.filename}"'
        },
    )


@router.delete("/{seal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seal(
    *,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    seal_id: UUID,
) -> Response:
    """
    Delete a seal.

    - **seal_id**: UUID of the seal to delete

    Only the seal owner can delete it. Returns 204 No Content on success.
    """
    seal = await seal_crud.get_seal_by_id(session=session, seal_id=seal_id)

    if seal is None:
        raise NotFoundError("Seal")

    # Verify ownership
    if seal.owner_id != current_user.id:
        raise ForbiddenError("You do not have permission to delete this seal")

    # Delete the seal
    await seal_crud.delete_seal(session=session, seal=seal, commit=True)

    # Create audit log for seal deletion
    await audit_log_crud.create_audit_log(
        session=session,
        actor_id=current_user.id,
        event_type="seal.deleted",
        resource="seal",
        meta={
            "seal_id": str(seal.id),
            "name": seal.name,
        },
        commit=True,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
