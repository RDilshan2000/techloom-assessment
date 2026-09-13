import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "E-Commerce Checkout & Payment System"
    DATABASE_URL: str = "sqlite+aiosqlite:///./ecommerce.db"
    RESERVATION_EXPIRY_MINUTES: int = 5
    CLEANUP_INTERVAL_SECONDS: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
