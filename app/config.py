"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Telegram
    BOT_TOKEN: str

    # External APIs
    # Kept for backward compatibility; Gemini-only OCR does not require it.
    OCR_API_KEY: str = ""
    CEREBRAS_API_KEY: str
    GEMINI_API_KEY: str = ""

    # Database
    DATABASE_URL: str  # mysql+aiomysql://user:pass@host:port/db

    # Internal
    API_BASE_URL: str = "http://localhost:8000"


settings = Settings()
