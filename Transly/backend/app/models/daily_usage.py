"""
DailyUsage model.

Tracks how many translations a user has performed on a given calendar day,
split into `usage_count` (image translations) and `video_usage_count`
(video translations) since each has its own per-plan daily limit. No
counters are stored on the `users` table so quota data stays isolated
and easy to purge (see retention policy below).

Indexes:
- Composite unique index on (user_id, date): a user can only have a single
  usage record per day, and this is exactly how the row is looked up:

      WHERE user_id = ? AND date = CURRENT_DATE
"""

import uuid
from datetime import date as date_type

from sqlalchemy import Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class DailyUsage(Base):
    __tablename__ = "daily_usages"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_daily_usages_user_id_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # Separate counter for video translations - tracked independently from
    # `usage_count` (image translations) since the two features have their
    # own daily limits (see constants.plans.VIDEO_DAILY_LIMITS).
    video_usage_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    user: Mapped["User"] = relationship("User", back_populates="daily_usages")

    def __repr__(self) -> str:
        return f"<DailyUsage user_id={self.user_id} date={self.date} count={self.usage_count}>"
