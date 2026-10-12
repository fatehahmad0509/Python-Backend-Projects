"""Utility for auto-generating a conversation title from its first message."""

_MAX_TITLE_LENGTH = 60


def generate_title(first_message: str) -> str:
    """Derive a short, human-readable title from the first user message.

    Simple, dependency-free truncation is used so title generation never
    fails or adds latency/cost via an extra LLM call.
    """
    cleaned = " ".join(first_message.strip().split())
    if not cleaned:
        return "New Conversation"
    if len(cleaned) <= _MAX_TITLE_LENGTH:
        return cleaned
    return cleaned[:_MAX_TITLE_LENGTH].rsplit(" ", 1)[0].rstrip(",.;:!?") + "…"
