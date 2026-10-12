"""
Authentication router.

Contains no business logic - every endpoint immediately delegates to
AuthService.
"""

from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db, get_redis
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.common import StandardResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.services.cache_service import CacheService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(
    db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
) -> AuthService:
    return AuthService(UserRepository(db), CacheService(redis))


@router.post(
    "/register",
    response_model=StandardResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> StandardResponse[UserResponse]:
    user = await auth_service.register(payload)
    return StandardResponse(
        message="Account created successfully",
        data=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=StandardResponse[TokenResponse],
    summary="Log in with email and password",
)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> StandardResponse[TokenResponse]:
    tokens = await auth_service.login(payload)
    return StandardResponse(message="Login successful", data=tokens)


@router.post(
    "/refresh",
    response_model=StandardResponse[TokenResponse],
    summary="Exchange a refresh token for a new access/refresh token pair",
)
async def refresh(
    payload: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> StandardResponse[TokenResponse]:
    tokens = await auth_service.refresh(payload.refresh_token)
    return StandardResponse(message="Token refreshed successfully", data=tokens)
