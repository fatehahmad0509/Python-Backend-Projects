"""Message ORM model."""
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from app.db.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Message(Base):
    """A single message (user or assistant) within a conversation."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Optional image attached to a user message (base64-encoded), so it can be
    # replayed in the conversation detail view. Never sent back to Gemini for
    # older turns -- only the turn it was originally attached to is analyzed.
    image_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_mime_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Web sources Gemini cited when it used Google Search grounding for this
    # (assistant) turn, e.g. [{"title": ..., "url": ...}, ...]. None/empty
    # when the turn didn't trigger a search.
    sources: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role}>"
