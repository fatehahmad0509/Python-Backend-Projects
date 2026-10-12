"""
Translation service.

Orchestrates the full translate-image flow:
1. Validate the uploaded image.
2. Enforce/consume the user's daily quota.
3. Call Gemini Vision through GeminiService.
4. Persist the result and invalidate the user's cached history.

Also orchestrates the equivalent translate-video flow (validate ->
enforce the separate video quota -> call Gemini -> persist with
media_type=VIDEO), and owns the paginated + cached history read path
(shared across both media types) and history deletion.
"""

import logging
import uuid

from fastapi import UploadFile

from app.models.translation import MediaTypeEnum, Translation
from app.models.user import User
from app.repositories.translation_repository import TranslationRepository
from app.schemas.common import PaginationMeta
from app.schemas.translation import (
    PaginatedTranslationHistory,
    TranslationHistoryItem,
    TranslationResult,
    VideoTranslationResult,
)
from app.services.cache_service import CacheService
from app.services.gemini_service import GeminiService
from app.services.usage_service import UsageService
from app.utils.image_validator import validate_image
from app.utils.video_validator import validate_video

logger = logging.getLogger("transly.translation_service")

_MIME_TYPES = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


class TranslationService:
    def __init__(
        self,
        translation_repository: TranslationRepository,
        usage_service: UsageService,
        gemini_service: GeminiService,
        cache_service: CacheService,
    ) -> None:
        self._translation_repository = translation_repository
        self._usage_service = usage_service
        self._gemini_service = gemini_service
        self._cache_service = cache_service

    async def translate_image(
        self, user: User, image: UploadFile, target_language: str
    ) -> TranslationResult:
        image_bytes = await image.read()
        pil_image = validate_image(image_bytes)
        mime_type = _MIME_TYPES.get(pil_image.format or "", "image/jpeg")

        # Quota is checked and consumed before calling Gemini so that users
        # who are already over their limit never trigger a paid API call.
        await self._usage_service.check_and_consume_quota(user.id, user.plan)

        result = await self._gemini_service.translate_image(image_bytes, mime_type, target_language)

        translation = Translation(
            user_id=user.id,
            media_type=MediaTypeEnum.IMAGE,
            detected_languages=result.detected_languages,
            target_language=result.target_language,
            response_json=result.model_dump(),
        )
        await self._translation_repository.create(translation)
        await self._cache_service.invalidate_history(user.id)

        return result

    async def translate_video(
        self, user: User, video: UploadFile, target_language: str
    ) -> VideoTranslationResult:
        video_bytes = await video.read()
        mime_type = await validate_video(video_bytes)

        # Same ordering as translate_image: quota is checked and consumed
        # against the video-specific limit before calling Gemini.
        await self._usage_service.check_and_consume_quota(
            user.id, user.plan, media_type=MediaTypeEnum.VIDEO
        )

        result = await self._gemini_service.translate_video(video_bytes, mime_type, target_language)

        translation = Translation(
            user_id=user.id,
            media_type=MediaTypeEnum.VIDEO,
            detected_languages=result.detected_languages,
            target_language=result.target_language,
            response_json=result.model_dump(),
        )
        await self._translation_repository.create(translation)
        await self._cache_service.invalidate_history(user.id)

        return result

    async def get_history(
        self, user_id: uuid.UUID, page: int, page_size: int
    ) -> PaginatedTranslationHistory:
        cached = await self._cache_service.get_history(user_id, page, page_size)
        if cached is not None:
            logger.info("cache HIT user=%s page=%s page_size=%s", user_id, page, page_size)
            return PaginatedTranslationHistory.model_validate(cached)

        logger.info("cache MISS user=%s page=%s page_size=%s", user_id, page, page_size)
        items, total_items = await self._translation_repository.get_paginated_by_user(
            user_id, page, page_size
        )
        total_pages = (total_items + page_size - 1) // page_size if page_size else 0

        response = PaginatedTranslationHistory(
            items=[TranslationHistoryItem.model_validate(item) for item in items],
            pagination=PaginationMeta(
                page=page,
                page_size=page_size,
                total_items=total_items,
                total_pages=total_pages,
            ),
        )

        await self._cache_service.set_history(
            user_id, page, page_size, response.model_dump(mode="json")
        )
        return response

    async def delete_history(self, user_id: uuid.UUID) -> None:
        await self._translation_repository.delete_all_by_user(user_id)
        await self._cache_service.invalidate_history(user_id)
