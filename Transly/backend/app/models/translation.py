"""
Translation model.

Stores the full result of every translation request for history purposes.

Indexes:
- Composite index on (user_id, created_at): supports the history query

      WHERE user_id = ? ORDER BY created_at DESC

  A standard ascending B-tree index on (user_id, created_at) is sufficient
  here because PostgreSQL can scan a B-tree index backwards just as
  efficiently as forwards, so no explicit DESC index definition is needed.

No index is created on `response_json`, `detected_languages`, or
`target_language` since none of them are ever filtered or sorted on.

`media_type` distinguishes image OCR translations from video (speech +
on-screen text) translations. Both share this same table and the same
`response_json` shape at the top level (success/detected_languages/
target_language/translations/error) - only the individual translation
items differ (video items carry an extra "type": "speech" |
"on_screen_text" field), which is why a single JSONB column is enough
without a schema migration on `response_json` itself.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class MediaTypeEnum(str, enum.Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


class Translation(Base):
    __tablename__ = "translations"
    __table_args__ = (
        Index("ix_translations_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    media_type: Mapped[MediaTypeEnum] = mapped_column(
        Enum(MediaTypeEnum, name="media_type_enum", native_enum=True),
        nullable=False,
        default=MediaTypeEnum.IMAGE,
        server_default=MediaTypeEnum.IMAGE.value,
    )
    detected_languages: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    target_language: Mapped[str] = mapped_column(String(50), nullable=False)
    response_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="translations")

    def __repr__(self) -> str:
        return f"<Translation id={self.id} user_id={self.user_id} target={self.target_language!r}>"
