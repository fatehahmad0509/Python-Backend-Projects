"""Business logic orchestrating the chat flow.

Flow for POST /chat:
    1. (Caller has already authenticated the user)
    2. Resolve/create the conversation
    3. Load conversation history (Redis cache -> Postgres fallback)
    4. Check the user's daily token budget (skipped for developer plan)
    5. Save the user message
    6. Build Gemini context and generate a reply
    7. Record actual Gemini token usage for today
    8. Save the assistant message
    9. Invalidate related caches
    10. Return the result
"""
import asyncio
import uuid

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.conversation import ConversationRead, MessageRead
from app.services.cache_service import CacheService, conversation_messages_key, user_conversations_key
from app.services.gemini_service import GeminiService, GeminiServiceError
from app.services.token_service import TokenService
from app.utils.image_input import decode_base64_image
from app.utils.title_generator import generate_title
from app.utils.token_estimator import estimate_tokens_for_messages

logger = get_logger(__name__)


class ChatService:
    """Coordinates repositories, cache, Gemini, and token budgets for chat."""

    # How many of the most recent messages get resent to Gemini as history
    # each turn. Keeps per-turn cost bounded in long conversations instead of
    # growing with every message ever sent in the conversation.
    _MAX_HISTORY_MESSAGES = 20

    # Rough fixed overhead (system prompt + web_search tool schema + search
    # instructions) that Gemini bills on *every* call regardless of message
    # content — used only to make the pre-flight budget check realistic.
    _FIXED_PROMPT_OVERHEAD_TOKENS = 150

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        cache: CacheService,
        gemini: GeminiService,
        token_service: TokenService,
    ):
        self._conversations = conversation_repo
        self._messages = message_repo
        self._cache = cache
        self._gemini = gemini
        self._tokens = token_service

    async def _get_owned_conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> Conversation:
        conversation = await self._conversations.get_by_id(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation not found")
        if conversation.user_id != user_id:
            raise ForbiddenError("You do not have access to this conversation")
        return conversation

    async def _load_history(self, conversation_id: uuid.UUID) -> list[Message]:
        """Load message history for a conversation, preferring the cache."""
        cache_key = conversation_messages_key(str(conversation_id))
        cached = await self._cache.get_json(cache_key)
        if cached is not None:
            return [
                Message(
                    id=uuid.UUID(m["id"]),
                    conversation_id=conversation_id,
                    role=m["role"],
                    content=m["content"],
                    sources=m.get("sources"),
                )
                for m in cached
            ]

        messages = await self._messages.list_for_conversation(conversation_id)
        await self._cache.set_json(cache_key, [self._serialize_message(m) for m in messages])
        return messages

    @staticmethod
    def _serialize_message(message: Message) -> dict:
        return {
            "id": str(message.id),
            "role": message.role,
            "content": message.content,
            "sources": message.sources,
            "created_at": message.created_at.isoformat() if message.created_at else None,
        }

    async def _invalidate(self, user_id: uuid.UUID, conversation_id: uuid.UUID) -> None:
        await self._cache.invalidate_user_conversations(str(user_id))
        await self._cache.invalidate_conversation_messages(str(conversation_id))

    async def send_message(
        self,
        user: User,
        conversation_id: uuid.UUID | None,
        message_text: str,
        image_base64: str | None = None,
        image_mime_type: str | None = None,
    ) -> tuple[Conversation, Message, Message]:
        """Handle a full chat turn. Returns (conversation, user_msg, assistant_msg).

        Raises TokenLimitExceededError before any message is persisted if
        the user's daily token budget would be exceeded. If image_base64 /
        image_mime_type are provided, the image is validated, sent to
        Gemini for this turn, and stored alongside the user message.
        """
        is_new_conversation = conversation_id is None

        title_task: asyncio.Task[str | None] | None = None
        if is_new_conversation:
            # Naive truncation is the immediate title (never fails, no
            # latency). A smart LLM-generated title is kicked off
            # concurrently and, if it succeeds, overwrites this once the
            # turn finishes — same idea as ChatGPT's auto-titling.
            conversation = await self._conversations.create(
                user_id=user.id, title=generate_title(message_text)
            )
            title_task = asyncio.create_task(self._gemini.generate_title(message_text))
        else:
            conversation = await self._get_owned_conversation(conversation_id, user.id)

        # Load history BEFORE saving the new user message, so it isn't duplicated.
        history = [] if is_new_conversation else await self._load_history(conversation.id)

        # The full history is resent to Gemini on *every* turn (it has no
        # server-side session), so an untruncated history makes cost grow
        # without bound as a conversation gets longer. Cap it to the most
        # recent messages — plenty of context for a chat assistant.
        history_for_gemini = history[-self._MAX_HISTORY_MESSAGES :]

        image_bytes: bytes | None = None
        if image_base64 and image_mime_type:
            image_bytes = decode_base64_image(image_base64, image_mime_type)

        # Rough pre-flight estimate used only to gate the request before an
        # expensive Gemini call. Besides the message text itself, every call
        # also carries a fixed system-prompt/tool-schema overhead plus the
        # user's "about me" details (capped at GeminiService's injection
        # limit) — include both so the daily-limit check isn't wildly more
        # optimistic than what actually gets billed.
        estimated_tokens = estimate_tokens_for_messages(
            *(m.content for m in history_for_gemini),
            message_text,
            user.details[: GeminiService.MAX_USER_CONTEXT_CHARS] if user.details else "",
        )
        estimated_tokens += self._FIXED_PROMPT_OVERHEAD_TOKENS
        if image_bytes is not None:
            # Rough fixed allowance for image tokens; the authoritative count
            # still comes from Gemini's own usage_metadata after the call.
            estimated_tokens += 300
        await self._tokens.check_limit(user, estimated_tokens)

        user_message = await self._messages.create(
            conversation.id,
            role="user",
            content=message_text,
            image_base64=image_base64 if image_bytes is not None else None,
            image_mime_type=image_mime_type if image_bytes is not None else None,
        )

        # The actual remaining search quota, not just a yes/no gate — a
        # single turn can call web_search more than once (see
        # GeminiService.generate_reply's retry loop), so Gemini needs to
        # know exactly how many it's allowed to actually run this turn to
        # avoid blowing past the daily cap mid-turn.
        search_allowance = await self._tokens.get_search_allowance(user)

        try:
            reply = await self._gemini.generate_reply(
                history_for_gemini,
                message_text,
                image_bytes=image_bytes,
                image_mime_type=image_mime_type if image_bytes is not None else None,
                user_context=user.details,
                web_search_allowed=search_allowance > 0,
                max_web_searches=search_allowance,
            )
        except GeminiServiceError:
            if title_task is not None:
                title_task.cancel()
            logger.error("Gemini generation failed for conversation_id=%s", conversation.id)
            raise

        await self._tokens.record_usage(
            user.id, reply.prompt_tokens, reply.completion_tokens, reply.search_count
        )

        assistant_message = await self._messages.create(
            conversation.id, role="assistant", content=reply.text, sources=reply.sources
        )

        if not is_new_conversation:
            await self._conversations.touch(conversation)
        elif title_task is not None:
            smart_title = await title_task
            if smart_title:
                await self._conversations.update_title(conversation, smart_title)

        await self._invalidate(user.id, conversation.id)

        return conversation, user_message, assistant_message

    async def list_conversations(self, user_id: uuid.UUID) -> list[ConversationRead]:
        cache_key = user_conversations_key(str(user_id))
        cached = await self._cache.get_json(cache_key)
        if cached is not None:
            return [ConversationRead.model_validate(c) for c in cached]

        conversations = await self._conversations.list_for_user(user_id)
        result = [ConversationRead.model_validate(c) for c in conversations]
        await self._cache.set_json(cache_key, [r.model_dump(mode="json") for r in result])
        return result

    async def get_conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> Conversation:
        conversation = await self._conversations.get_by_id_with_messages(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation not found")
        if conversation.user_id != user_id:
            raise ForbiddenError("You do not have access to this conversation")
        return conversation

    async def delete_conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> None:
        conversation = await self._get_owned_conversation(conversation_id, user_id)
        await self._conversations.delete(conversation)
        await self._invalidate(user_id, conversation_id)
