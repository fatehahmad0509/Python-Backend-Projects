"""Pydantic schemas for the chat endpoint."""
import uuid

from pydantic import BaseModel, Field, model_validator

from app.schemas.conversation import MessageRead


class ChatRequest(BaseModel):
    conversation_id: uuid.UUID | None = None
    message: str = Field(min_length=1, max_length=8000)
    # Optional image attached to this message (vision input). Both fields
    # must be provided together, e.g. image_mime_type="image/png".
    image_base64: str | None = Field(default=None, description="Base64-encoded image data.")
    image_mime_type: str | None = Field(default=None, description="MIME type of image_base64.")

    @model_validator(mode="after")
    def _validate_image_pair(self) -> "ChatRequest":
        if bool(self.image_base64) != bool(self.image_mime_type):
            raise ValueError("image_base64 and image_mime_type must be provided together")
        return self


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    title: str
    user_message: MessageRead
    assistant_message: MessageRead
