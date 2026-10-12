from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from functools import lru_cache
from urllib.parse import urlparse, urlunparse

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:password@localhost/studify"
    secret_key: str = "supersecret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    gemini_api_key: str = "DUMMY_KEY"
    
    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            
            # Remove all query parameters (like ?sslmode=require&channel_binding=...) 
            # because asyncpg expects SSL config in connect_args, not in the URL.
            if "?" in v:
                parsed = urlparse(v)
                v = urlunparse(parsed._replace(query=""))
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
