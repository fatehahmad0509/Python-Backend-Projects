"""
Dependency providers for the database session and the Redis client.
"""

from collections.abc import AsyncGenerator

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.redis import get_redis_client
from app.database.session import get_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a request-scoped async session. Commits automatically if the
    request completes without raising, rolls back otherwise.
    """
    async for session in get_session():
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_redis() -> Redis:
    """Yield a Redis client borrowed from the shared connection pool."""
    return get_redis_client()
