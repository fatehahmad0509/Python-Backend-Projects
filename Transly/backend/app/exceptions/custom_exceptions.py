"""
Custom application exception hierarchy.

Services and repositories raise these exceptions instead of returning
HTTP-specific objects, keeping business logic decoupled from the web
framework. `exceptions.handlers` translates them into the standard API
error response shape.
"""

from typing import Any

from starlette import status

from app.constants.errors import ErrorCode


class AppException(Exception):
    """Base class for all application-level exceptions."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = ErrorCode.INTERNAL_SERVER_ERROR

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


class ValidationException(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = ErrorCode.VALIDATION_ERROR


class ConflictException(AppException):
    status_code = status.HTTP_409_CONFLICT
    error_code = ErrorCode.CONFLICT


class NotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = ErrorCode.NOT_FOUND


class AuthenticationException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = ErrorCode.UNAUTHORIZED


class ForbiddenException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = ErrorCode.FORBIDDEN


class UsageLimitExceededException(AppException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = ErrorCode.DAILY_LIMIT_EXCEEDED


class RateLimitExceededException(AppException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = ErrorCode.RATE_LIMIT_EXCEEDED


class InvalidImageException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.INVALID_IMAGE


class InvalidVideoException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.INVALID_VIDEO


class GeminiServiceException(AppException):
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = ErrorCode.GEMINI_SERVICE_ERROR
