"""
Auth service.

Owns all authentication business logic: registration, login, and the
refresh token exchange/rotation flow. Routers only translate HTTP requests
into calls on this service - they contain no business logic themselves.
"""

import uuid

import jwt as pyjwt

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.exceptions.custom_exceptions import (
    AuthenticationException,
    ConflictException,
    ForbiddenException,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.cache_service import CacheService
from app.utils.jwt import create_access_token, create_refresh_token, decode_token


class AuthService:
    def __init__(self, user_repository: UserRepository, cache_service: CacheService) -> None:
        self._user_repository = user_repository
        self._cache_service = cache_service

    async def register(self, payload: RegisterRequest) -> User:
        if await self._user_repository.get_by_email(payload.email):
            raise ConflictException(
                "An account with this email already exists", {"field": "email"}
            )
        if await self._user_repository.get_by_username(payload.username):
            raise ConflictException(
                "This username is already taken", {"field": "username"}
            )

        user = User(
            full_name=payload.full_name,
            username=payload.username,
            email=payload.email,
            password_hash=hash_password(payload.password),
        )
        return await self._user_repository.create(user)

    async def _issue_tokens(self, user_id: uuid.UUID) -> TokenResponse:
        access_token = create_access_token(str(user_id))
        refresh_token, jti, _expire = create_refresh_token(str(user_id))

        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        await self._cache_service.store_refresh_token(jti, user_id, ttl_seconds)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self._user_repository.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise AuthenticationException("Invalid email or password")

        if user.is_blocked:
            raise ForbiddenException("This account has been blocked")

        return await self._issue_tokens(user.id)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except pyjwt.PyJWTError as exc:
            raise AuthenticationException("Invalid or expired refresh token") from exc

        if payload.get("type") != "refresh":
            raise AuthenticationException("Invalid token type")

        jti = payload.get("jti")
        user_id = payload.get("sub")

        stored_owner = await self._cache_service.get_refresh_token_owner(jti)
        if stored_owner is None or stored_owner != str(user_id):
            raise AuthenticationException("Refresh token has been revoked or has expired")

        user = await self._user_repository.get_by_id(uuid.UUID(user_id))
        if user is None:
            raise AuthenticationException("User no longer exists")
        if user.is_blocked:
            raise ForbiddenException("This account has been blocked")

        # Rotate: the old refresh token is revoked as soon as it is used,
        # and a brand-new access/refresh pair is issued.
        await self._cache_service.revoke_refresh_token(jti)
        return await self._issue_tokens(user.id)
