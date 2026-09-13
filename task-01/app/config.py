import os
from pydantic_settings import BaseSettings, SettingsConfigDict

def normalize_db_url(url: str) -> str:
    if not url:
        return "sqlite+aiosqlite:///./sql_app.db"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./sql_app.db"
    RESERVATION_EXPIRATION_MINUTES: int = 5
    BACKGROUND_CLEANUP_INTERVAL_SECONDS: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def __init__(self, **values):
        super().__init__(**values)
        self.DATABASE_URL = normalize_db_url(self.DATABASE_URL)

settings = Settings()
