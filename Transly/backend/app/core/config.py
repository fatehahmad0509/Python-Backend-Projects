"""
Application configuration.

All configuration values are loaded from environment variables (or a local
.env file during development). Nothing is hardcoded so the same image can
be deployed to any environment simply by changing environment variables.
"""

from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    APP_NAME: str = "Transly"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalize_for_asyncpg(cls, v: str) -> str:
        # Managed Postgres providers (Render, Neon, Heroku, etc.) hand out
        # plain postgres:// / postgresql:// URLs, sometimes with libpq-style
        # query params (sslmode, channel_binding) that asyncpg's connect()
        # does not accept as keyword arguments. Normalize both so the same
        # URL works regardless of provider.
        scheme, netloc, path, query, fragment = urlsplit(v)
        if scheme in ("postgres", "postgresql"):
            scheme = "postgresql+asyncpg"

        params = dict(parse_qsl(query, keep_blank_values=True))
        # asyncpg's `ssl` kwarg accepts the same mode strings libpq uses
        # (disable/allow/prefer/require/verify-ca/verify-full), so translate
        # sslmode -> ssl. channel_binding has no asyncpg equivalent and is
        # safe to drop since asyncpg negotiates SCRAM channel binding
        # automatically over an SSL connection.
        if "sslmode" in params:
            params.setdefault("ssl", params.pop("sslmode"))
        params.pop("channel_binding", None)

        query = urlencode(params)
        return urlunsplit((scheme, netloc, path, query, fragment))

    # Convenience flag for local/dev bootstrap only. Real schema changes are
    # managed manually by the team (no Alembic), this only creates tables
    # that do not exist yet - it never alters existing ones.
    AUTO_CREATE_TABLES: bool = True

    # Redis
    REDIS_URL: str

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Google Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.1-flash-lite"

    # Uploads
    MAX_UPLOAD_SIZE_MB: int = 10
    MAX_IMAGE_DIMENSION: int = 6000

    # Video uploads. Kept small on purpose: videos are sent to Gemini as
    # inline bytes (not the Files API), and the inline request size cap is
    # 20MB total (video + prompt text), so MAX_VIDEO_UPLOAD_SIZE_MB must
    # stay comfortably under that. MAX_VIDEO_DURATION_SECONDS is the
    # product-level cap (1 minute) enforced via ffprobe before any Gemini
    # call is made.
    MAX_VIDEO_UPLOAD_SIZE_MB: int = 19
    MAX_VIDEO_DURATION_SECONDS: int = 60

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # CORS
    CORS_ORIGINS: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance, loaded once per process."""
    return Settings()


settings = get_settings()
