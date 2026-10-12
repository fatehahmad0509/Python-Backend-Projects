"""Business logic for registration, login, token refresh, and logout."""
from datetime import datetime, timezone

from app.core.exceptions import AccountBlockedError, ConflictError, UnauthorizedError
from app.core.jwt import TokenError, TokenType, create_access_token, create_refresh_token, decode_token
from app.core.logging import get_logger
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.cache_service import CacheService

logger = get_logger(__name__)

_BLACKLIST_PREFIX = "auth:blacklist:jti:"


class AuthService:
    """Encapsulates authentication and account-credential use cases."""

    def __init__(
        self,
        user_repo: UserRepository,
        cache: CacheService,
    ):
        self._user_repo = user_repo
        self._cache = cache

    async def register(self, email: str, password: str) -> User:
        """Create a new user account."""
        existing = await self._user_repo.get_by_email(email)
        if existing is not None:
            raise ConflictError("An account with this email already exists")

        password_hash = hash_password(password)
        return await self._user_repo.create(email=email, password_hash=password_hash)

    async def login(self, email: str, password: str) -> tuple[str, str]:
        """Validate credentials and issue an access + refresh token pair."""
        user = await self._user_repo.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            logger.warning("Authentication failure for a login attempt")
            raise UnauthorizedError("Invalid email or password")

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        return access_token, refresh_token

    async def refresh(self, refresh_token: str) -> str:
        try:
            payload = decode_token(refresh_token, TokenType.REFRESH)
        except TokenError:
            raise UnauthorizedError("Invalid or expired refresh token")

        jti = payload.get("jti")
        if jti and await self._is_blacklisted(jti):
            raise UnauthorizedError("Refresh token has been revoked")

        user_id = payload.get("sub")
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User no longer exists")

        if user.is_blocked:
            raise AccountBlockedError()

        return create_access_token(str(user.id))

    async def logout(self, refresh_token: str) -> None:
        """Revoke a refresh token by blacklisting its jti until it would expire."""
        try:
            payload = decode_token(refresh_token, TokenType.REFRESH)
        except TokenError:
            return

        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or not exp:
            return

        ttl_seconds = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
        await self._cache.set_json(f"{_BLACKLIST_PREFIX}{jti}", True, ttl_seconds=ttl_seconds)

    async def _is_blacklisted(self, jti: str) -> bool:
        value = await self._cache.get_json(f"{_BLACKLIST_PREFIX}{jti}")
        return bool(value)
