"""
Cache service.

Wraps every Redis interaction used by the application:
- Translation history caching (24h TTL, invalidated on write/delete).
- Blocked-user flag caching (used by the blocked-user middleware fast path).
- Refresh token tracking (enables refresh token rotation and revocation).
"""

import json
import uuid

from redis.asyncio import Redis

HISTORY_CACHE_TTL_SECONDS = 60 * 60 * 24  # 24 hours


class CacheService:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    # ------------------------------------------------------------------
    # Translation history cache
    # ------------------------------------------------------------------

    @staticmethod
    def _history_key(user_id: uuid.UUID, page: int, page_size: int) -> str:
        return f"history:{user_id}:{page}:{page_size}"

    @staticmethod
    def _history_index_key(user_id: uuid.UUID) -> str:
        return f"history_keys:{user_id}"

    async def get_history(self, user_id: uuid.UUID, page: int, page_size: int) -> dict | None:
        cached = await self._redis.get(self._history_key(user_id, page, page_size))
        return json.loads(cached) if cached is not None else None

    async def set_history(
        self, user_id: uuid.UUID, page: int, page_size: int, payload: dict
    ) -> None:
        key = self._history_key(user_id, page, page_size)
        await self._redis.set(key, json.dumps(payload, default=str), ex=HISTORY_CACHE_TTL_SECONDS)

        # Track every cache key created for this user so it can be fully
        # invalidated later without relying on a KEYS/SCAN pattern match.
        index_key = self._history_index_key(user_id)
        await self._redis.sadd(index_key, key)
        await self._redis.expire(index_key, HISTORY_CACHE_TTL_SECONDS)

    async def invalidate_history(self, user_id: uuid.UUID) -> None:
        index_key = self._history_index_key(user_id)
        keys = await self._redis.smembers(index_key)
        if keys:
            await self._redis.delete(*keys)
        await self._redis.delete(index_key)

    # ------------------------------------------------------------------
    # Blocked-user flag (used by middlewares.blocked_user)
    # ------------------------------------------------------------------

    async def mark_user_blocked(self, user_id: uuid.UUID, ttl_seconds: int = 300) -> None:
        await self._redis.set(f"blocked_user:{user_id}", "1", ex=ttl_seconds)

    async def unmark_user_blocked(self, user_id: uuid.UUID) -> None:
        await self._redis.delete(f"blocked_user:{user_id}")

    # ------------------------------------------------------------------
    # Refresh token tracking (rotation / revocation)
    # ------------------------------------------------------------------

    async def store_refresh_token(self, jti: str, user_id: uuid.UUID, ttl_seconds: int) -> None:
        await self._redis.set(f"refresh_token:{jti}", str(user_id), ex=ttl_seconds)

    async def get_refresh_token_owner(self, jti: str) -> str | None:
        return await self._redis.get(f"refresh_token:{jti}")

    async def revoke_refresh_token(self, jti: str) -> None:
        await self._redis.delete(f"refresh_token:{jti}")
