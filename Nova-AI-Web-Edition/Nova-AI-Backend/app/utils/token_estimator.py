"""Rough token-count estimation used only for pre-flight budget checks.

This does not need to be exact — it only needs to catch requests that
would clearly blow through the remaining daily budget before an
expensive Gemini call is made. The authoritative token count used to
record usage always comes from Gemini's own `usage_metadata`.
"""
_CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Approximate the token count of a single string."""
    if not text:
        return 0
    return max(1, len(text) // _CHARS_PER_TOKEN)


def estimate_tokens_for_messages(*texts: str) -> int:
    """Approximate the total token count across several strings."""
    return sum(estimate_tokens(t) for t in texts if t)
