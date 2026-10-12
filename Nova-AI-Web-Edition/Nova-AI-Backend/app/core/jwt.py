"""JWT creation and verification helpers."""
import uuid
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any

import jwt
from jwt import PyJWTError

from app.config import settings


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenError(Exception):
    """Raised when a token is invalid, expired, or malformed."""


def _create_token(subject: str, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str) -> str:
    """Create a short-lived access token (default 1 day)."""
    return _create_token(
        user_id,
        TokenType.ACCESS,
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived refresh token (default 30 days)."""
    return _create_token(
        user_id,
        TokenType.REFRESH,
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    """Decode and validate a JWT, ensuring it matches the expected type.

    Raises TokenError if the token is invalid, expired, or the wrong type.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except PyJWTError as exc:
        raise TokenError("Invalid or expired token") from exc

    if payload.get("type") != expected_type.value:
        raise TokenError("Incorrect token type")

    return payload
