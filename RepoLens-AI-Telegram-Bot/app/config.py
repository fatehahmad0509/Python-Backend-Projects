from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    telegram_bot_token: str
    gemini_api_key: str
    github_token: str | None = None
    gemini_model: str = "gemini-3.1-flash-lite"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
