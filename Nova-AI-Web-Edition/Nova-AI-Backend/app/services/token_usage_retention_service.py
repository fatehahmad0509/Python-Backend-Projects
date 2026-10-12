"""Retention policy for DailyTokenUsage rows.

daily_token_usage previously grew without bound: the daily-limit check
only ever reads today's row, so nothing was reading (or deleting) old
rows once the day had passed. This module purges rows 48 hours after
they were created so the table doesn't accumulate indefinitely, while
keeping a full extra day of history around a calendar-day boundary as
a safety margin.
"""
import asyncio
from datetime import datetime, timedelta, timezone

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.repositories.token_usage_repository import TokenUsageRepository

logger = get_logger(__name__)

RETENTION_WINDOW = timedelta(hours=48)
CLEANUP_INTERVAL_SECONDS = 60 * 60  # run once an hour


async def purge_expired_token_usage() -> int:
    """Delete daily_token_usage rows created more than 48h ago.

    Opens its own short-lived session so it can be called from a
    background task that isn't tied to any HTTP request.
    """
    cutoff = datetime.now(timezone.utc) - RETENTION_WINDOW
    async with AsyncSessionLocal() as db:
        repo = TokenUsageRepository(db)
        deleted = await repo.delete_created_before(cutoff)

    if deleted:
        logger.info("Purged %d daily_token_usage row(s) older than 48h", deleted)
    return deleted


async def run_token_usage_retention_loop() -> None:
    """Background loop: purge expired rows once an hour until cancelled."""
    logger.info(
        "Starting daily_token_usage retention loop (interval=%ds, window=48h)",
        CLEANUP_INTERVAL_SECONDS,
    )
    while True:
        try:
            await purge_expired_token_usage()
        except asyncio.CancelledError:
            raise
        except Exception:
            # Never let a transient DB hiccup kill the background loop.
            logger.exception("daily_token_usage retention job failed; will retry next cycle")

        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
