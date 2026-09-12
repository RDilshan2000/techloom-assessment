from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite+aiosqlite:///./sql_app.db"
    RESERVATION_EXPIRATION_MINUTES: int = 5
    BACKGROUND_CLEANUP_INTERVAL_SECONDS: int = 30

settings = Settings()
