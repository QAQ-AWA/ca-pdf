"""Helpers for validating and reading uploaded files."""

from __future__ import annotations

from typing import Collection

from fastapi import HTTPException, UploadFile, status

__all__ = ["read_upload_file"]

_DEFAULT_CHUNK_SIZE = 1024 * 1024


def _normalize_content_types(allowed: Collection[str]) -> set[str]:
    return {item.lower().strip() for item in allowed if item}


async def read_upload_file(
    upload_file: UploadFile,
    *,
    allowed_content_types: Collection[str],
    max_bytes: int,
    kind: str,
    filename: str | None = None,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
) -> bytes:
    """Read an uploaded file enforcing size and MIME constraints."""

    normalized_types = _normalize_content_types(allowed_content_types)
    display_name = filename or (upload_file.filename or kind)
    content_type = (upload_file.content_type or "").lower().strip()

    if normalized_types and content_type not in normalized_types:
        allowed_display = ", ".join(sorted(normalized_types)) or "none"
        message = (
            f"{kind} content type '{upload_file.content_type or 'unknown'}' is not allowed. "
            f"Allowed types: {allowed_display}."
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    total_bytes = 0
    buffer = bytearray()

    try:
        while True:
            chunk = await upload_file.read(chunk_size)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > max_bytes:
                message = (
                    f"{kind} file '{display_name}' exceeds the maximum allowed size of {max_bytes} bytes"
                )
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
            buffer.extend(chunk)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive error mapping
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process {kind.lower()} upload: {exc}",
        ) from exc
    finally:
        await upload_file.close()

    if not buffer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{kind} file '{display_name}' is empty",
        )

    return bytes(buffer)
