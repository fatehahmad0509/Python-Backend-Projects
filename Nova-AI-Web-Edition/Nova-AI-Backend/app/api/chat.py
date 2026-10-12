"""Chat and conversation endpoints."""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import AppError
from app.core.limiter import rate_limit
from app.db.session import get_db
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.token_usage_repository import TokenUsageRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.conversation import ConversationDetailRead, ConversationRead, MessageRead
from app.services.cache_service import CacheService, get_cache_service
from app.services.chat_service import ChatService
from app.services.gemini_service import GeminiService, GeminiServiceError, get_gemini_service
from app.services.token_service import TokenService

router = APIRouter(tags=["chat"])

_CHAT_RATE_LIMIT = Depends(rate_limit("chat", limit=20, window_seconds=60, by="user"))


def get_chat_service(
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    gemini: GeminiService = Depends(get_gemini_service),
) -> ChatService:
    return ChatService(
        conversation_repo=ConversationRepository(db),
        message_repo=MessageRepository(db),
        cache=cache,
        gemini=gemini,
        token_service=TokenService(TokenUsageRepository(db)),
    )


class GeminiUnavailableError(AppError):
    def __init__(self):
        super().__init__(
            "The AI service is temporarily unavailable. Please try again shortly.",
            status_code=status.HTTP_502_BAD_GATEWAY,
            error="gemini_unavailable",
        )


@router.post("/chat", response_model=ChatResponse, dependencies=[_CHAT_RATE_LIMIT])
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Send a message and receive Nova's generated reply."""
    try:
        conversation, user_message, assistant_message = await service.send_message(
            user=current_user,
            conversation_id=body.conversation_id,
            message_text=body.message,
            image_base64=body.image_base64,
            image_mime_type=body.image_mime_type,
        )
    except GeminiServiceError:
        raise GeminiUnavailableError()

    return ChatResponse(
        conversation_id=conversation.id,
        title=conversation.title,
        user_message=MessageRead.model_validate(user_message),
        assistant_message=MessageRead.model_validate(assistant_message),
    )


@router.get("/chat/conversations", response_model=list[ConversationRead])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> list[ConversationRead]:
    """List all conversations belonging to the current user, most recent first."""
    return await service.list_conversations(current_user.id)


@router.get("/chat/conversations/{conversation_id}", response_model=ConversationDetailRead)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ConversationDetailRead:
    """Fetch a single conversation along with its full message history."""
    conversation = await service.get_conversation(conversation_id, current_user.id)
    return ConversationDetailRead.model_validate(conversation)


@router.delete("/chat/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> None:
    """Delete a conversation and all of its messages."""
    await service.delete_conversation(conversation_id, current_user.id)
