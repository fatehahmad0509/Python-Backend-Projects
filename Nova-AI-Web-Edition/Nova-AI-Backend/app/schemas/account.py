"""Pydantic schemas for account management endpoints."""
from pydantic import BaseModel, Field


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)
