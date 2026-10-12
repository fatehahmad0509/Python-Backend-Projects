"""
Usage repository.

Encapsulates all direct database access for the `DailyUsage` model,
including the retention cleanup query.
"""

import uuid
from datetime import date, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.plans import DAILY_USAGE_RETENTION_DAYS
from app.models.daily_usage import DailyUsage
from app.models.translation import MediaTypeEnum


class UsageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_today_usage(
        self, user_id: uuid.UUID, today: date, for_update: bool = False
    ) -> DailyUsage | None:
        stmt = select(DailyUsage).where(
            DailyUsage.user_id == user_id, DailyUsage.date == today
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_usage(self, user_id: uuid.UUID, today: date) -> DailyUsage:
        usage = DailyUsage(user_id=user_id, date=today, usage_count=0, video_usage_count=0)
        self._session.add(usage)
        await self._session.flush()
        await self._session.refresh(usage)
        return usage

    async def increment_usage(
        self, usage: DailyUsage, media_type: MediaTypeEnum = MediaTypeEnum.IMAGE
    ) -> DailyUsage:
        if media_type == MediaTypeEnum.VIDEO:
            usage.video_usage_count += 1
        else:
            usage.usage_count += 1
        await self._session.flush()
        await self._session.refresh(usage)
        return usage

    async def delete_older_than(self, cutoff_date: date) -> None:
        await self._session.execute(delete(DailyUsage).where(DailyUsage.date < cutoff_date))

    @staticmethod
    def retention_cutoff(today: date) -> date:
        return today - timedelta(days=DAILY_USAGE_RETENTION_DAYS)
