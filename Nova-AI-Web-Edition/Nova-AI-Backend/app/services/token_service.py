"""Business logic for daily token-limit enforcement and usage recording.

Limits and plan names live in app.core.plans — this service never
hardcodes a number or plan string itself.
"""
import uuid

from app.core.exceptions import TokenLimitExceededError
from app.core.plans import get_daily_limit, get_daily_search_limit, is_unlimited
from app.models.user import User
from app.repositories.token_usage_repository import TokenUsageRepository


class TokenService:
    """Enforces daily token budgets and records Gemini usage per user."""

    # Effective allowance handed back for plans with no daily search cap
    # (currently just the developer plan). Only needs to be >= the max
    # number of web_search calls GeminiService will ever attempt in a
    # single turn (its retry loop caps at 3) — it does not need to be
    # (and, to avoid float/int overflow issues, must not be) infinite.
    _UNLIMITED_SEARCH_ALLOWANCE = 1_000

    def __init__(self, usage_repo: TokenUsageRepository):
        self._usage_repo = usage_repo

    async def check_limit(self, user: User, estimated_tokens: int) -> None:
        """Raise TokenLimitExceededError if this request would exceed today's budget.

        Developer-plan users bypass this check entirely.
        """
        if is_unlimited(user.plan):
            return

        daily_limit = get_daily_limit(user.plan)
        usage = await self._usage_repo.get_today(user.id)
        current_total = usage.total_tokens if usage is not None else 0

        if current_total + estimated_tokens > daily_limit:
            raise TokenLimitExceededError()

    async def get_search_allowance(self, user: User) -> int:
        """How many web searches the user may actually run *this turn*.

        This is the number of searches still left in today's quota, not
        just a yes/no gate: GeminiService's tool-call loop can invoke
        web_search more than once in a single turn (e.g. a question that
        needs two lookups), and passing only a boolean let a single turn
        run past the remaining quota as long as the user had at least one
        search left when the turn *started* — silently blowing past the
        daily cap. Returning the actual remaining count lets the caller
        cap real Tavily calls precisely at what's left, whether that's 0,
        1, or more. Developer-plan users get a large fixed allowance
        (there's no cap to compute against).
        """
        if is_unlimited(user.plan):
            return self._UNLIMITED_SEARCH_ALLOWANCE

        search_limit = get_daily_search_limit(user.plan)
        usage = await self._usage_repo.get_today(user.id)
        current_searches = usage.search_count if usage is not None else 0
        return max(0, int(search_limit - current_searches))

    async def can_search(self, user: User) -> bool:
        """Whether the user has at least one web search remaining today.

        Used to decide whether to offer the web_search tool to Gemini at
        all for this turn. Does NOT by itself cap how many searches run
        within that turn — see `get_search_allowance` for that.
        """
        return await self.get_search_allowance(user) > 0

    async def record_usage(
        self,
        user_id: uuid.UUID,
        prompt_tokens: int,
        completion_tokens: int,
        search_count: int = 0,
    ) -> None:
        """Persist a completed request's Gemini token usage for today."""
        await self._usage_repo.increment_today(user_id, prompt_tokens, completion_tokens, search_count)
