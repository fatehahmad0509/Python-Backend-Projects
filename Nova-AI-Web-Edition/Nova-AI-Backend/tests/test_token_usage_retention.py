"""Tests for the daily_token_usage 48h retention policy."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.daily_token_usage import DailyTokenUsage
from app.models.user import User
from app.repositories.token_usage_repository import TokenUsageRepository

pytestmark = pytest.mark.asyncio


async def _make_user(session: AsyncSession) -> uuid.UUID:
    user = User(email=f"user-{uuid.uuid4().hex[:10]}@example.com", password_hash="x")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user.id


async def _make_usage_row(session: AsyncSession, user_id: uuid.UUID, created_at: datetime, day_offset: int):
    usage = DailyTokenUsage(
        user_id=user_id,
        date=(datetime.now(timezone.utc) - timedelta(days=day_offset)).date(),
        prompt_tokens=10,
        completion_tokens=10,
        total_tokens=20,
        request_count=1,
    )
    session.add(usage)
    await session.commit()
    # created_at has a server_default, so it must be overwritten explicitly
    # after the insert to simulate an "old" row for the test.
    await session.execute(
        update(DailyTokenUsage).where(DailyTokenUsage.id == usage.id).values(created_at=created_at)
    )
    await session.commit()
    await session.refresh(usage)
    return usage


async def test_delete_created_before_removes_only_old_rows(test_engine):
    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        user_id = await _make_user(session)

        now = datetime.now(timezone.utc)
        old_row = await _make_usage_row(session, user_id, now - timedelta(hours=50), day_offset=2)
        recent_row = await _make_usage_row(session, user_id, now - timedelta(hours=1), day_offset=0)

        repo = TokenUsageRepository(session)
        cutoff = now - timedelta(hours=48)
        deleted_count = await repo.delete_created_before(cutoff)

        assert deleted_count == 1

        remaining = await repo.get_for_date(user_id, recent_row.date)
        assert remaining is not None
        assert remaining.id == recent_row.id

        purged = await repo.get_for_date(user_id, old_row.date)
        assert purged is None


async def test_delete_created_before_noop_when_nothing_expired(test_engine):
    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        user_id = await _make_user(session)
        now = datetime.now(timezone.utc)
        await _make_usage_row(session, user_id, now - timedelta(hours=1), day_offset=0)

        repo = TokenUsageRepository(session)
        deleted_count = await repo.delete_created_before(now - timedelta(hours=48))

        assert deleted_count == 0
