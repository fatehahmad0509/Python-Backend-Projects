"""Custom exceptions and centralized error response formatting.

All error responses follow the shape:
    {"success": false, "message": "...", "error": "..."}
Internal error details are never leaked to clients.
"""
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Base class for application-level errors with an HTTP status code."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, error: str = "app_error"):
        self.message = message
        self.status_code = status_code
        self.error = error
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND, "not_found")


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, "unauthorized")


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status.HTTP_403_FORBIDDEN, "forbidden")


class ConflictError(AppError):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status.HTTP_409_CONFLICT, "conflict")


class RateLimitError(AppError):
    def __init__(self, message: str = "Too many requests"):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS, "rate_limited")


class InvalidCodeError(AppError):
    def __init__(self, message: str = "Invalid or expired verification code"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, "invalid_code")


class TokenLimitExceededError(AppError):
    def __init__(self, message: str = "Daily token limit reached."):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS, "TOKEN_LIMIT_EXCEEDED")


class AccountBlockedError(AppError):
    def __init__(self, message: str = "Your account has been blocked."):
        super().__init__(message, status.HTTP_403_FORBIDDEN, "ACCOUNT_BLOCKED")


class InvalidImageError(AppError):
    def __init__(self, message: str = "The provided image is invalid."):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, "invalid_image")


def _envelope(message: str, error: str) -> dict:
    return {"success": False, "message": message, "error": error}


def register_exception_handlers(app) -> None:
    """Attach all exception handlers to the FastAPI app."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_envelope(exc.message, exc.error))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(str(exc.detail), "http_error"),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_envelope("Invalid request data", "validation_error"),
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        # Internal details are logged server-side only, never returned to the client.
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope("An internal error occurred", "internal_error"),
        )
