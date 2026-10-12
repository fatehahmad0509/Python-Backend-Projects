"""Service wrapping the Google Gemini API for chat completions."""
from dataclasses import dataclass
from datetime import datetime

import google.generativeai as genai

from app.config import settings
from app.core.logging import get_logger
from app.models.message import Message
from app.services.tavily_service import TavilyService, get_tavily_service

logger = get_logger(__name__)

genai.configure(api_key=settings.gemini_api_key)

_WEB_SEARCH_TOOL = {
    "function_declarations": [
        {
            "name": "web_search",
            "description": (
                "Search the live web for current info (news, prices, events, "
                "anything that may have changed since training). `query` "
                "should be a short, keyword-based search-engine query, not "
                "the user's literal sentence."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A concise search-engine-style query.",
                    }
                },
                "required": ["query"],
            },
        }
    ]
}


class GeminiServiceError(Exception):
    """Raised when the Gemini API fails to produce a response."""


@dataclass
class GeminiConfig:
    """Configurable generation parameters for a single request."""

    model: str = settings.gemini_model
    temperature: float = settings.gemini_temperature
    max_output_tokens: int = settings.gemini_max_output_tokens
    system_prompt: str = settings.gemini_system_prompt
    web_search_enabled: bool = settings.gemini_web_search_enabled


@dataclass
class GeminiReply:
    """A generated reply plus the token usage Gemini reported for it."""

    text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    # Web sources returned by Tavily if the model called the web_search
    # tool for this turn. None when it didn't.
    sources: list[dict] | None = None
    # How many times the web_search tool actually ran this turn (0 if it
    # wasn't offered, wasn't called, or the user was out of searches).
    search_count: int = 0


class GeminiService:
    """Generates chat responses from conversation history via Gemini."""

    def __init__(self, config: GeminiConfig | None = None, tavily: TavilyService | None = None):
        self._config = config or GeminiConfig()
        self._tavily = tavily or get_tavily_service()

    @staticmethod
    def _to_gemini_history(messages: list[Message]) -> list[dict]:
        """Convert stored Message rows into Gemini's expected message format.

        Gemini uses role "user" and "model" (not "assistant").
        """
        history = []
        for msg in messages:
            role = "model" if msg.role == "assistant" else "user"
            history.append({"role": role, "parts": [msg.content]})
        return history

    # user_context (the user's self-written "about me" details) is resent in
    # full on *every single turn* of a conversation — it can be up to 4000
    # chars (~1000 tokens) per the UserDetailsUpdate schema. Left uncapped,
    # a user with a long bio pays that cost on every message, forever. Cap
    # what we actually inject here; storage/editing is untouched.
    MAX_USER_CONTEXT_CHARS = 350

    def _build_system_instruction(self, user_context: str | None, search_tool_offered: bool) -> str:
        """Append the user's self-provided details to the base system prompt, if any."""
        base = self._config.system_prompt
        today = datetime.now().strftime("%d %B %Y, %A")
        if search_tool_offered:
            # Kept short on purpose: this (plus the web_search tool schema
            # below) is fixed overhead sent on *every* turn this is offered.
            search_instruction = (
                f"\n\nToday is {today}. Trust this over training data. You "
                "have a `web_search` tool — use it for anything time-sensitive "
                "or possibly outdated (news, prices, scores, current "
                "office-holders, etc.) instead of guessing. Write a proper "
                "search query, not the user's raw sentence."
            )
        else:
            # No web_search tool this turn (out of daily quota, or this
            # message plausibly doesn't need it) — don't tell the model to
            # call something that isn't offered.
            search_instruction = (
                f"\n\nToday is {today}. Trust this over training data. Web "
                "search isn't available right now — answer from your own "
                "knowledge and say so if something may have changed recently."
            )
        if not user_context:
            return base + search_instruction

        trimmed_context = user_context[: self.MAX_USER_CONTEXT_CHARS]
        if len(user_context) > self.MAX_USER_CONTEXT_CHARS:
            trimmed_context += "…"
        return (
            f"{base}{search_instruction}\n\n"
            "User-shared info (background only — do NOT greet, address by name, "
            "or react to this unless the user's message is directly about it):\n"
            f"{trimmed_context}"
        )

    def _build_tools(self, search_tool_offered: bool) -> list | None:
        """Return the Gemini tools list for web search, if enabled and offered this turn.

        `search_tool_offered` is already the combination of daily search
        quota remaining AND the per-message need classification — when
        False the tool isn't offered at all, so Gemini answers from its
        own knowledge instead.
        """
        if not self._config.web_search_enabled or not search_tool_offered:
            return None
        return [_WEB_SEARCH_TOOL]

    def _run_web_search(self, query: str) -> list[dict]:
        """Run a Tavily search and return normalized results."""
        return self._tavily.search(query)

    _SEARCH_CLASSIFIER_PROMPT = (
        "You decide whether answering a chat message well would require "
        "current/real-time external information (news, prices, scores, "
        "weather, who currently holds a position, recent events, etc.) "
        "that an AI's static training data likely can't answer reliably. "
        "Casual conversation, opinions, general knowledge, math, coding, "
        "and personal topics do NOT need this. Reply with exactly one "
        "word: YES or NO."
    )

    async def _should_offer_search(self, new_user_message: str) -> bool:
        """Cheap pre-check deciding whether to offer the web_search tool.

        Runs a small, tool-less classification call (no system prompt, no
        function schema) instead of a keyword list, so it actually
        understands intent rather than pattern-matching words. This call
        costs far less than the web_search tool's own schema (~250 tokens),
        so skipping the tool on the (common) messages that don't need it is
        a net win. On any failure/ambiguity we default to True (offer the
        tool) — better to pay the extra tokens than silently withhold real
        search when it's actually needed.
        """
        try:
            classifier = genai.GenerativeModel(
                model_name=self._config.model,
                system_instruction=self._SEARCH_CLASSIFIER_PROMPT,
                generation_config={"temperature": 0, "max_output_tokens": 5},
            )
            response = await classifier.generate_content_async(new_user_message)
            answer = (response.text or "").strip().upper()
            return answer.startswith("Y")
        except Exception as exc:
            logger.warning("Search-need classification failed, defaulting to offering the tool: %s", exc)
            return True

    # Kept short and cheap on purpose — this is one extra LLM call per new
    # conversation only, not per turn.
    _TITLE_SYSTEM_PROMPT = (
        "You generate short conversation titles, like a chat app's sidebar "
        "label. Read the user's message and reply with ONLY a concise title "
        "(max 3 words) summarizing its topic, in the same language as the "
        "message. No quotation marks, no punctuation at the end, no preamble."
    )

    async def generate_title(self, first_message: str) -> str | None:
        """Generate a short, descriptive conversation title via a cheap LLM call.

        Returns None on any failure (bad response, API error, empty text) so
        the caller can fall back to a deterministic, dependency-free title
        instead of failing the whole chat turn over a cosmetic feature.
        """
        try:
            model = genai.GenerativeModel(
                model_name=self._config.model,
                system_instruction=self._TITLE_SYSTEM_PROMPT,
                generation_config={"temperature": 0.3, "max_output_tokens": 20},
            )
            response = await model.generate_content_async(first_message)
            title = (response.text or "").strip().strip("\"'").rstrip(".")
            return title or None
        except Exception as exc:
            logger.warning("Title generation failed, falling back to truncation: %s", exc)
            return None

    async def generate_reply(
        self,
        history: list[Message],
        new_user_message: str,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
        user_context: str | None = None,
        web_search_allowed: bool = True,
        max_web_searches: int = 3,
    ) -> GeminiReply:
        """Generate an assistant reply given prior messages plus a new one.

        `history` should be the conversation's existing messages (not
        including `new_user_message`, which is sent as the latest turn).
        If `image_bytes`/`image_mime_type` are given, the image is attached
        to this turn only (older turns are never replayed with their
        images). `user_context` is free-form info about the user, injected
        into the system prompt so Nova can personalize its reply.
        `web_search_allowed` controls whether the web_search tool is
        offered at all (False when the user is out of daily searches for
        their plan). `max_web_searches` caps how many times the tool may
        actually be run *this turn* — since a single turn can call it more
        than once, this (the caller's remaining daily quota) is what keeps
        a turn from running more searches than the user has left, even
        though `web_search_allowed` alone already said the tool could be
        offered at the start of the turn. When search runs, cited sources
        and the number of searches performed are returned on `GeminiReply`.
        Returns the reply text along with the token usage Gemini reported.
        """
        try:
            # Only offer the web_search tool (and its ~250-token schema) on
            # turns that plausibly need it. `web_search_allowed` is the
            # quota gate (unchanged); `_should_offer_search` is a cheap,
            # tool-less classification call that decides need. Skipping the
            # classifier entirely when quota is already exhausted saves that
            # extra call too.
            search_tool_offered = web_search_allowed and await self._should_offer_search(new_user_message)

            model = genai.GenerativeModel(
                model_name=self._config.model,
                system_instruction=self._build_system_instruction(user_context, search_tool_offered),
                generation_config={
                    "temperature": self._config.temperature,
                    "max_output_tokens": self._config.max_output_tokens,
                },
                tools=self._build_tools(search_tool_offered),
            )
            chat_session = model.start_chat(history=self._to_gemini_history(history))

            if image_bytes is not None:
                content = [{"mime_type": image_mime_type, "data": image_bytes}, new_user_message]
            else:
                content = new_user_message

            response = await chat_session.send_message_async(content)

            prompt_tokens = 0
            completion_tokens = 0
            sources: list[dict] | None = None
            search_count = 0

            # If Gemini decided to call the web_search tool, run it via
            # Tavily and send the results back so it can finish its answer.
            # Loop in case the model wants to search more than once.
            for _ in range(3):
                usage = getattr(response, "usage_metadata", None)
                prompt_tokens += getattr(usage, "prompt_token_count", 0) or 0
                completion_tokens += getattr(usage, "candidates_token_count", 0) or 0

                function_call = self._extract_function_call(response)
                if function_call is None:
                    break

                if search_count >= max_web_searches:
                    # The daily quota was already used up by earlier
                    # searches *this same turn* — don't call Tavily again.
                    # Tell the model no more searches are available so it
                    # can still finish an answer with what it already has.
                    response = await chat_session.send_message_async(
                        genai.protos.Content(
                            parts=[
                                genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name="web_search",
                                        response={"error": "Daily web search limit reached"},
                                    )
                                )
                            ]
                        )
                    )
                    continue

                query = function_call.args.get("query", "")
                results = self._run_web_search(query)
                search_count += 1
                if results:
                    sources = (sources or []) + [
                        {"title": r["title"], "url": r["url"]} for r in results
                    ]

                response = await chat_session.send_message_async(
                    genai.protos.Content(
                        parts=[
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name="web_search",
                                    response={"results": results},
                                )
                            )
                        ]
                    )
                )

            # response.text raises ValueError when the response is blocked
            # by safety filters (finish_reason != STOP).
            try:
                text = response.text
            except ValueError as exc:
                feedback = getattr(response, "prompt_feedback", None)
                reason = getattr(feedback, "block_reason", None) or "unknown"
                logger.warning(
                    "Gemini response blocked (block_reason=%s): %s",
                    reason, exc,
                )
                raise GeminiServiceError(
                    f"Gemini response was blocked. Reason: {reason}"
                ) from exc

            text = (text or "").strip()
            if not text:
                raise GeminiServiceError("Gemini returned an empty response")

            usage = getattr(response, "usage_metadata", None)
            prompt_tokens += getattr(usage, "prompt_token_count", 0) or 0
            completion_tokens += getattr(usage, "candidates_token_count", 0) or 0
            total_tokens = prompt_tokens + completion_tokens

            # Dedupe sources while preserving order.
            if sources:
                seen = set()
                deduped = []
                for s in sources:
                    if s["url"] not in seen:
                        seen.add(s["url"])
                        deduped.append(s)
                sources = deduped

            return GeminiReply(
                text=text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                sources=sources,
                search_count=search_count,
            )
        except GeminiServiceError:
            raise
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)
            raise GeminiServiceError("Failed to generate a response from Gemini") from exc

    @staticmethod
    def _extract_function_call(response):
        """Return the first function_call part in the response, if any."""
        try:
            for part in response.candidates[0].content.parts:
                fc = getattr(part, "function_call", None)
                if fc and fc.name == "web_search":
                    return fc
        except (AttributeError, IndexError):
            pass
        return None


def get_gemini_service() -> GeminiService:
    """FastAPI dependency returning a GeminiService with default config."""
    return GeminiService()
