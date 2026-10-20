"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram Bot & Webhook Secrets (Defaults must remain strictly empty strings)
    BOT_TOKEN: str = ""
    MAKE_WEBHOOK_URL: str = ""
    WEBAPP_URL: str = "http://localhost:8000"

    # Application & Static Versioning
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"


settings = Settings()
