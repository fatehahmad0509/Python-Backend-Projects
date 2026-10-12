"""
Plan-related constants.

There is no payment system - plan changes are applied manually in the
database by an operator.
"""

from app.models.user import PlanEnum

# Maximum translations allowed per calendar day, per plan.
# `None` means unlimited.
PLAN_DAILY_LIMITS: dict[PlanEnum, int | None] = {
    PlanEnum.FREE: 5,
    PlanEnum.PLUS: 25,
    PlanEnum.DEVELOPER: None,
}

# Maximum video translations allowed per calendar day, per plan. Kept
# separate (and much lower) than PLAN_DAILY_LIMITS because a video
# translation call is far more expensive (audio + visual understanding
# over up to a minute of footage) than a single-image OCR call.
VIDEO_DAILY_LIMITS: dict[PlanEnum, int | None] = {
    PlanEnum.FREE: 2,
    PlanEnum.PLUS: 5,
    PlanEnum.DEVELOPER: None,
}

# Daily usage rows older than this many days are purged whenever a usage
# record is created or updated (see services.usage_service).
DAILY_USAGE_RETENTION_DAYS = 10
