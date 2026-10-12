"""
User model.

Indexes:
- Unique index on `email` (login lookups use email).
- Unique index on `username` (uniqueness validation during registration).
- Primary key index on `id` is created automatically by PostgreSQL.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PlanEnum(str, enum.Enum):
    FREE = "FREE"
    PLUS = "PLUS"
    DEVELOPER = "DEVELOPER"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[PlanEnum] = mapped_column(
        Enum(PlanEnum, name="plan_enum", native_enum=True),
        nullable=False,
        default=PlanEnum.FREE,
        server_default=PlanEnum.FREE.value,
    )
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    translations: Mapped[list["Translation"]] = relationship(
        "Translation", back_populates="user", cascade="all, delete-orphan"
    )
    daily_usages: Mapped[list["DailyUsage"]] = relationship(
        "DailyUsage", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} plan={self.plan}>"
