"""
Redis connection pool and client factory.

A single connection pool is shared across the application's lifetime.
Individual `Redis` client instances are cheap to create and simply borrow
connections from this pool, so a new instance can safely be created per
request without extra connection overhead.
"""

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

_pool: ConnectionPool = ConnectionPool.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    max_connections=50,
)


def get_redis_client() -> Redis:
    """Return a Redis client instance backed by the shared connection pool."""
    return Redis(connection_pool=_pool)
