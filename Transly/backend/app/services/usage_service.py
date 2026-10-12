"""
Usage service.

Owns all business logic around daily translation quotas:
- Lazily creates today's usage record on first use (no reset jobs needed).
- Enforces per-plan daily limits, separately for image and video
  translations (see constants.plans.PLAN_DAILY_LIMITS vs
  VIDEO_DAILY_LIMITS).
- Purges usage records older than the retention window on every write,
  as required (no separate cron job).
"""

import uuid
from datetime import date as date_type
from datetime import datetime, timezone

from app.constants.plans import PLAN_DAILY_LIMITS, VIDEO_DAILY_LIMITS
from app.exceptions.custom_exceptions import UsageLimitExceededException
from app.models.daily_usage import DailyUsage
from app.models.translation import MediaTypeEnum
from app.models.user import PlanEnum
from app.repositories.usage_repository import UsageRepository


class UsageService:
    def __init__(self, usage_repository: UsageRepository) -> None:
        self._usage_repository = usage_repository

    @staticmethod
    def _today() -> date_type:
        return datetime.now(timezone.utc).date()

    async def _get_or_create_today_usage(
        self, user_id: uuid.UUID, for_update: bool = False
    ) -> DailyUsage:
        today = self._today()
        usage = await self._usage_repository.get_today_usage(user_id, today, for_update=for_update)
        if usage is None:
            usage = await self._usage_repository.create_usage(user_id, today)
        return usage

    async def _cleanup_old_records(self) -> None:
        cutoff = self._usage_repository.retention_cutoff(self._today())
        await self._usage_repository.delete_older_than(cutoff)

    async def check_and_consume_quota(
        self,
        user_id: uuid.UUID,
        plan: PlanEnum,
        media_type: MediaTypeEnum = MediaTypeEnum.IMAGE,
    ) -> DailyUsage:
        """
        Validate that the user still has quota left today for the given
        media type, then atomically consume one unit of quota. Raises
        UsageLimitExceededException when the daily limit for the user's
        plan has already been reached.
        """
        usage = await self._get_or_create_today_usage(user_id, for_update=True)

        if media_type == MediaTypeEnum.VIDEO:
            daily_limit = VIDEO_DAILY_LIMITS.get(plan)
            current_count = usage.video_usage_count
        else:
            daily_limit = PLAN_DAILY_LIMITS.get(plan)
            current_count = usage.usage_count

        if daily_limit is not None and current_count >= daily_limit:
            kind = "video" if media_type == MediaTypeEnum.VIDEO else "image"
            raise UsageLimitExceededException(
                f"Daily {kind} translation limit of {daily_limit} reached for the {plan.value} plan",
                {"limit": daily_limit, "plan": plan.value, "media_type": media_type.value},
            )

        usage = await self._usage_repository.increment_usage(usage, media_type)

        # Required retention policy: keep only the last N days of usage
        # history. Runs inline instead of a separate scheduled job.
        await self._cleanup_old_records()

        return usage

    async def get_today_usage_count(self, user_id: uuid.UUID) -> int:
        usage = await self._usage_repository.get_today_usage(user_id, self._today())
        return usage.usage_count if usage else 0

    async def get_today_video_usage_count(self, user_id: uuid.UUID) -> int:
        usage = await self._usage_repository.get_today_usage(user_id, self._today())
        return usage.video_usage_count if usage else 0
