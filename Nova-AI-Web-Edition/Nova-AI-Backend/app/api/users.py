"""User-related endpoints, including account deletion."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.plans import get_daily_limit, get_daily_search_limit, is_unlimited
from app.db.session import get_db
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.token_usage_repository import TokenUsageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.account import DeleteAccountRequest
from app.schemas.common import MessageResponse
from app.schemas.user import UsageRead, UserDetailsUpdate, UserRead
from app.services.account_service import AccountService
from app.services.cache_service import CacheService, get_cache_service

router = APIRouter(prefix="/users", tags=["users"])


def get_account_service(
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
) -> AccountService:
    return AccountService(
        user_repo=UserRepository(db),
        conversation_repo=ConversationRepository(db),
        cache=cache,
    )


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_token_usage_repository(db: AsyncSession = Depends(get_db)) -> TokenUsageRepository:
    return TokenUsageRepository(db)


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    """Return the currently authenticated user's profile."""
    return UserRead.model_validate(current_user)


@router.get("/me/usage", response_model=UsageRead)
async def get_my_usage(
    current_user: User = Depends(get_current_user),
    usage_repo: TokenUsageRepository = Depends(get_token_usage_repository),
) -> UsageRead:
    """Return today's token/search usage for the current user alongside their plan limits."""
    usage = await usage_repo.get_today(current_user.id)
    unlimited = is_unlimited(current_user.plan)

    return UsageRead(
        plan=current_user.plan,
        tokens_used_today=usage.total_tokens if usage is not None else 0,
        token_limit=None if unlimited else int(get_daily_limit(current_user.plan)),
        searches_used_today=usage.search_count if usage is not None else 0,
        search_limit=None if unlimited else int(get_daily_search_limit(current_user.plan)),
    )


@router.put("/me/details", response_model=UserRead)
async def update_my_details(
    body: UserDetailsUpdate,
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserRead:
    """Set or update the free-form info Nova uses to personalize replies.

    Send an empty string to clear it.
    """
    updated_user = await user_repo.update_details(current_user, body.details)
    return UserRead.model_validate(updated_user)


@router.delete("/me", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def delete_me(
    body: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    service: AccountService = Depends(get_account_service),
) -> MessageResponse:
    """Permanently delete the account and all associated data."""
    await service.delete_account(current_user, body.password)
    return MessageResponse(message="Your account and all associated data have been deleted.")
