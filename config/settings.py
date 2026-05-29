"""
Environment detection and configuration class for GentleQuest.
Extracted from app.py monolith.
"""

import os
from typing import Any, Dict


def _detect_environment() -> str:
    """Detect current environment automatically for single codebase usage."""
    if os.environ.get("RENDER"):
        return "production"
    elif os.environ.get("DOCKER_ENV") or os.environ.get("DOCKER"):
        return "docker"
    elif os.environ.get("ENVIRONMENT"):
        return os.environ.get("ENVIRONMENT") or "local"
    else:
        return "local"


def _get_environment_config(environment: str) -> Dict[str, Any]:
    """Get environment-specific configuration for single codebase usage."""
    configs: Dict[str, Dict[str, Any]] = {
        "local": {
            "port": 5055,
            "database_url": "postgresql+psycopg://ai_buddy:ai_buddy_password@localhost:5432/mental_health",
            "redis_url": "redis://localhost:6379",
            "cors_origins": [
                "http://localhost:8080",
                "http://127.0.0.1:8080",
                "http://localhost:3000",
                "http://localhost:9100",
                "http://127.0.0.1:9100",
            ],
        },
        "docker": {
            "port": 5055,
            "database_url": "postgresql+psycopg://ai_buddy:ai_buddy_password@db:5432/mental_health",
            "redis_url": "redis://redis:6379",
            "cors_origins": [
                "http://localhost:8080",
                "http://127.0.0.1:8080",
                "http://localhost:3000",
                "http://localhost:9100",
                "http://127.0.0.1:9100",
                "http://localhost:57442",
                "http://localhost:55725",
            ],
        },
        "production": {
            "port": 10000,
            "database_url": os.environ.get("DATABASE_URL"),
            "redis_url": "redis://localhost:6379",
            "cors_origins": [
                "https://gentlequest.onrender.com",
                "https://gentlequest.com",
                "https://www.gentlequest.com",
                "https://gentlequest.app",
                "https://www.gentlequest.app",
                "https://app.gentlequest.app",
            ],
        },
    }
    return configs.get(environment, configs["local"])


# Module-level environment constants (evaluated at import time, matching
# the legacy app.py behavior).
ENVIRONMENT = _detect_environment()
ENV_CONFIG = _get_environment_config(ENVIRONMENT)


class Config:
    """Configuration class for single codebase usage."""

    # Environment detection
    RENDER = os.getenv("RENDER", "false").lower() == "true"
    DOCKER_ENV = os.getenv("DOCKER_ENV", "false").lower() == "true"
    # Auto-detect production: if RENDER is true, treat as production unless overridden
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production" if RENDER else "local")

    # Database configuration
    if RENDER:
        # Production (Render) configuration
        DATABASE_URL = os.getenv("DATABASE_URL")
        if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    elif DOCKER_ENV:
        # Docker environment
        DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql://ai_buddy:ai_buddy_password@db:5432/mental_health",
        )
    else:
        # Local development - persistent SQLite by default
        DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "sqlite:///instance/mental_health.db",
        )

    # Cloud SQL fallback: if DATABASE_URL is missing/sqlite but DB_* components
    # are set (e.g. from Secret Manager), construct a Unix-socket DSN.
    if not DATABASE_URL or "sqlite" in DATABASE_URL:
        _db_user = os.getenv("DB_USER")
        _db_pass = os.getenv("DB_PASSWORD")
        _db_name = os.getenv("DB_NAME")
        _db_host = os.getenv("DB_HOST")  # e.g. /cloudsql/project:region:instance

        if _db_user and _db_pass and _db_name and _db_host:
            DATABASE_URL = (
                f"postgresql+psycopg://{_db_user}:{_db_pass}@/{_db_name}?host={_db_host}"
            )

    # Redis configuration
    if RENDER:
        REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    elif DOCKER_ENV:
        REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
    else:
        REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Flask configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SESSION_TYPE = os.getenv("SESSION_TYPE", "redis")

    # Server configuration
    PORT = int(os.getenv("PORT", 5055))
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", 5055))

    # AI Provider configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PPLX_API_KEY = os.getenv("PPLX_API_KEY")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")

    # CORS (env-driven; fallback to environment config)
    CORS_ORIGINS = [
        o.strip()
        for o in (
            os.getenv("CORS_ORIGINS") or ",".join(ENV_CONFIG.get("cors_origins", []))
        ).split(",")
        if o.strip()
    ]

    # Rate limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 30))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Version and build info
    VERSION = os.getenv("VERSION", "1.0.0")
    BUILD_TIME = os.getenv("BUILD_TIME", "unknown")

    # Community feature flags and rate limits
    COMMUNITY_ENABLED = os.getenv("COMMUNITY_ENABLED", "true")
    COMMUNITY_POSTING_ENABLED = os.getenv("COMMUNITY_POSTING_ENABLED", "false")
    TEMPLATES_ONLY = os.getenv("TEMPLATES_ONLY", "true")
    RATE_LIMITS_COMMUNITY_FEED = os.getenv(
        "RATE_LIMITS_COMMUNITY_FEED", "120 per minute"
    )
    RATE_LIMITS_REACTION = os.getenv(
        "RATE_LIMITS_REACTION", "20 per minute; 200 per day"
    )
    RATE_LIMITS_REPORT = os.getenv("RATE_LIMITS_REPORT", "10 per minute; 100 per day")

    # Retention policy (days)
    MESSAGE_RETENTION_DAYS = int(os.getenv("MESSAGE_RETENTION_DAYS", 30))
    SESSION_RETENTION_DAYS = int(os.getenv("SESSION_RETENTION_DAYS", 14))
    ERROR_LOG_RETENTION_DAYS = int(os.getenv("ERROR_LOG_RETENTION_DAYS", 14))
    ANALYTICS_RETENTION_DAYS = int(os.getenv("ANALYTICS_RETENTION_DAYS", 90))

    # Admin token for protected maintenance endpoints
    ADMIN_API_TOKEN = os.getenv("ADMIN_API_TOKEN")
