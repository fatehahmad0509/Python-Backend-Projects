"""
Authentication dependencies.

`get_current_user` is the single source of truth for "who is making this
request": it decodes and validates the access token, loads the user from
the database, and rejects the request if the account is blocked. This is
also where the Redis blocked-user flag gets (re)populated, which is what
lets `middlewares.blocked_user` short-circuit future requests cheaply.
"""

import uuid

import jwt as pyjwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db, get_redis
from app.exceptions.custom_exceptions import AuthenticationException, ForbiddenException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.cache_service import CacheService
from app.utils.jwt import decode_token

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User:
    if credentials is None:
        raise AuthenticationException("Missing authentication credentials")

    try:
        payload = decode_token(credentials.credentials)
    except pyjwt.PyJWTError as exc:
        raise AuthenticationException("Invalid or expired access token") from exc

    if payload.get("type") != "access":
        raise AuthenticationException("Invalid token type")

    user_id = payload.get("sub")
    user_repository = UserRepository(db)
    user = await user_repository.get_by_id(uuid.UUID(user_id))
    if user is None:
        raise AuthenticationException("User no longer exists")

    if user.is_blocked:
        cache_service = CacheService(redis)
        await cache_service.mark_user_blocked(user.id)
        raise ForbiddenException("This account has been blocked")

    return user


async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """Alias kept separate from get_current_user so extra checks (e.g. plan
    gating) can be layered on in the future without touching every router."""
    return user
