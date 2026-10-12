"""Shared/generic response schemas used across multiple routers."""
from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Generic success envelope for endpoints with no other payload to return."""

    success: bool = True
    message: str
