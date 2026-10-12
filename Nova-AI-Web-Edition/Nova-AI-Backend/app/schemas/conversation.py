"""Pydantic schemas for conversations."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    image_base64: str | None = None
    image_mime_type: str | None = None
    sources: list[dict] | None = None
    created_at: datetime


class ConversationDetailRead(ConversationRead):
    messages: list[MessageRead] = []
