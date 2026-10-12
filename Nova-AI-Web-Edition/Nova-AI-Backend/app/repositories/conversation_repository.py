"""Data access layer for the Conversation model."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation


class ConversationRepository:
    """Encapsulates all direct database access for conversations."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, user_id: uuid.UUID, title: str) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title)
        self._db.add(conversation)
        await self._db.commit()
        await self._db.refresh(conversation)
        return conversation

    async def get_by_id(self, conversation_id: uuid.UUID) -> Conversation | None:
        result = await self._db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_messages(self, conversation_id: uuid.UUID) -> Conversation | None:
        result = await self._db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> list[Conversation]:
        result = await self._db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, conversation: Conversation) -> None:
        await self._db.delete(conversation)
        await self._db.commit()

    async def update_title(self, conversation: Conversation, title: str) -> None:
        """Overwrite a conversation's title (used by async post-hoc title generation)."""
        conversation.title = title
        self._db.add(conversation)
        await self._db.commit()
        await self._db.refresh(conversation)

    async def touch(self, conversation: Conversation) -> None:
        """Mark a conversation as updated (bumps updated_at)."""
        from sqlalchemy import func

        conversation.updated_at = func.now()
        self._db.add(conversation)
        await self._db.commit()
        await self._db.refresh(conversation)
