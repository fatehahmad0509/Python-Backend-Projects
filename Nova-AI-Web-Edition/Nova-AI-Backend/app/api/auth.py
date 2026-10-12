"""Authentication endpoints: register, login, refresh, and logout."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.limiter import rate_limit
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.services.auth_service import AuthService
from app.services.cache_service import CacheService, get_cache_service

router = APIRouter(prefix="/auth", tags=["auth"])

_AUTH_RATE_LIMIT = Depends(rate_limit("auth", limit=10, window_seconds=60, by="ip"))


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
) -> AuthService:
    return AuthService(
        user_repo=UserRepository(db),
        cache=cache,
    )


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_AUTH_RATE_LIMIT],
)
async def register(body: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> UserRead:
    """Create a new account."""
    user = await service.register(body.email, body.password)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenResponse, dependencies=[_AUTH_RATE_LIMIT])
async def login(body: LoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    """Validate credentials and return an access + refresh token pair."""
    access_token, refresh_token = await service.login(body.email, body.password)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=AccessTokenResponse, dependencies=[_AUTH_RATE_LIMIT])
async def refresh(body: RefreshRequest, service: AuthService = Depends(get_auth_service)) -> AccessTokenResponse:
    """Exchange a valid refresh token for a new access token."""
    access_token = await service.refresh(body.refresh_token)
    return AccessTokenResponse(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_AUTH_RATE_LIMIT])
async def logout(body: LogoutRequest, service: AuthService = Depends(get_auth_service)) -> None:
    """Revoke a refresh token, logging the user out of that session."""
    await service.logout(body.refresh_token)
