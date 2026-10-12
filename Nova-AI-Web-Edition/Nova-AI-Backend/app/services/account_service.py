"""Business logic for account deletion."""
from app.core.exceptions import UnauthorizedError
from app.core.logging import get_logger
from app.core.security import verify_password
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.user_repository import UserRepository
from app.services.cache_service import CacheService

logger = get_logger(__name__)


class AccountService:
    """Encapsulates account deletion."""

    def __init__(
        self,
        user_repo: UserRepository,
        conversation_repo: ConversationRepository,
        cache: CacheService,
    ):
        self._user_repo = user_repo
        self._conversations = conversation_repo
        self._cache = cache

    async def delete_account(self, user: User, current_password: str) -> None:
        """Verify the current password and permanently delete the account."""
        if not verify_password(current_password, user.password_hash):
            raise UnauthorizedError("Incorrect password")

        conversations = await self._conversations.list_for_user(user.id)
        for conversation in conversations:
            await self._cache.invalidate_conversation_messages(str(conversation.id))
            await self._conversations.delete(conversation)

        await self._cache.invalidate_user_conversations(str(user.id))
        await self._user_repo.delete(user)

        logger.info("Account and all associated data deleted for a user")
