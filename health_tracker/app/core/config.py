from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    DATABASE_URL: str = "sqlite+aiosqlite:///./health_tracker.db"
    SECRET_KEY: str = "CHANGE-ME"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    DEBUG: bool = False


settings = Settings()
