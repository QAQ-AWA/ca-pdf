"""Error codes and custom exception classes for standardized error handling."""

from __future__ import annotations

from enum import Enum
from typing import Optional


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""

    # Authentication errors
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"

    # Authorization errors
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # Validation errors
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_FILE = "INVALID_FILE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"

    # Business logic errors
    OPERATION_FAILED = "OPERATION_FAILED"
    INVALID_STATE = "INVALID_STATE"

    # Server errors
    INTERNAL_ERROR = "INTERNAL_ERROR"


class APIException(Exception):
    """Base exception class for API errors."""

    def __init__(
        self,
        code: str,
        message: str,
        detail: Optional[str] = None,
        status_code: int = 400,
    ) -> None:
        """Initialize an API exception.

        Args:
            code: Error code identifying the error type
            message: User-friendly error message
            detail: Technical details (optional, hidden in production)
            status_code: HTTP status code
        """
        self.code = code
        self.message = message
        self.detail = detail
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(APIException):
    """Raised for input validation errors."""

    def __init__(self, message: str, detail: Optional[str] = None) -> None:
        super().__init__(
            code=ErrorCode.INVALID_INPUT,
            message=message,
            detail=detail,
            status_code=400,
        )


class InvalidFileError(APIException):
    """Raised for invalid file errors."""

    def __init__(self, message: str, detail: Optional[str] = None) -> None:
        super().__init__(
            code=ErrorCode.INVALID_FILE,
            message=message,
            detail=detail,
            status_code=400,
        )


class FileTooLargeError(APIException):
    """Raised when file size exceeds limit."""

    def __init__(self, message: str, detail: Optional[str] = None) -> None:
        super().__init__(
            code=ErrorCode.FILE_TOO_LARGE,
            message=message,
            detail=detail,
            status_code=413,
        )


class UnauthorizedError(APIException):
    """Raised for authentication failures."""

    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(
            code=ErrorCode.UNAUTHORIZED,
            message=message,
            detail=None,
            status_code=401,
        )


class InvalidTokenError(APIException):
    """Raised for invalid token errors."""

    def __init__(self, message: str = "Invalid token") -> None:
        super().__init__(
            code=ErrorCode.INVALID_TOKEN,
            message=message,
            detail=None,
            status_code=401,
        )


class TokenExpiredError(APIException):
    """Raised for expired token errors."""

    def __init__(self, message: str = "Token has expired") -> None:
        super().__init__(
            code=ErrorCode.TOKEN_EXPIRED,
            message=message,
            detail=None,
            status_code=401,
        )


class ForbiddenError(APIException):
    """Raised for authorization failures."""

    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(
            code=ErrorCode.FORBIDDEN,
            message=message,
            detail=None,
            status_code=403,
        )


class InsufficientPermissionsError(APIException):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(
            code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            message=message,
            detail=None,
            status_code=403,
        )


class NotFoundError(APIException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: Optional[str] = None) -> None:
        message = f"{resource} not found"
        detail = (
            f"Could not find {resource} with identifier: {identifier}"
            if identifier
            else None
        )
        super().__init__(
            code=ErrorCode.NOT_FOUND,
            message=message,
            detail=detail,
            status_code=404,
        )


class AlreadyExistsError(APIException):
    """Raised when trying to create a resource that already exists."""

    def __init__(self, resource: str, identifier: Optional[str] = None) -> None:
        message = f"{resource} already exists"
        detail = (
            f"A {resource} with identifier '{identifier}' already exists"
            if identifier
            else None
        )
        super().__init__(
            code=ErrorCode.ALREADY_EXISTS,
            message=message,
            detail=detail,
            status_code=409,
        )


class OperationFailedError(APIException):
    """Raised when an operation fails."""

    def __init__(self, message: str, detail: Optional[str] = None) -> None:
        super().__init__(
            code=ErrorCode.OPERATION_FAILED,
            message=message,
            detail=detail,
            status_code=400,
        )


class InvalidStateError(APIException):
    """Raised when resource is in invalid state for operation."""

    def __init__(self, message: str, detail: Optional[str] = None) -> None:
        super().__init__(
            code=ErrorCode.INVALID_STATE,
            message=message,
            detail=detail,
            status_code=400,
        )


class InternalServerError(APIException):
    """Raised for unexpected internal errors."""

    def __init__(self, detail: Optional[str] = None) -> None:
        super().__init__(
            code=ErrorCode.INTERNAL_ERROR,
            message="An internal server error occurred",
            detail=detail,
            status_code=500,
        )
