"""Data access layer for the Message model."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


class MessageRepository:
    """Encapsulates all direct database access for messages."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        image_base64: str | None = None,
        image_mime_type: str | None = None,
        sources: list[dict] | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            image_base64=image_base64,
            image_mime_type=image_mime_type,
            sources=sources or None,
        )
        self._db.add(message)
        await self._db.commit()
        await self._db.refresh(message)
        return message

    async def list_for_conversation(self, conversation_id: uuid.UUID) -> list[Message]:
        result = await self._db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())
