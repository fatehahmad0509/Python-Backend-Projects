"""
JWT creation and decoding utilities.

Two token types are issued:
- access:  short-lived, sent with every authenticated request.
- refresh: long-lived, exchanged for a new access/refresh token pair via
           POST /auth/refresh. Each refresh token carries a unique `jti`
           which is tracked in Redis (see services.cache_service) so it can
           be individually revoked/rotated - a compromised refresh token
           can be invalidated without invalidating every user's tokens.
"""

import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

import jwt

from app.core.config import settings


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": TokenType.ACCESS.value,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> tuple[str, str, datetime]:
    """Create a refresh token. Returns (token, jti, expires_at)."""
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": TokenType.REFRESH.value,
        "jti": jti,
        "iat": now,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expire


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
