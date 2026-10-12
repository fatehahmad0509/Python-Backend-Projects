"""
Shared schemas used across the API, primarily the standard response envelope.

Every endpoint returns responses shaped like:

Success:
    {"success": true, "message": "Success", "data": {...}}

Error (see exceptions.handlers for how these are produced):
    {"success": false, "message": "...", "error": {"code": "...", "details": {...}}}
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    details: dict[str, Any] | None = None


class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: T | None = None


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
