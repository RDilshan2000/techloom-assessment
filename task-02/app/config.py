import os
from pydantic_settings import BaseSettings, SettingsConfigDict

def normalize_db_url(url: str) -> str:
    if not url:
        return "sqlite+aiosqlite:///./ecommerce.db"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

class Settings(BaseSettings):
    PROJECT_NAME: str = "E-Commerce Checkout & Payment System"
    DATABASE_URL: str = "sqlite+aiosqlite:///./ecommerce.db"
    RESERVATION_EXPIRY_MINUTES: int = 5
    CLEANUP_INTERVAL_SECONDS: int = 10

    model_config = SettingsConfigDict(
        env_file=(".env", "../task-01/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def __init__(self, **values):
        super().__init__(**values)
        self.DATABASE_URL = normalize_db_url(self.DATABASE_URL)

settings = Settings()
