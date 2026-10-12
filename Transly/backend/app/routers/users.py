"""
Users router.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.plans import PLAN_DAILY_LIMITS, VIDEO_DAILY_LIMITS
from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.usage_repository import UsageRepository
from app.schemas.common import StandardResponse
from app.schemas.user import UserResponse
from app.services.usage_service import UsageService

router = APIRouter(prefix="/users", tags=["Users"])


def get_usage_service(db: AsyncSession = Depends(get_db)) -> UsageService:
    return UsageService(UsageRepository(db))


@router.get(
    "/me",
    response_model=StandardResponse[UserResponse],
    summary="Get the currently authenticated user's profile",
)
async def get_profile(
    user: User = Depends(get_current_active_user),
    usage_service: UsageService = Depends(get_usage_service),
) -> StandardResponse[UserResponse]:
    used_today = await usage_service.get_today_usage_count(user.id)
    daily_limit = PLAN_DAILY_LIMITS.get(user.plan)
    remaining_today = None if daily_limit is None else max(daily_limit - used_today, 0)

    videos_used_today = await usage_service.get_today_video_usage_count(user.id)
    video_daily_limit = VIDEO_DAILY_LIMITS.get(user.plan)
    videos_remaining_today = (
        None if video_daily_limit is None else max(video_daily_limit - videos_used_today, 0)
    )

    profile = UserResponse.model_validate(user).model_copy(
        update={
            "daily_limit": daily_limit,
            "translations_used_today": used_today,
            "translations_remaining_today": remaining_today,
            "video_daily_limit": video_daily_limit,
            "videos_used_today": videos_used_today,
            "videos_remaining_today": videos_remaining_today,
        }
    )
    return StandardResponse(message="Success", data=profile)
