"""
Flask extension initialization: database, sessions, rate limiter, CORS,
security headers. Extracted from app.py monolith.
"""

import re
import time

import redis
from flask import Flask, Response, current_app, request
from flask_cors import CORS
from flask_limiter.util import get_remote_address

from config.settings import Config
from flask_session import Session  # type: ignore[attr-defined]
from models import db


def _init_database(app: Flask) -> None:
    """Initialize database with tables (SQLAlchemy ORM)."""
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables initialized successfully via SQLAlchemy")
        except Exception as e:
            app.logger.error(f"Database initialization error: {e}")
            app.logger.warning(
                "Continuing without full DB initialization. Check health endpoint."
            )


def _setup_session(app: Flask) -> None:
    """Configure session management with Redis fallback."""
    redis_url = app.config.get("REDIS_URL")

    if redis_url and redis_url != "port" and redis_url.strip():
        try:
            redis_client = redis.from_url(
                redis_url,
                socket_connect_timeout=1,
                socket_timeout=1,
                retry_on_timeout=False,
            )
            redis_client.ping()
            app.config["SESSION_TYPE"] = "redis"
            app.config["SESSION_REDIS"] = redis_client
            app.logger.info("Redis sessions enabled")
        except Exception as e:
            app.logger.info(
                f"Redis connection failed: {e}, using filesystem sessions"
            )
            app.config["SESSION_TYPE"] = "filesystem"
            app.config["SESSION_REDIS"] = None
    else:
        app.logger.info("No REDIS_URL found, using filesystem sessions")
        app.config["SESSION_TYPE"] = "filesystem"
        app.config["SESSION_REDIS"] = None

    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = False

    Session(app)


def _rate_limit_enabled() -> bool:
    """Return True if rate limiting should be applied for this request."""
    try:
        raw = current_app.config.get("RATE_LIMIT_ENABLED", True)
    except Exception:
        return True
    if isinstance(raw, str):
        return raw.lower() == "true"
    return bool(raw)


def _rate_limit_key():
    """Compute the rate-limit key.

    Prefer per-session limiting; fall back to client IP to avoid false positives
    when many clients share an IP (e.g., behind proxies).
    """
    if not _rate_limit_enabled():
        return f"disabled:{request.remote_addr}:{time.time_ns()}"

    try:
        env = (current_app.config.get("ENVIRONMENT") or "").lower()
    except Exception:
        env = ""

    if env == "test":
        return get_remote_address()

    try:
        sid = request.headers.get("X-Session-ID")
        if sid and sid.strip():
            return f"sid:{sid.strip()}"
    except Exception:
        pass
    return get_remote_address()


def _setup_rate_limiter(app: Flask):
    """Configure rate limiting."""
    from extensions import limiter

    # Choose storage based on Redis availability
    storage_uri = "memory://"
    try:
        if (
            app.config.get("SESSION_TYPE") == "redis"
            and app.config.get("SESSION_REDIS") is not None
        ):
            storage_uri = app.config.get("REDIS_URL", "memory://")
    except Exception:
        pass

    app.config["RATELIMIT_STORAGE_URI"] = storage_uri
    app.config["RATELIMIT_DEFAULT"] = "5000 per day; 1000 per hour"

    limiter.init_app(app)
    limiter._key_func = _rate_limit_key
    app.limiter = limiter  # type: ignore[attr-defined]
    return limiter


def _setup_cors(app: Flask) -> None:
    """Configure CORS with security best practices."""
    origins = app.config.get("CORS_ORIGINS") or [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://localhost:9100",
        "http://127.0.0.1:9100",
    ]
    try:
        if Config.ENVIRONMENT == "local" or Config.DOCKER_ENV:
            origins = list(origins) + [
                re.compile(r"^http://localhost:\d+$"),
                re.compile(r"^http://127\.0\.0\.1:\d+$"),
            ]
    except Exception:
        pass
    CORS(
        app,
        origins=origins,
        supports_credentials=True,
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Accept",
            "X-Session-ID",
            "X-Request-ID",
            "X-Analytics-Consent",
            "X-Admin-Token",
        ],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        expose_headers=["Content-Type", "X-Session-ID", "X-Request-ID"],
    )


def _setup_security_headers(app: Flask) -> None:
    """Add security headers to all responses."""
    @app.after_request
    def add_security_headers(response: Response) -> Response:
        if app.config.get("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if "Content-Security-Policy" not in response.headers:
            response.headers["Content-Security-Policy"] = (
                "upgrade-insecure-requests"
            )

        if "Permissions-Policy" not in response.headers:
            response.headers["Permissions-Policy"] = (
                "geolocation=(), microphone=(), camera=(), payment=()"
            )

        return response


def _init_extensions(app: Flask) -> None:
    """Initialize Flask extensions with proper error handling."""
    try:
        db.init_app(app)
        _setup_session(app)
        app.limiter = _setup_rate_limiter(app)  # type: ignore[attr-defined]
        _setup_cors(app)

        app.logger.info(
            f"All extensions initialized successfully for environment: "
            f"{app.config.get('ENVIRONMENT')}"
        )
    except Exception as e:
        app.logger.error(f"Failed to initialize extensions: {e}")
        raise


def configure_app(app: Flask) -> None:
    """One-call setup: extensions + security headers + initial DB."""
    _init_extensions(app)
    _setup_security_headers(app)
    _init_database(app)
