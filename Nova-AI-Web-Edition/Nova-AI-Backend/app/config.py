"""Application configuration loaded from environment variables (.env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings, populated from the environment."""

    # Database
    database_url: str

    # Redis
    redis_url: str

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    refresh_token_expire_days: int = 30

    # Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-3.1-flash-lite"
    gemini_temperature: float = 0.7
    gemini_max_output_tokens: int = 2048
    gemini_system_prompt: str = "You are Nova, a helpful, friendly AI assistant."
    # Toggle for the Google Search grounding tool (env: GEMINI_WEB_SEARCH_ENABLED)
    gemini_web_search_enabled: bool = True

    # Tavily (web search)
    tavily_api_key: str = ""

    # CORS
    frontend_origin: str = "http://localhost:3000"

    # Public backend URL (used to populate the "servers" field in openapi.json
    # so frontend tooling generated from the schema points at the right host).
    backend_url: str = "http://localhost:8000"

    # Vision (image understanding)
    max_image_size_mb: float = 8.0

    # App
    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once per process)."""
    return Settings()


settings = get_settings()
