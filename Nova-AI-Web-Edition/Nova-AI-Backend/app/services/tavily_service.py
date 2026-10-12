"""Thin wrapper around the Tavily web search API."""
from tavily import TavilyClient

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TavilyService:
    """Runs web searches via Tavily and returns normalized results."""

    def __init__(self):
        self._client = TavilyClient(api_key=settings.tavily_api_key) if settings.tavily_api_key else None

    def search(self, query: str, max_results: int = 2) -> list[dict]:
        """Search the web for `query`. Returns [{"title", "url", "content"}, ...].

        Returns an empty list if Tavily isn't configured or the call fails,
        so a search hiccup never breaks the chat turn.
        """
        if self._client is None:
            logger.warning("Tavily search skipped: TAVILY_API_KEY not configured")
            return []
        try:
            response = self._client.search(query=query, max_results=max_results)
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title") or item.get("url"),
                    "url": item.get("url"),
                    "content": item.get("content", ""),
                })
            return results
        except Exception as exc:
            logger.error("Tavily search failed: %s", exc)
            return []


def get_tavily_service() -> TavilyService:
    """FastAPI dependency returning a TavilyService."""
    return TavilyService()
