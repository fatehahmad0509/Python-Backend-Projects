"""
Translation router.

Contains no business logic. Image/video validation, quota checks, the
Gemini call, persistence, and caching all happen inside
TranslationService and its collaborators.
"""

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db, get_redis
from app.models.user import User
from app.repositories.translation_repository import TranslationRepository
from app.repositories.usage_repository import UsageRepository
from app.schemas.common import StandardResponse
from app.schemas.translation import (
    PaginatedTranslationHistory,
    TranslationResult,
    VideoTranslationResult,
)
from app.services.cache_service import CacheService
from app.services.gemini_service import GeminiService
from app.services.translation_service import TranslationService
from app.services.usage_service import UsageService

router = APIRouter(tags=["Translations"])

# GeminiService holds a long-lived API client - a single instance is shared
# across requests instead of being recreated per-request.
_gemini_service = GeminiService()


def get_translation_service(
    db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
) -> TranslationService:
    return TranslationService(
        translation_repository=TranslationRepository(db),
        usage_service=UsageService(UsageRepository(db)),
        gemini_service=_gemini_service,
        cache_service=CacheService(redis),
    )


@router.post(
    "/translate/image",
    response_model=StandardResponse[TranslationResult],
    summary="Translate all text found in an uploaded image",
)
async def translate_image(
    target_language: str,
    image: UploadFile = File(...),
    user: User = Depends(get_current_active_user),
    translation_service: TranslationService = Depends(get_translation_service),
) -> StandardResponse[TranslationResult]:
    result = await translation_service.translate_image(user, image, target_language)
    return StandardResponse(message="Image translated successfully", data=result)


@router.post(
    "/translate/video",
    response_model=StandardResponse[VideoTranslationResult],
    summary="Translate speech and on-screen text found in an uploaded video (max 60s)",
)
async def translate_video(
    target_language: str,
    video: UploadFile = File(...),
    user: User = Depends(get_current_active_user),
    translation_service: TranslationService = Depends(get_translation_service),
) -> StandardResponse[VideoTranslationResult]:
    result = await translation_service.translate_video(user, video, target_language)
    return StandardResponse(message="Video translated successfully", data=result)


@router.get(
    "/translations/history",
    response_model=StandardResponse[PaginatedTranslationHistory],
    summary="Get the current user's paginated translation history",
)
async def get_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_active_user),
    translation_service: TranslationService = Depends(get_translation_service),
) -> StandardResponse[PaginatedTranslationHistory]:
    history = await translation_service.get_history(user.id, page, page_size)
    return StandardResponse(message="Success", data=history)


@router.delete(
    "/translations/history",
    response_model=StandardResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete all of the current user's translation history",
)
async def delete_history(
    user: User = Depends(get_current_active_user),
    translation_service: TranslationService = Depends(get_translation_service),
) -> StandardResponse[None]:
    await translation_service.delete_history(user.id)
    return StandardResponse(message="Translation history deleted successfully", data=None)
