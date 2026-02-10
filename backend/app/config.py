"""
Configuration and settings for PayShield AI backend.
Supports multiple environments: dev, test, production.
"""

import os
from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    APP_NAME: str = "PayShield AI"
    APP_VERSION: str = "1.0.0"
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = ENV != "production"

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    WORKERS: int = int(os.getenv("WORKERS", 4))
    RELOAD: bool = DEBUG

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://payshield:payshield@localhost:5432/payshield_db",
    )
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", 20))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", 40))
    DATABASE_POOL_TIMEOUT: int = int(os.getenv("DATABASE_POOL_TIMEOUT", 30))
    DATABASE_POOL_RECYCLE: int = int(os.getenv("DATABASE_POOL_RECYCLE", 3600))
    DATABASE_ECHO: bool = DEBUG

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_POOL_SIZE: int = int(os.getenv("REDIS_POOL_SIZE", 50))
    REDIS_MAX_CONNECTIONS: int = int(os.getenv("REDIS_MAX_CONNECTIONS", 100))
    REDIS_SOCKET_KEEPALIVE: bool = True
    REDIS_SOCKET_KEEPALIVE_OPTIONS: dict = {
        "TCP_KEEPIDLE": 60,
        "TCP_KEEPINTVL": 10,
        "TCP_KEEPCNT": 5,
    }

    # JWT & Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-prod")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JWT_REFRESH_EXPIRATION_DAYS: int = 30
    BCRYPT_COST: int = 12
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * JWT_EXPIRATION_HOURS
    REFRESH_TOKEN_EXPIRE_DAYS: int = JWT_REFRESH_EXPIRATION_DAYS

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 5000

    # ML Model
    MODEL_PATH: str = os.getenv(
        "MODEL_PATH", "../models/payshield_model.joblib"
    )
    SHAP_EXPLAINER_PATH: str = os.getenv(
        "SHAP_EXPLAINER_PATH", "../models/shap_explainer.joblib"
    )
    PREPROCESSOR_PATH: str = os.getenv(
        "PREPROCESSOR_PATH", "../models/preprocessor.joblib"
    )
    MODEL_VERSION: str = os.getenv("MODEL_VERSION", "1.0.0")
    PREDICTION_THREADPOOL_SIZE: int = int(os.getenv("PREDICTION_THREADPOOL_SIZE", 4))
    PREDICTION_TIMEOUT_SECONDS: int = 5

    # Observability
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO" if not DEBUG else "DEBUG")
    LOG_FORMAT: str = "json"  # json or text
    PROMETHEUS_METRICS_ENABLED: bool = True

    # Caching
    CACHE_PREDICTION_TTL_SECONDS: int = 86400  # 24 hours
    CACHE_USER_TTL_SECONDS: int = 3600  # 1 hour
    CACHE_TRANSACTION_TTL_SECONDS: int = 3600  # 1 hour

    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 500

    # Validation
    MAX_TRANSACTION_AMOUNT: float = 1_000_000.00
    MIN_TRANSACTION_AMOUNT: float = 0.01

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True

    @property
    def sqlalchemy_url(self) -> str:
        """Get SQLAlchemy database URL."""
        return self.DATABASE_URL

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENV == "production"

    @property
    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return self.ENV == "test"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()