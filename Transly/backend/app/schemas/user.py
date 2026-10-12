"""
User-facing schemas. Never exposes `password_hash`.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import PlanEnum


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    username: str
    email: EmailStr
    plan: PlanEnum
    is_blocked: bool
    created_at: datetime

    # Daily translation quota snapshot. Not present on the User ORM model -
    # populated explicitly by whichever endpoint wants to expose it (see
    # GET /users/me). `daily_limit` / `translations_remaining_today` are
    # None for plans with no daily cap (e.g. DEVELOPER).
    daily_limit: int | None = None
    translations_used_today: int = 0
    translations_remaining_today: int | None = None

    # Same snapshot, for video translations (tracked separately - see
    # constants.plans.VIDEO_DAILY_LIMITS).
    video_daily_limit: int | None = None
    videos_used_today: int = 0
    videos_remaining_today: int | None = None
