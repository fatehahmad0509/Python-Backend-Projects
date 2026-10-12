"""Data access layer for DailyTokenUsage."""
import uuid
from datetime import date as date_type
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_token_usage import DailyTokenUsage


class TokenUsageRepository:
    """Encapsulates all direct database access for daily token usage."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_for_date(self, user_id: uuid.UUID, on_date: date_type) -> DailyTokenUsage | None:
        result = await self._db.execute(
            select(DailyTokenUsage).where(
                DailyTokenUsage.user_id == user_id, DailyTokenUsage.date == on_date
            )
        )
        return result.scalar_one_or_none()

    async def get_today(self, user_id: uuid.UUID) -> DailyTokenUsage | None:
        return await self.get_for_date(user_id, date_type.today())

    async def increment_today(
        self,
        user_id: uuid.UUID,
        prompt_tokens: int,
        completion_tokens: int,
        search_count: int = 0,
    ) -> DailyTokenUsage:
        """Add usage to today's row for a user, creating it if needed.

        Handles the race where two concurrent requests both try to create
        today's row for the same user by falling back to an update.
        """
        today = date_type.today()
        total = prompt_tokens + completion_tokens

        usage = await self.get_for_date(user_id, today)
        if usage is not None:
            usage.prompt_tokens += prompt_tokens
            usage.completion_tokens += completion_tokens
            usage.total_tokens += total
            usage.request_count += 1
            usage.search_count += search_count
            self._db.add(usage)
            await self._db.commit()
            await self._db.refresh(usage)
            return usage

        usage = DailyTokenUsage(
            user_id=user_id,
            date=today,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            request_count=1,
            search_count=search_count,
        )
        self._db.add(usage)
        try:
            await self._db.commit()
        except IntegrityError:
            # Another concurrent request created today's row first.
            await self._db.rollback()
            usage = await self.get_for_date(user_id, today)
            usage.prompt_tokens += prompt_tokens
            usage.completion_tokens += completion_tokens
            usage.total_tokens += total
            usage.request_count += 1
            usage.search_count += search_count
            self._db.add(usage)
            await self._db.commit()

        await self._db.refresh(usage)
        return usage

    async def delete_created_before(self, cutoff: datetime) -> int:
        """Delete every row created before `cutoff`.

        Used by the retention job to purge rows older than the configured
        retention window (48h). Returns the number of rows deleted.
        """
        result = await self._db.execute(
            delete(DailyTokenUsage)
            .where(DailyTokenUsage.created_at < cutoff)
            .execution_options(synchronize_session=False)
        )
        await self._db.commit()
        return result.rowcount or 0
