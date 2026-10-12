"""
Global exception handlers.

Every error response returned by the API follows the same shape:

    {
      "success": false,
      "message": "Human readable message",
      "error": {"code": "MACHINE_READABLE_CODE", "details": {...} | null}
    }
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.constants.errors import ErrorCode
from app.exceptions.custom_exceptions import AppException

logger = logging.getLogger("transly.exceptions")


def _error_response(
    status_code: int, message: str, code: str, details: dict[str, Any] | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "error": {"code": code, "details": details},
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return _error_response(exc.status_code, exc.message, exc.error_code, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Validation failed",
            ErrorCode.VALIDATION_ERROR,
            {"errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception while processing request", exc_info=exc)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal server error",
            ErrorCode.INTERNAL_SERVER_ERROR,
            None,
        )
