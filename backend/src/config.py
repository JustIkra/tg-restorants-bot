from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_MINI_APP_URL: str = "http://localhost"

    # Backend API (for internal communication)
    BACKEND_API_URL: str = "http://backend:8000/api/v1"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Kafka
    KAFKA_BROKER_URL: str = "localhost:9092"

    # Redis
    REDIS_URL: str

    # Gemini API
    GEMINI_API_KEYS: str
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    GEMINI_MAX_REQUESTS_PER_KEY: int = 195

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def gemini_keys_list(self) -> list[str]:
        """Parse comma-separated Gemini API keys into a list."""
        return [k.strip() for k in self.GEMINI_API_KEYS.split(",") if k.strip()]

    @model_validator(mode="after")
    def validate_secrets(self):
        if len(self.JWT_SECRET_KEY) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return self


settings = Settings()
