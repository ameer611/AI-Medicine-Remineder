"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Telegram
    BOT_TOKEN: str

    # External APIs
    # Kept for backward compatibility; Gemini-only OCR does not require it.
    OCR_API_KEY: str = ""
    CEREBRAS_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Database
    DATABASE_URL: str  # mysql+aiomysql://user:pass@host:port/db
    TIMEZONE: str = "Asia/Tashkent"

    # Internal
    API_BASE_URL: str = "http://localhost:8000"

    # Bot metadata
    BOT_USERNAME: str | None = None

    # Web auth / JWT
    JWT_SECRET: str | None = None
    JWT_EXPIRE_DAYS: int = 7
    INTERNAL_API_KEY: str | None = None

    # Supervisor invite
    SUPERVISOR_INVITE_CODE: str | None = None


settings = Settings()
