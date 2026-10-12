"""User ORM model."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, Text, func, text
from app.core.plans import DEFAULT_PLAN, PLAN_CHOICES
from app.db.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """A registered Nova AI user."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(f"plan IN {PLAN_CHOICES}", name="ck_users_plan_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    plan: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DEFAULT_PLAN, server_default=DEFAULT_PLAN
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # Free-form info the user shares about themselves (name, age, preferences,
    # etc.) so Nova can personalize replies. Sent to Gemini as context on
    # every chat turn.
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
