"""Redis-backed fixed-window rate limiting.

Usage as a FastAPI dependency:

    @router.post("/login", dependencies=[Depends(rate_limit("auth:login", limit=10, window_seconds=60, by="ip"))])
    @router.post("/chat", dependencies=[Depends(rate_limit("chat", limit=20, window_seconds=60, by="user"))])
"""
from collections.abc import Callable

from fastapi import Depends, Request

from app.core.exceptions import RateLimitError
from app.services.cache_service import CacheService, get_cache_service


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _enforce(cache: CacheService, key: str, limit: int, window_seconds: int, scope: str) -> None:
    current = await cache.increment_with_expiry(key, window_seconds)
    if current > limit:
        raise RateLimitError(f"Rate limit exceeded for {scope}. Try again later.")


def rate_limit(scope: str, limit: int, window_seconds: int, by: str = "ip") -> Callable:
    """Return a FastAPI dependency enforcing `limit` requests per `window_seconds`.

    `by="ip"`   -> limited per client IP address (auth endpoints).
    `by="user"` -> limited per authenticated user id (chat endpoint). This
                   variant depends on get_current_user so the user is
                   resolved (and cached by FastAPI for the request) once.
    """
    if by == "user":
        # Imported lazily to avoid a module-level circular import between
        # core.limiter and core.dependencies.
        from app.core.dependencies import get_current_user
        from app.models.user import User

        async def dependency_by_user(
            current_user: User = Depends(get_current_user),
            cache: CacheService = Depends(get_cache_service),
        ) -> None:
            key = f"ratelimit:{scope}:{current_user.id}"
            await _enforce(cache, key, limit, window_seconds, scope)

        return dependency_by_user

    async def dependency_by_ip(
        request: Request,
        cache: CacheService = Depends(get_cache_service),
    ) -> None:
        key = f"ratelimit:{scope}:{_client_ip(request)}"
        await _enforce(cache, key, limit, window_seconds, scope)

    return dependency_by_ip
