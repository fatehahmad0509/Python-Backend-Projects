"""Redis cache service.

Cache keys:
    user:{id}:conversations       -> JSON list of a user's conversations
    conversation:{id}:messages    -> JSON list of a conversation's messages

TTL: 4 days for all cached entries. Callers are responsible for
invalidating the relevant keys whenever the underlying data changes.
"""
import json
from functools import lru_cache
from typing import Any

from redis.asyncio import ConnectionPool, Redis

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

CACHE_TTL_SECONDS = 4 * 24 * 60 * 60  # 4 days

_pool: ConnectionPool = ConnectionPool.from_url(settings.redis_url, decode_responses=True)


def user_conversations_key(user_id: str) -> str:
    return f"user:{user_id}:conversations"


def conversation_messages_key(conversation_id: str) -> str:
    return f"conversation:{conversation_id}:messages"


class CacheService:
    """Thin async wrapper around Redis used throughout the app."""

    def __init__(self, redis: Redis):
        self._redis = redis

    async def get_json(self, key: str) -> Any | None:
        try:
            raw = await self._redis.get(key)
        except Exception:
            logger.warning("Redis GET failed for key=%s", key, exc_info=True)
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Corrupt cache value for key=%s; ignoring", key)
            return None

    async def set_json(self, key: str, value: Any, ttl_seconds: int = CACHE_TTL_SECONDS) -> None:
        try:
            await self._redis.set(key, json.dumps(value, default=str), ex=ttl_seconds)
        except Exception:
            logger.warning("Redis SET failed for key=%s", key, exc_info=True)

    async def delete(self, *keys: str) -> None:
        if not keys:
            return
        try:
            await self._redis.delete(*keys)
        except Exception:
            logger.warning("Redis DELETE failed for keys=%s", keys, exc_info=True)

    async def increment_with_expiry(self, key: str, window_seconds: int) -> int:
        """Atomically increment a counter, setting its TTL on first increment.

        Used for fixed-window rate limiting.
        """
        try:
            pipe = self._redis.pipeline()
            pipe.incr(key, 1)
            pipe.expire(key, window_seconds, nx=True)
            results = await pipe.execute()
            return int(results[0])
        except Exception:
            logger.warning("Redis rate-limit counter failed for key=%s; failing open", key, exc_info=True)
            # Fail open: if Redis is unavailable, do not block traffic.
            return 0

    async def invalidate_user_conversations(self, user_id: str) -> None:
        await self.delete(user_conversations_key(user_id))

    async def invalidate_conversation_messages(self, conversation_id: str) -> None:
        await self.delete(conversation_messages_key(conversation_id))


@lru_cache
def _get_redis_client() -> Redis:
    return Redis(connection_pool=_pool)


def get_cache_service() -> CacheService:
    """FastAPI dependency returning a CacheService bound to the shared pool."""
    return CacheService(_get_redis_client())
