"""Central definition of subscription plans and their daily token limits.

This is the single source of truth for plan names and limits — nothing
else in the codebase should hardcode a plan string or a token number.
"""
from typing import Final

PLAN_FREE: Final[str] = "free"
PLAN_PLUS: Final[str] = "plus"
PLAN_PRO: Final[str] = "pro"
PLAN_DEVELOPER: Final[str] = "developer"

PLAN_CHOICES: Final[tuple[str, ...]] = (PLAN_FREE, PLAN_PLUS, PLAN_PRO, PLAN_DEVELOPER)

DEFAULT_PLAN: Final[str] = PLAN_FREE

TOKEN_LIMITS: Final[dict[str, float]] = {
    # Free: 2x the original 15k. Plus/Pro: 1.5x their original 40k/80k.
    # These MUST match what SettingsPage.tsx advertises to users ("30k
    # token/day", "60k token/day", "120k token/day") — see the SEARCH_LIMITS
    # comment below for why that sync matters.
    PLAN_FREE: 30_000,
    PLAN_PLUS: 60_000,
    PLAN_PRO: 120_000,
    PLAN_DEVELOPER: float("inf"),
}

SEARCH_LIMITS: Final[dict[str, float]] = {
    # These MUST match what SettingsPage.tsx advertises to users ("1 web
    # search/day", "5 web search/day", "20 web search/day") — they had
    # drifted out of sync (this dict used to say 5/10/20), which meant the
    # daily quota was being enforced correctly against the WRONG numbers:
    # a free-plan user really did have 5 searches/day even though the UI
    # told them they only had 1, so testers who took the UI at its word
    # saw what looked like a broken limit.
    PLAN_FREE: 1,
    PLAN_PLUS: 5,
    PLAN_PRO: 20,
    PLAN_DEVELOPER: float("inf"),
}


def get_daily_search_limit(plan: str) -> float:
    """Return the daily web-search limit for a plan (unknown plans fall back to free)."""
    return SEARCH_LIMITS.get(plan, SEARCH_LIMITS[PLAN_FREE])


def get_daily_limit(plan: str) -> float:
    """Return the daily token limit for a plan (unknown plans fall back to free)."""
    return TOKEN_LIMITS.get(plan, TOKEN_LIMITS[PLAN_FREE])


def is_unlimited(plan: str) -> bool:
    """Whether a plan has no daily token limit."""
    return plan == PLAN_DEVELOPER
