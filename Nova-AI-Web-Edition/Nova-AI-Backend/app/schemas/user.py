"""Pydantic schemas for user data."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRead(BaseModel):
    """Public representation of a user (never includes password_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    details: str | None = None
    plan: str
    created_at: datetime


class UserDetailsUpdate(BaseModel):
    """Free-form info the user shares about themselves, given to Nova as context."""

    details: str = Field(default="", max_length=4000)


class UsageRead(BaseModel):
    """Today's token/search usage for the current user, plus their plan's limits.

    `token_limit` / `search_limit` are null for unlimited (developer) plans
    so the frontend can render "unlimited" instead of a bogus huge number.
    """

    plan: str
    tokens_used_today: int
    token_limit: int | None
    searches_used_today: int
    search_limit: int | None
