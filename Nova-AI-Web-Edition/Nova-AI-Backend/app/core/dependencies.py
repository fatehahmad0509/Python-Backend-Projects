"""Shared FastAPI dependencies (auth, current user, etc.)."""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AccountBlockedError, UnauthorizedError
from app.core.jwt import TokenError, TokenType, decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a Bearer access token.

    Raises UnauthorizedError (401) if the token is missing, invalid,
    expired, or does not correspond to an existing user. Raises
    AccountBlockedError (403) if the user has been blocked — this single
    choke point covers every endpoint that depends on it (chat,
    conversations, and the user endpoints).
    """
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Missing bearer token")

    try:
        payload = decode_token(credentials.credentials, TokenType.ACCESS)
    except TokenError:
        raise UnauthorizedError("Invalid or expired access token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("User no longer exists")

    if user.is_blocked:
        raise AccountBlockedError()

    return user
