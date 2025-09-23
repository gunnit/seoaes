from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/llm_optimization")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")

    # PayPal
    PAYPAL_CLIENT_ID: str = os.getenv("PAYPAL_CLIENT_ID", "")
    PAYPAL_CLIENT_SECRET: str = os.getenv("PAYPAL_CLIENT_SECRET", "")
    PAYPAL_ENVIRONMENT: str = os.getenv("PAYPAL_ENVIRONMENT", "sandbox")

    # URLs
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    # App Settings
    APP_NAME: str = "AIVisibility.pro"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "True") == "True"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # Analysis Settings
    MAX_CRAWL_DEPTH_FREE: int = 1
    MAX_CRAWL_DEPTH_PRO: int = 50
    MAX_CRAWL_DEPTH_AGENCY: int = 100
    FREE_MONTHLY_SCANS: int = 10

    # Cache Settings
    CRAWL_CACHE_HOURS: int = 1
    AI_CACHE_HOURS: int = 24
    REPORT_CACHE_HOURS: int = 1

    # OpenAI Settings
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_DAILY_LIMIT_USD: float = 100.0

    # Pricing
    PLAN_PRICES = {
        "free": 0,
        "professional": 397,
        "agency": 1497
    }

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()