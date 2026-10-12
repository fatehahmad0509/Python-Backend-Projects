"""
Rate limiting middleware.

A simple, effective fixed-window rate limiter backed by Redis. Requests
are keyed by authenticated user (when a bearer token is present) or by
client IP otherwise, and are limited within a rolling 60-second window.
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.constants.errors import ErrorCode
from app.core.config import settings
from app.database.redis import get_redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        redis = get_redis_client()
        identifier = self._resolve_identifier(request)
        window = int(time.time() // 60)
        key = f"rate_limit:{identifier}:{window}"

        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, 60)

        if current > settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Too many requests. Please try again later.",
                    "error": {"code": ErrorCode.RATE_LIMIT_EXCEEDED, "details": None},
                },
            )

        return await call_next(request)

    @staticmethod
    def _resolve_identifier(request: Request) -> str:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Hash instead of storing the raw token as a Redis key.
            return f"token:{hash(auth_header)}"
        client = request.client
        return f"ip:{client.host}" if client else "ip:unknown"
