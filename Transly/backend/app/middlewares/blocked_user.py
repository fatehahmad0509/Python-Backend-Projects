"""
Blocked-user middleware.

The authoritative blocked check happens in `dependencies.auth.get_current_user`
against the database on every request. This middleware adds a cheap
fast-path in front of it: if a user was already flagged as blocked in Redis
(set by that same dependency), the request is rejected immediately, before
it reaches routing, dependency resolution, or the database.
"""

import logging

import jwt as pyjwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.constants.errors import ErrorCode
from app.database.redis import get_redis_client
from app.utils.jwt import decode_token

logger = logging.getLogger("transly.middleware.blocked_user")


class BlockedUserMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
            user_id = None
            try:
                payload = decode_token(token)
                user_id = payload.get("sub")
            except pyjwt.PyJWTError:
                # Malformed/expired tokens are handled downstream by the
                # actual auth dependency - this middleware only cares about
                # short-circuiting known-blocked users.
                user_id = None

            if user_id:
                redis = get_redis_client()
                is_blocked = await redis.get(f"blocked_user:{user_id}")
                if is_blocked is not None:
                    return JSONResponse(
                        status_code=403,
                        content={
                            "success": False,
                            "message": "This account has been blocked",
                            "error": {"code": ErrorCode.USER_BLOCKED, "details": None},
                        },
                    )

        return await call_next(request)
