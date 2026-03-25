"""
AI Mental Health Assistant - Flask Backend
Optimized for single codebase usage across development, Docker, and Render production
"""

import os
print("DEBUG: app.py start imports")
from dotenv import load_dotenv

# Load environment variables explicitly from file location (Fix for missing API keys)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

import socket
import re
import logging
import json
import sys
import redis
import requests
import time
import threading
import uuid
import secrets
import functools
from concurrent.futures import ThreadPoolExecutor

# Add mcp-server-nucleus to python path for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "mcp-server-nucleus", "src")))
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory,
    g,
    Response,
    current_app,
    render_template,
)
from flask_cors import CORS
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import text as sql_text



# Import after environment setup
from models import db, Message, ConversationLog, SelfAssessmentEntry, CrisisEvent, MoodEntry, UserSession, AnalyticsEvent
from crisis_detection import detect_crisis_level
from community import register_community_routes
from providers.clinical_assessments import (
    get_assessment_questions,
    validate_responses,
    score_phq9,
    score_gad7,
    save_assessment_result,
    get_assessment_history
)
from providers.alert_manager import AlertManager

# Import enterprise integration
try:
    from api_clinical_dashboard import clinical_dashboard
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    print("Clinical Dashboard not available: api_clinical_dashboard.py missing")

try:
    from integrations import integrate_with_app

    ENTERPRISE_FEATURES = True
except ImportError as e:
    ENTERPRISE_FEATURES = False
    print(f"Enterprise features not available: {e}")

try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    SENTRY_AVAILABLE = True
except Exception:
    SENTRY_AVAILABLE = False

# Initialize background executor for async tasks (Scaling Crisis Detection)
background_executor = ThreadPoolExecutor(max_workers=5)

# Graceful shutdown: wait for background tasks during deployment restarts
import atexit
atexit.register(lambda: background_executor.shutdown(wait=True))

# Geography-specific crisis resources
CRISIS_RESOURCES_BY_COUNTRY = {
    "in": {  # India
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call iCall Helpline at 022-25521111 or AASRA at 91-22-27546669. You can also text HOME to 741741 to reach Crisis Text Line. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {"name": "iCall Helpline", "number": "022-25521111", "available": "24/7"},
            {"name": "AASRA", "number": "91-22-27546669", "available": "24/7"},
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
        ],
    },
    "us": {  # United States
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call the National Suicide Prevention Lifeline at 988 or text HOME to 741741 to reach the Crisis Text Line. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {
                "name": "National Suicide Prevention Lifeline",
                "number": "988",
                "available": "24/7",
            },
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "911", "available": "24/7"},
        ],
    },
    "uk": {  # United Kingdom
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call Samaritans at 116 123 or text SHOUT to 85258. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {"name": "Samaritans", "number": "116 123", "available": "24/7"},
            {"name": "SHOUT Text Line", "text": "SHOUT to 85258", "available": "24/7"},
            {"name": "Emergency Services", "number": "999", "available": "24/7"},
        ],
    },
    "ca": {  # Canada
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call the National Suicide Prevention Service at 1-833-456-4566 or text HOME to 741741. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {
                "name": "National Suicide Prevention Service",
                "number": "1-833-456-4566",
                "available": "24/7",
            },
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "911", "available": "24/7"},
        ],
    },
    "au": {  # Australia
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call Lifeline at 13 11 14 or text HOME to 741741. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {"name": "Lifeline", "number": "13 11 14", "available": "24/7"},
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "000", "available": "24/7"},
        ],
    },
    "de": {  # Germany
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call TelefonSeelsorge at 0800 111 0 111 or text HOME to 741741. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {
                "name": "TelefonSeelsorge",
                "number": "0800 111 0 111",
                "available": "24/7",
            },
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "112", "available": "24/7"},
        ],
    },
    "fr": {  # France
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call SOS Amitié at 09 72 39 40 50 or text HOME to 741741. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {"name": "SOS Amitié", "number": "09 72 39 40 50", "available": "24/7"},
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "112", "available": "24/7"},
        ],
    },
    "jp": {  # Japan
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call TELL Lifeline at 03-5774-0992 or text HOME to 741741. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {"name": "TELL Lifeline", "number": "03-5774-0992", "available": "24/7"},
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "119", "available": "24/7"},
        ],
    },
    "br": {  # Brazil
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call CVV at 188 or text HOME to 741741. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {"name": "CVV", "number": "188", "available": "24/7"},
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "192", "available": "24/7"},
        ],
    },
    "mx": {  # Mexico
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call SAPTEL at 55-5259-8121 or text HOME to 741741. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {"name": "SAPTEL", "number": "55-5259-8121", "available": "24/7"},
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "911", "available": "24/7"},
        ],
    },
    "generic": {  # Fallback for unsupported countries
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please reach out to Befrienders Worldwide or call your local emergency services. You can also text HOME to 741741 for international crisis support. You're not alone, and help is available.",
        "crisis_numbers": [
            {
                "name": "Befrienders Worldwide",
                "url": "https://www.befrienders.org/",
                "available": "24/7",
            },
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {
                "name": "Emergency Services",
                "note": "Call your local emergency number",
                "available": "24/7",
            },
        ],
    },
}


@functools.lru_cache(maxsize=1024)
def get_country_code_from_ip(ip: str) -> str:
    """Get country code from IP address using ipinfo.io (cached per IP)."""
    try:
        # Skip local/private IPs
        if ip in ["127.0.0.1", "localhost", "::1"] or ip.startswith(
            ("10.", "172.", "192.168.")
        ):
            return "generic"

        # Validate IP format before external call (SSRF prevention)
        import ipaddress as _ipaddress
        try:
            _ipaddress.ip_address(ip)
        except ValueError:
            return "generic"

        # Use ipinfo.io for geolocation
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            country_code = data.get("country", "").lower()
            return (
                country_code
                if country_code in CRISIS_RESOURCES_BY_COUNTRY
                else "generic"
            )
        else:
            return "generic"
    except Exception as e:
        print(f"IP geolocation error: {e}")
        return "generic"


def get_country_from_request(req) -> str:
    """Get country from request - either from country parameter or IP"""
    # Check for explicit country override
    data = req.get_json() if req.is_json else {}
    country = data.get("country", "").lower()

    if country and country in CRISIS_RESOURCES_BY_COUNTRY:
        return country

    # Get IP from various headers
    ip = req.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not ip:
        ip = req.headers.get("X-Real-IP", "")
    if not ip:
        ip = req.remote_addr

    return get_country_code_from_ip(ip)


def _detect_environment() -> str:
    """Detect current environment automatically for single codebase usage"""
    if os.environ.get("RENDER"):
        return "production"
    elif os.environ.get("DOCKER_ENV") or os.environ.get("DOCKER"):
        return "docker"
    elif os.environ.get("ENVIRONMENT"):
        return os.environ.get("ENVIRONMENT")
    else:
        return "local"


def _get_environment_config(environment: str) -> Dict[str, Any]:
    """Get environment-specific configuration for single codebase usage"""
    configs = {
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
                "https://nucleus.gentlequest.app",
            ],
        },
    }
    return configs.get(environment, configs["local"])


# Configuration constants with environment detection
ENVIRONMENT = _detect_environment()
ENV_CONFIG = _get_environment_config(ENVIRONMENT)


class Config:
    """Configuration class for single codebase usage"""

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
        # Local development - use persistent SQLite by default
        DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "sqlite:///instance/mental_health.db",
        )

    # -------------------------------------------------------------------------
    # GENTLEQUEST CLOUD SQL FIX (~Line 322)
    # If DATABASE_URL is somehow missing but we have DB components (e.g. from Secrets),
    # construct it dynamically for Cloud SQL.
    # -------------------------------------------------------------------------
    if not DATABASE_URL or "sqlite" in DATABASE_URL:
        _db_user = os.getenv("DB_USER")
        _db_pass = os.getenv("DB_PASSWORD")
        _db_name = os.getenv("DB_NAME")
        _db_host = os.getenv("DB_HOST")  # Expected: /cloudsql/project:region:instance

        if _db_user and _db_pass and _db_name and _db_host:
            # Construct PostgreSQL connection string for Unix Socket
            # Format: postgresql+psycopg://user:pass@/dbname?host=/cloudsql/instance
            DATABASE_URL = f"postgresql+psycopg://{_db_user}:{_db_pass}@/{_db_name}?host={_db_host}"
    # -------------------------------------------------------------------------

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

    # CORS configuration (env-driven; fallback to environment config)
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

    # Community feature flags and limits
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


def create_app() -> Flask:
    """Application factory pattern for single codebase usage"""
    app = Flask(__name__, static_folder="static", static_url_path="", template_folder="templates")

    # Load configuration
    app.config.from_object(Config)

    # Fail-fast if production uses default SECRET_KEY
    if app.config.get("ENVIRONMENT") == "production" and \
       app.config.get("SECRET_KEY") == "dev-secret-key-change-in-production":
        raise ValueError("SECRET_KEY must be explicitly set in production")

    # Limit request body size to prevent memory exhaustion (5 MB)
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    test_mode = bool(os.getenv("CI") or os.getenv("PYTEST_CURRENT_TEST"))
    if test_mode:
        app.config["TESTING"] = True
        app.config["RATE_LIMIT_ENABLED"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

    # Configure logging level/handler early so INFO diagnostics are emitted
    try:
        level_name = str(app.config.get("LOG_LEVEL", "INFO")).upper()
        level = getattr(logging, level_name, logging.INFO)
        app.logger.setLevel(level)
        # Ensure a StreamHandler exists (avoid duplicates)
        if not any(isinstance(h, logging.StreamHandler) for h in app.logger.handlers):
            sh = logging.StreamHandler()
            sh.setLevel(level)
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
            )
            sh.setFormatter(formatter)
            app.logger.addHandler(sh)
    except Exception:
        pass

    # Initialize Sentry (if DSN provided)
    try:
        dsn = os.getenv("SENTRY_DSN_BACKEND", "").strip()
        if dsn:
            sentry_sdk.init(
                dsn=dsn,
                integrations=[FlaskIntegration()],
                traces_sample_rate=float(
                    os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0") or 0
                ),
                profiles_sample_rate=float(
                    os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0") or 0
                ),
                environment=Config.ENVIRONMENT,
                release=Config.VERSION,
            )
            app.logger.info("Sentry initialized for backend")
    except Exception as e:
        # Non-fatal: continue without Sentry
        app.logger.warning(f"Sentry init failed: {e}")

    # Set SQLAlchemy database URI with explicit psycopg driver and SSL if needed
    if Config.DATABASE_URL:
        db_url = Config.DATABASE_URL
        # Normalize legacy scheme if present
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        # Force use of psycopg driver
        if "postgresql://" in db_url and "psycopg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

        # Append sslmode=require and a short connect_timeout for Postgres if not already present
        try:
            needs_ssl = (
                getattr(Config, "RENDER", False)
                or str(getattr(Config, "ENVIRONMENT", "")).lower() == "production"
            )
            parsed = urlparse(db_url)
            # Only mutate query params for Postgres URLs; preserve sqlite formatting (e.g., sqlite:///)
            if parsed.scheme.startswith("postgresql"):
                query_items = dict(parse_qsl(parsed.query)) if parsed.query else {}
                lower_keys = {k.lower() for k in query_items.keys()}
                if needs_ssl and "sslmode" not in lower_keys:
                    query_items["sslmode"] = "require"
                # Ensure a short connect timeout for Postgres to prevent long hangs
                if "connect_timeout" not in lower_keys:
                    query_items["connect_timeout"] = "2"
                new_query = urlencode(query_items)
                parsed = parsed._replace(query=new_query)
                db_url = urlunparse(parsed)
            else:
                # Non-Postgres schemes (e.g., sqlite) are left untouched
                pass
        except Exception as e:
            app.logger.warning(f"Failed to process DB URL SSL params: {e}")

        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///instance/mental_health.db"

    # SQLAlchemy reliability options
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Define base engine options
    engine_options = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    # Add pooling options only for non-SQLite databases (Postgres/MySQL)
    # SQLite (especially in-memory) doesn't support these pool arguments with StaticPool
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not db_uri.startswith("sqlite"):
        engine_options.update({
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 2,
        })
        
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options

    # Log effective DB URL (masked) and attempt DNS resolution of host
    try:
        effective_url = app.config.get("SQLALCHEMY_DATABASE_URI")

        def _mask_db_url(url: str) -> str:
            try:
                # For sqlite, return as-is to preserve triple slashes in logs (e.g., sqlite:///file.db)
                if isinstance(url, str) and url.strip().lower().startswith("sqlite:"):
                    return url
                p = urlparse(url)
                netloc = p.netloc
                if "@" in netloc:
                    creds, host = netloc.split("@", 1)
                    if ":" in creds:
                        user, _pwd = creds.split(":", 1)
                        creds_masked = f"{user}:***"
                    else:
                        creds_masked = f"{creds}:***"
                    netloc_masked = f"{creds_masked}@{host}"
                else:
                    netloc_masked = netloc
                return urlunparse(
                    (p.scheme, netloc_masked, p.path, p.params, p.query, p.fragment)
                )
            except Exception:
                return "<mask_failed>"

        masked = _mask_db_url(effective_url) if effective_url else "None"
        app.logger.info(f"Database URL (masked): {masked}")

        # DNS resolution info
        if effective_url:
            p = urlparse(effective_url)
            # Skip DNS resolution for sqlite
            if p.scheme and p.scheme.lower().startswith("sqlite"):
                pass
            else:
                host = p.hostname
                if host:
                    try:
                        addr_list = socket.getaddrinfo(host, None)
                        ips = sorted(
                            {
                                item[4][0]
                                for item in addr_list
                                if item and item[4] and item[4][0]
                            }
                        )
                        app.logger.info(
                            f"DB host '{host}' resolves to: {', '.join(ips)}"
                        )
                    except Exception as e:
                        app.logger.warning(
                            f"DNS resolution failed for DB host '{host}': {e}"
                        )
    except Exception as e:
        app.logger.warning(f"Failed to log DB URL or DNS info: {e}")

    # AI startup diagnostics
    try:
        debug_flag = (os.getenv("AI_DEBUG_LOGS") or "").lower() == "true"
        available = _provider_keys_available()
        configured = str(app.config.get("AI_PROVIDER", "gemini")).lower()
        chain = []
        try:
            with app.app_context():
                chain = _build_failover_chain()
        except Exception:
            # Build a best-effort chain without app context
            default_order = ["gemini", "openai", "perplexity"]
            if available.get(configured):
                chain.append(configured)
            for p in default_order:
                if available.get(p) and p not in chain:
                    chain.append(p)
        app.logger.info(
            f"AI startup: AI_DEBUG_LOGS={debug_flag} configured={configured} available={available} failover_chain={chain}"
        )
    except Exception as e_diag:
        app.logger.warning(f"AI startup diagnostics failed: {e_diag}")

    # Initialize extensions
    _init_extensions(app)

    # Initialize database tables
    _init_database(app)

    # Register routes
    _register_routes(app)
    _register_additional_routes(app)

    # Register Community (Phase 0) routes
    try:
        register_community_routes(app)
        app.logger.info("Community routes registered")
    except Exception as e:
        app.logger.warning(f"Community routes failed to register: {e}")

    # Register Nuclear Brain Telegram Integration
    try:
        from brain_telegram import (
            send_telegram_alert, 
            process_telegram_message,
            handle_status_command,
            handle_sprint_command,
            handle_tasks_command,
            load_state,
            emit_event
        )
        
        TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
        
        @app.route("/api/brain/telegram/webhook", methods=["POST"])
        def brain_telegram_webhook():
            """Handle incoming Telegram updates for Nuclear Brain"""
            try:
                data = request.get_json()
                message = data.get("message", {})
                chat_id = str(message.get("chat", {}).get("id", ""))
                
                # Security: Only respond to authorized chat
                if chat_id != TG_CHAT_ID:
                    return jsonify({"ok": False, "error": "Unauthorized"}), 403
                
                response_text = process_telegram_message(message)
                send_telegram_alert(response_text)
                
                return jsonify({"ok": True})
            except Exception as e:
                app.logger.error(f"Telegram webhook error: {e}")
                return jsonify({"ok": False, "error": "Webhook processing failed"}), 500

        @app.route("/api/brain/status", methods=["GET"])
        def brain_status():
            """Get Nuclear Brain status via API"""
            try:
                state = load_state()
                return jsonify(state)
            except Exception as e:
                app.logger.error(f"Brain status error: {e}")
                return jsonify({"error": "Failed to load brain status"}), 500
        
        @app.route("/api/brain/alert", methods=["POST"])
        def brain_alert():
            """Send alert to founder's Telegram"""
            data = request.get_json() or {}
            msg = data.get("message", "Alert from Nuclear Brain")
            success = send_telegram_alert(msg)
            return jsonify({"ok": success})
        
        @app.route("/api/brain/sprint", methods=["POST"])
        def brain_sprint():
            """Start new sprint via API"""
            data = request.get_json() or {}
            goal = data.get("goal", "")
            if not goal:
                return jsonify({"error": "Goal required"}), 400
            result = handle_sprint_command(goal)
            # Alert founder
            send_telegram_alert(f"🚀 New Sprint Started via API\n\n{goal}")
            return jsonify({"ok": True, "message": result})

        @app.route("/api/swarms", methods=["GET"])
        def get_swarms():
            """Get active swarms state"""
            try:
                from pathlib import Path
                # Determine brain path
                brain_path = Path(os.getenv("NUCLEUS_BRAIN_PATH", ".brain"))
                state_file = brain_path / "swarms" / "state.json"
                
                swarms_list = []
                if state_file.exists():
                    state = json.loads(state_file.read_text())
                    for mid, mdata in state.items():
                        # Adapt data model for frontend
                        mdata['session_id'] = mid
                        if 'agents' not in mdata:
                            # Show lead and implied squad
                            # MVP: just show lead
                            mdata['agents'] = [mdata.get('lead', 'Unknown')]
                        swarms_list.append(mdata)
                        
                return jsonify({"swarms": swarms_list})
            except Exception as e:
                app.logger.error(f"Failed to get swarms: {e}")
                return jsonify({"error": str(e)}), 500

        @app.route("/api/brain/sync", methods=["POST"])
        def brain_sync_state():
             """Sync local brain state to production"""
             try:
                 from pathlib import Path
                 state_data = request.get_json()
                 if not state_data:
                     return jsonify({"error": "No data provided"}), 400

                 # Write to file where brain_telegram reads
                 brain_root = Path(app.root_path) / ".brain"
                 ledger_dir = brain_root / "ledger"
                 ledger_dir.mkdir(parents=True, exist_ok=True)
                 
                 save_path = ledger_dir / "state.json"
                 with open(save_path, "w") as f:
                     json.dump(state_data, f, indent=4)
                 
                 app.logger.info(f"Brain state synced to {save_path}")
                 return jsonify({"ok": True, "message": "State synced"})
             except Exception as e:
                 app.logger.error(f"Sync failed: {e}")
                 return jsonify({"ok": False, "error": str(e)}), 500
        
        app.logger.info("Nuclear Brain Telegram routes registered (/api/brain/*)")
    except Exception as e:
        import traceback
        app.logger.error(f"Brain Telegram routes failed to register: {e}\n{traceback.format_exc()}")

    # DEBUG: Expose import failure reason (admin-only)
    @app.route("/api/brain/debug_import")
    def debug_brain_import():
        token = request.headers.get("X-Admin-Token") or ""
        expected = app.config.get("ADMIN_API_TOKEN") or ""
        if not expected or not secrets.compare_digest(token, expected):
            return jsonify({"error": "Unauthorized"}), 401
        import traceback
        try:
            import brain_telegram
            return "Import Successful! If routes are 404, check route registration logic."
        except Exception:
            return traceback.format_exc()



    # Initialize Memory System (Phase II)
    try:
        from providers.memory import init_memory_tables, MEMORY_ENABLED

        if MEMORY_ENABLED:
            if init_memory_tables(app):
                app.logger.info("Memory system initialized with pgvector")
            else:
                app.logger.info(
                    "Memory system running without pgvector (fallback mode)"
                )
    except Exception as e:
        app.logger.warning(f"Memory system initialization skipped: {e}")

    # Initialize Brain State Tables (for Telegram/Nucleus integration)
    try:
        with app.app_context():
            from providers.brain_state import init_brain_tables
            if init_brain_tables():
                app.logger.info("Brain state tables initialized")
    except Exception as e:
        app.logger.warning(f"Brain state initialization skipped: {e}")

    # Initialize Database via ORM
    _init_database(app)

    # Initialize Enterprise Features
    enterprise_routes_registered = False
    if ENTERPRISE_FEATURES:
        try:
            integrate_with_app(app)
            # If the integration module defined these endpoints, avoid double registration
            enterprise_routes_registered = (
                "enterprise_status" in app.view_functions
                and "enterprise_metrics" in app.view_functions
            )
            app.logger.info("✅ Enterprise features integrated successfully")
        except Exception as e:
            app.logger.warning(f"⚠️ Enterprise features integration failed: {e}")
    else:
        app.logger.info("ℹ️ Enterprise features not enabled")

    # Add enterprise endpoints directly only if they weren't provided by integrations
    if not enterprise_routes_registered:

        @app.route("/api/enterprise/status")
        def enterprise_status():
            """Enterprise status endpoint"""
            return jsonify(
                {
                    "status": "active",
                    "features": {
                        "ai_optimization": os.getenv(
                            "ENABLE_AI_OPTIMIZATION", "false"
                        ).lower()
                        == "true",
                        "clinical_detection": os.getenv(
                            "ENABLE_CLINICAL_DETECTION", "false"
                        ).lower()
                        == "true",
                        "revenue_system": os.getenv(
                            "ENABLE_REVENUE_SYSTEM", "false"
                        ).lower()
                        == "true",
                        "security_encryption": os.getenv(
                            "ENABLE_SECURITY_ENCRYPTION", "false"
                        ).lower()
                        == "true",
                        "distributed_scale": os.getenv(
                            "ENABLE_DISTRIBUTED_SCALE", "false"
                        ).lower()
                        == "true",
                    },
                    "version": "2.0.0",
                    "environment": os.getenv("ENVIRONMENT", "production"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

        @app.route("/api/enterprise/metrics")
        def enterprise_metrics():
            """Enterprise metrics endpoint"""
            return jsonify(
                {
                    "status": "active",
                    "metrics": {
                        "uptime": True,
                        "health": "healthy",
                        "version": "2.0.0",
                    },
                }
            )

    # Attach request ID and start timer for latency tracking
    @app.before_request
    def _attach_request_id():
        try:
            g.request_start = time.monotonic()
            rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
            g.request_id = rid
            # Also set as Sentry tag if available
            try:
                sentry_sdk.set_tag("request_id", rid)
            except Exception:
                pass
        except Exception:
            pass

    @app.after_request
    def _add_request_id_header(resp):
        try:
            rid = getattr(g, "request_id", None)
            if rid:
                resp.headers["X-Request-ID"] = rid
            # Log slow requests (> 5s) for monitoring
            start = getattr(g, "request_start", None)
            if start:
                elapsed_ms = int((time.monotonic() - start) * 1000)
                resp.headers["X-Response-Time"] = str(elapsed_ms)
                if elapsed_ms > 5000 and request.path.startswith("/api/"):
                    app.logger.warning(f"Slow request: {request.method} {request.path} {elapsed_ms}ms")
        except Exception:
            pass
        return resp

    # Global error handlers — return JSON for API routes, HTML for browser
    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        return render_template("landing.html"), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(413)
    def handle_413(e):
        return jsonify({"error": "Request too large", "max_bytes": 5 * 1024 * 1024}), 413

    @app.errorhandler(429)
    def handle_429(e):
        return jsonify({"error": "Rate limit exceeded", "retry_after": e.description}), 429

    @app.errorhandler(500)
    def handle_500(e):
        app.logger.error(f"Internal error: {e}")
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500
        return "Internal server error", 500

    return app


def _init_database(app: Flask) -> None:
    """Initialize database with tables (SQLAlchemy ORM)"""
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables initialized successfully via SQLAlchemy")
        except Exception as e:
            app.logger.error(f"Database initialization error: {e}")
            # Do NOT crash app during startup; continue and let health endpoint report DB status
            app.logger.warning("Continuing without full DB initialization. Check health endpoint.")


def _init_extensions(app: Flask) -> None:
    """Initialize Flask extensions with proper error handling"""
    try:
        # Initialize database
        db.init_app(app)

        # Initialize session management
        _setup_session(app)

        # Initialize rate limiter
        app.limiter = _setup_rate_limiter(app)

        # Setup CORS
        _setup_cors(app)

        app.logger.info(
            f"All extensions initialized successfully for environment: {app.config.get('ENVIRONMENT')}"
        )

    except Exception as e:
        app.logger.error(f"Failed to initialize extensions: {e}")
        raise


def _setup_session(app: Flask) -> None:
    """Configure session management with Redis fallback"""
    redis_url = app.config.get("REDIS_URL")

    if redis_url and redis_url != "port" and redis_url.strip():
        try:
            # Use short socket timeouts so Redis cannot hang requests
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
            app.logger.warning(
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


_CHAT_LOG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".brain", "ledger", "chat_requests.jsonl"
)
_chat_log_lock = threading.Lock()


def _log_chat_request(
    session_id: str,
    prompt_len: int,
    response_len: int,
    latency_ms: int,
    status: int,
    model: str = "",
):
    """Append a single chat request/response record to chat_requests.jsonl."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "prompt_len": prompt_len,
        "response_len": response_len,
        "latency_ms": latency_ms,
        "status": status,
        "model": model,
    }
    try:
        with _chat_log_lock:
            with open(_CHAT_LOG_PATH, "a") as f:
                f.write(json.dumps(record) + "\n")
    except Exception:
        logging.getLogger(__name__).debug("chat request log write failed", exc_info=True)


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

    In most tests we effectively disable rate limits by using a unique key per
    request when RATE_LIMIT_ENABLED is false, while still allowing explicit
    rate-limiting tests to turn it back on.
    """
    # When rate limiting is disabled, return a unique key per request so we
    # never trip any limits.
    if not _rate_limit_enabled():
        return f"disabled:{request.remote_addr}:{time.time_ns()}"

    # In the test environment, key purely by remote address so repeated
    # requests from the same client exercise the limiter.
    try:
        env = (current_app.config.get("ENVIRONMENT") or "").lower()
    except Exception:
        env = ""

    if env == "test":
        return get_remote_address()

    # Normal behavior: prefer per-session limiting; fall back to client IP.
    try:
        sid = request.headers.get("X-Session-ID")
        if sid and sid.strip():
            return f"sid:{sid.strip()}"
    except Exception:
        pass
    return get_remote_address()


def _setup_rate_limiter(app: Flask) -> None:
    """Configure rate limiting"""
    from extensions import limiter
    
    # Choose storage based on Redis availability to avoid blocking when Redis is down
    storage_uri = "memory://"
    try:
        if (
            app.config.get("SESSION_TYPE") == "redis"
            and app.config.get("SESSION_REDIS") is not None
        ):
            storage_uri = app.config.get("REDIS_URL", "memory://")
    except Exception:
        pass

    # Configure Limiter via app config
    app.config["RATELIMIT_STORAGE_URI"] = storage_uri
    app.config["RATELIMIT_DEFAULT"] = "5000 per day; 1000 per hour"
    
    limiter.init_app(app)
    # Assign key_func manually as init_app doesn't accept it
    limiter._key_func = _rate_limit_key
    app.limiter = limiter
    return limiter


def _setup_cors(app: Flask) -> None:
    """Configure CORS with security best practices"""
    origins = app.config.get("CORS_ORIGINS") or [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://localhost:9100",
        "http://127.0.0.1:9100",
    ]
    # In local environment, also allow any localhost/127.0.0.1 port to avoid dev port hassle
    try:
        if Config.ENVIRONMENT == "local" or Config.DOCKER_ENV:
            # Append regex origins that match any port on localhost/127.0.0.1
            origins = list(origins) + [
                re.compile(r"^http://localhost:\d+$"),
                re.compile(r"^http://127\.0\.0\.1:\d+$"),
            ]
    except Exception:
        # Non-fatal: fall back to explicit origins only
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
    """Add security headers to all responses"""
    @app.after_request
    def add_security_headers(response: Response) -> Response:
        # HSTS (Strict-Transport-Security)
        # Enforce HTTPS in production.
        # Max-age: 1 year (31536000 seconds)
        # includeSubDomains: Apply to all subdomains (api., app., etc.)
        # preload: Allow inclusion in browser HSTS preload list
        if app.config.get("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # X-Content-Type-Options
        # Prevent MIME-type sniffing (security requirement)
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options
        # Prevent clickjacking. Allow same origin for iframe embedding (if needed)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        
        # X-XSS-Protection
        # Enable XSS filtering in modern browsers (legacy but good to have)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy
        # Control how much referrer info is sent with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content-Security-Policy (CSP)
        # A basic policy to upgrade insecure requests.
        # NOTE: A full CSP requires careful tuning to avoid breaking scripts.
        # Currently, we only enforce HTTPS upgrade.
        if "Content-Security-Policy" not in response.headers:
             response.headers["Content-Security-Policy"] = "upgrade-insecure-requests"
             
        # Permissions-Policy (formerly Feature-Policy)
        # Disable sensitive features by default
        if "Permissions-Policy" not in response.headers:
            response.headers["Permissions-Policy"] = (
                "geolocation=(), microphone=(), camera=(), payment=()"
            )

        return response


def _register_routes(app: Flask) -> None:
    """Register all application routes"""

    @app.before_request
    def ensure_session_id_is_str():
        """Ensure session ID is always a string for consistency"""
        session_id = request.headers.get("X-Session-ID")
        if session_id and not isinstance(session_id, str):
            request.headers["X-Session-ID"] = str(session_id)

    def _serve_app_logic():
        """Shared logic to serve the Flutter web app or fallback."""
        app.logger.info(
            f"Serving app logic. Environment: {app.config.get('ENVIRONMENT')}"
        )
        if os.path.exists(app.static_folder) and os.path.exists(
            os.path.join(app.static_folder, "index.html")
        ):
            return send_from_directory(app.static_folder, "index.html")
        else:
            return jsonify(
                {
                    "message": "GentleQuest AI Mental Health Assistant",
                    "status": "running",
                    "environment": app.config.get("ENVIRONMENT", "development"),
                }
            )

    # Security Headers
    _setup_security_headers(app)

    # Register Blueprints
    try:
        from app_quest_routes import quest_bp
        app.register_blueprint(quest_bp)
        app.logger.info("Quest Blueprint registered successfully")
    except Exception as e:
        app.logger.error(f"Failed to register Quest Blueprint: {e}")

    # Register Resource Routes
    try:
        from app_resource_routes import register_resource_routes
        register_resource_routes(app)
        app.logger.info("Resource Routes registered successfully")
    except Exception as e:
        app.logger.error(f"Failed to register Resource Routes: {e}")

    # Register Alert Routes
    try:
        from app_alert_routes import register_alert_routes
        register_alert_routes(app)
        app.logger.info("Alert Routes registered successfully")
    except Exception as e:
        app.logger.error(f"Failed to register Alert Routes: {e}")

    # Register Clinical Dashboard
    if DASHBOARD_AVAILABLE:
        try:
            app.register_blueprint(clinical_dashboard)
            app.logger.info("Clinical Dashboard Blueprint registered successfully")
        except Exception as e:
            app.logger.error(f"Failed to register Clinical Dashboard Blueprint: {e}")
    else:
        app.logger.info("Clinical Dashboard skipped: DASHBOARD_AVAILABLE is False")

    @app.route("/clinical")
    @app.route("/clinical-dashboard")
    def serve_clinical_dashboard():
        """Serve the Clinical Dashboard for university admins."""
        return send_from_directory("static", "clinical-dashboard.html")

    @app.route("/health")
    def health_check():
        """Simple health check for Render/K8s"""
        return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200

    @app.route("/")
    def landing_page():
        """Serve the 'Quiet Launch' landing page, or the App if strictly on 'app.*' domain."""
        host = request.headers.get("Host", "").lower()
        # If accessing via app.gentlequest.app (or similar app.*), serve the Flutter app
        if host.startswith("app.") or host.startswith("nucleus."):
            return _serve_app_logic()
        
        # Otherwise, serve the marketing landing page
        return render_template("landing.html")

    @app.route("/api/assessment/<assessment_type>/questions", methods=["GET"])
    def get_assessment_questions_route(assessment_type):
        """Get questions for a specific assessment type"""
        try:
            questions = get_assessment_questions(assessment_type)
            return jsonify(questions)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.error(f"Error fetching assessment questions: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/assessment/<assessment_type>", methods=["POST"])
    def submit_assessment(assessment_type):
        """Submit and score an assessment"""
        try:
            # Check header first, then JSON body for session_id (Standardizing across clients)
            data = request.get_json() or {}
            session_id = request.headers.get("X-Session-ID") or data.get("session_id")
            
            if not session_id:
                return jsonify({"error": "Session ID required"}), 401
                
            responses = data.get("responses")
            if responses is None:
                return jsonify({"error": "Responses array required"}), 400
                
            # 1. Validate
            from providers.clinical_assessments import validate_responses, score_phq9, score_gad7
            is_valid, error = validate_responses(assessment_type, responses)
            if not is_valid:
                return jsonify({"error": error}), 400
                
            # 2. Score
            if assessment_type == "phq9":
                result = score_phq9(responses)
            elif assessment_type == "gad7":
                result = score_gad7(responses)
            else:
                 return jsonify({"error": f"Unknown assessment type: {assessment_type}"}), 400
            
            # 3. Save using Provider (ORM enabled)
            from providers.clinical_assessments import save_assessment_result
            new_id = save_assessment_result(session_id, result)
            
            # AUTO-COMPLETE QUEST (Gamification Hook)
            try:
                from providers.quest_engine import QuestEngine
                QuestEngine.complete_quest_for_assessment(session_id, assessment_type)
            except Exception as qe:
                app.logger.error(f"Failed to auto-complete quest: {qe}")

            
            result["id"] = new_id

            # 4. Trigger Alert if High Severity (Crisis Watchdog Integration)
            severity = result.get("severity", "minimal")
            requires_follow_up = result.get("requires_follow_up", False)
            
            # Map clinical severity to system risk levels
            risk_level = "low"
            risk_score = 0.0
            should_alert = False
            trigger_reason = f"Clinical Assessment: {assessment_type.upper()} Result"
            
            if assessment_type == "phq9":
                if requires_follow_up: # Suicidality logic (Q9 > 0)
                    risk_level = "crisis"
                    risk_score = 1.0
                    should_alert = True
                    trigger_reason += f" - Suicide Ideation Detected (Q9)"
                elif severity in ["severe", "moderately_severe"]:
                    risk_level = "high"
                    risk_score = 0.8
                    should_alert = True
                    trigger_reason += f" - {severity.replace('_', ' ').title()}"
                    
            elif assessment_type == "gad7":
                if severity == "severe":
                    risk_level = "high"  # GAD-7 Severe is significant but generally not immediate life threat like PHQ-9 Q9
                    risk_score = 0.7
                    should_alert = True
                    trigger_reason += f" - Severe Anxiety"

            if should_alert:
                try:
                    alert_id = AlertManager.create_alert(
                        session_id=session_id,
                        trigger_message=f"{trigger_reason}. Score: {result.get('total_score')}.",
                        risk_level=risk_level,
                        risk_score=risk_score,
                        keywords=[assessment_type.upper(), severity, "clinical_assessment"]
                    )
                    if alert_id:
                        # Attempt to send notification immediately
                        AlertManager.send_alert(alert_id)
                        app.logger.info(f"🚨 Clinical Alert Triggered: {alert_id} for session {session_id}")
                except Exception as alert_err:
                     app.logger.error(f"Failed to trigger clinical alert: {alert_err}")

            return jsonify(result)
            
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.error(f"Error submitting assessment: {e}", exc_info=True)
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/assessment/history", methods=["GET"])
    def get_assessment_history_route():
        """Get assessment history for the user"""
        try:
            session_id = request.headers.get("X-Session-ID")
            if not session_id:
                return jsonify({"error": "Session ID required"}), 401
            from providers.clinical_assessments import get_assessment_history
            history = get_assessment_history(session_id)
            return jsonify({"history": history})
        except Exception as e:
            app.logger.error(f"Error fetching history: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/app", methods=["GET"])
    def serve_app():
        """Serve the Flutter web app or fallback page (explicit route)."""
        return _serve_app_logic()

    @app.route("/.well-known/assetlinks.json")
    @app.limiter.exempt
    def assetlinks():
        """Serve assetlinks.json for Android App Links verification"""
        try:
            return send_from_directory(
                os.path.join(os.path.dirname(__file__), ".well-known"),
                "assetlinks.json",
                mimetype="application/json",
            )
        except FileNotFoundError:
            return jsonify({"error": "Asset links file not found"}), 404

    @app.route("/privacy")
    @app.route("/privacy/")
    @app.limiter.exempt
    def privacy_policy():
        """Serve privacy policy page for app stores"""
        privacy_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy - GentleQuest</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }
        h1 { color: #6366f1; }
        h2 { color: #4f46e5; margin-top: 2em; }
        .updated { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <h1>Privacy Policy</h1>
    <p class="updated">Last updated: January 2, 2026</p>
    
    <p>We respect your privacy. This Privacy Policy explains what we collect, why we collect it, 
    and how we handle your information when you use GentleQuest ("Service").</p>
    
    <h2>What We Collect</h2>
    <ul>
        <li>Messages you send to the assistant</li>
        <li>Technical metadata (timestamps, device/browser info, approximate location by country for crisis resources)</li>
        <li>Optional wellness/self-assessment inputs</li>
    </ul>
    
    <h2>How We Use Data</h2>
    <ul>
        <li>Provide and improve the Service (e.g., generate responses, show country-specific crisis resources)</li>
        <li>Maintain security and reliability (e.g., rate limiting, abuse prevention)</li>
        <li>Troubleshoot and measure basic usage, in aggregate</li>
    </ul>
    
    <h2>Data Retention</h2>
    <ul>
        <li>Messages: up to 30 days</li>
        <li>Sessions (inactive): up to 14 days</li>
        <li>Error logs: up to 14 days (or provider defaults)</li>
        <li>Aggregated/anonymized analytics: up to 90 days</li>
    </ul>
    <p>We retain data only as long as necessary for the purposes above.</p>
    
    <h2>Data Sharing</h2>
    <ul>
        <li>We do not sell your personal data.</li>
        <li>We may use third-party processors (e.g., AI providers, hosting) subject to confidentiality and data protection obligations.</li>
        <li>We avoid sending PII to providers; please don't include sensitive identifiers in messages.</li>
    </ul>
    
    <h2>Your Choices</h2>
    <ul>
        <li>You may request export or deletion of your data using the in-app Settings > Safety & Legal section.</li>
        <li>You can stop using the Service at any time; retention continues only as described above.</li>
    </ul>
    
    <h2>Safety Notice</h2>
    <p>This Service is not medical care. In an emergency or crisis, contact local emergency services. 
    Crisis resources may be shown based on your country.</p>
    
    <h2>Changes</h2>
    <p>We may update this Policy. Continued use indicates acceptance of the updated Policy.</p>
    
    <h2>Contact</h2>
    <p>For questions or requests, please refer to the in-app Settings > Safety & Legal section, 
    or contact us at <a href="mailto:support@gentlequest.app">support@gentlequest.app</a>.</p>
</body>
</html>
        """
        return privacy_html, 200, {'Content-Type': 'text/html'}

    @app.route("/terms")
    @app.route("/terms/")
    @app.limiter.exempt
    def terms_of_service():
        """Serve terms of service page for app stores"""
        terms_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terms of Service - GentleQuest</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }
        h1 { color: #6366f1; }
        h2 { color: #4f46e5; margin-top: 2em; }
        .updated { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <h1>Terms of Service</h1>
    <p class="updated">Last updated: August 14, 2025</p>
    
    <p>Welcome to GentleQuest ("Service"). By using the Service, you agree to these Terms. If you do not agree, please discontinue use.</p>
    
    <h2>1. Not Medical Advice</h2>
    <p>The Service provides AI-generated wellness support and education only. It is not medical advice, diagnosis, or treatment. In an emergency or crisis, contact your local emergency number or country-specific crisis resources.</p>
    
    <h2>2. Eligibility</h2>
    <p>You must comply with applicable laws and use the Service for lawful purposes. Do not submit illegal, harmful, or personal data you are not authorized to share.</p>
    
    <h2>3. Your Content</h2>
    <p>You are responsible for the content you submit. To operate and improve the Service, you grant us a limited license to process your content.</p>
    
    <h2>4. Privacy</h2>
    <p>See the Privacy Policy for how we collect, use, and retain data.</p>
    
    <h2>5. Data Retention and Deletion</h2>
    <p>We retain data as described in our Privacy Policy. You may request data export or deletion via the in-app settings.</p>
    
    <h2>6. Acceptable Use</h2>
    <p>No misuse, harassment, scraping, reverse engineering, or security testing without permission. Respect rate limits and system integrity.</p>
    
    <h2>7. Third-Party Services</h2>
    <p>We use infrastructure and AI providers. Your use is subject to their terms.</p>
    
    <h2>8. Disclaimers</h2>
    <p>The Service is provided "as is" without warranties. We do not guarantee accuracy, availability, or fitness for a particular purpose.</p>
    
    <h2>9. Limitation of Liability</h2>
    <p>To the maximum extent permitted by law, we are not liable for indirect, incidental, or consequential damages.</p>
    
    <h2>10. Changes</h2>
    <p>We may update these Terms. Continued use means you accept the updated Terms.</p>
    
    <h2>11. Contact</h2>
    <p>For questions or requests, please refer to the in-app Settings > Safety & Legal section, or contact us at <a href="mailto:support@gentlequest.app">support@gentlequest.app</a>.</p>
</body>
</html>
        """
        return terms_html, 200, {'Content-Type': 'text/html'}



    @app.route("/api/health", methods=["GET"])
    @app.limiter.exempt
    def health():
        """Enhanced health check endpoint with environment info"""
        try:
            # Check database and Redis with timing to detect hangs
            t0 = time.monotonic()
            db_status = _check_database_health()
            db_ms = int((time.monotonic() - t0) * 1000)

            t1 = time.monotonic()
            redis_status = _check_redis_health()
            redis_ms = int((time.monotonic() - t1) * 1000)

            t2 = time.monotonic()
            ollama_status = _check_ollama_health()
            ollama_ms = int((time.monotonic() - t2) * 1000)

            overall = "healthy"
            if ("unhealthy" in db_status.lower()) or (
                "unhealthy" in str(redis_status).lower()
            ):
                overall = "degraded"

            health_data = {
                "status": overall,
                "timestamp": datetime.utcnow().isoformat(),
                "environment": app.config.get("ENVIRONMENT"),
                "port": app.config.get("PORT"),
                "provider": app.config.get("AI_PROVIDER"),
                "database": db_status,
                "redis": redis_status,
                "ollama": ollama_status,
                "latency_ms": {
                    "db_check": db_ms,
                    "redis_check": redis_ms,
                    "ollama_check": ollama_ms,
                },
                "cors_enabled": True,
                "cors_origins": app.config.get("CORS_ORIGINS", []),
                "deployment": {
                    "platform": _detect_platform(),
                    "environment": app.config.get("ENVIRONMENT"),
                    "version": os.environ.get("VERSION", "1.0.0"),
                    "build_time": os.environ.get(
                        "BUILD_TIME", datetime.utcnow().isoformat()
                    ),
                },
                "endpoints": [
                    "/api/health",
                    "/api/chat",
                    "/api/chat_stream",
                    "/api/get_or_create_session",
                    "/api/chat_history",
                    "/api/mood_history",
                    "/api/mood_entry",
                    "/api/self_assessment",
                    "/api/analytics/log",
                    "/api/analytics/overview",
                    "/api/analytics/interventions",
                    "/api/analytics/user/<session_id>",
                    "/api/analytics/function-calling",
                    "/api/intervention/outcome",
                    "/api/admin/analytics",
                    "/api/memory/status",
                    "/api/metrics",
                ],
            }
            try:
                rid = getattr(g, "request_id", None)
            except Exception:
                rid = None
            app.logger.info(
                f"health endpoint status={overall} db={db_status} db_ms={db_ms} redis={redis_status} redis_ms={redis_ms} rid={rid}"
            )

            return jsonify(health_data), 200

        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return jsonify({"status": "unhealthy", "error": str(e)}), 500

    @app.route("/api/ping", methods=["GET", "HEAD"])
    @app.limiter.exempt
    def ping():
        """Ultra-lightweight keep-alive endpoint. Does not touch DB or Redis."""
        try:
            resp = jsonify({"ok": True, "ts": datetime.utcnow().isoformat()})
            resp.headers["Cache-Control"] = "no-store"
            return resp, 200
        except Exception:
            # Always return 200 to avoid failing external pingers
            return jsonify({"ok": False}), 200

    @app.route("/api/deploy-test", methods=["GET"])
    @app.limiter.exempt
    def deploy_test():
        """Simple deploy verification endpoint"""
        return (
            jsonify(
                {
                    "ok": True,
                    "version": app.config.get("VERSION"),
                    "environment": app.config.get("ENVIRONMENT"),
                }
            ),
            200,
        )

    @app.route("/api/compliance/log", methods=["POST"])
    @app.limiter.limit("60 per minute")
    def log_compliance_event():
        """Log compliance check outcomes from Flutter for funnel analysis."""
        data = request.get_json() or {}
        event_type = data.get("event_type", "")
        session_id = _get_or_create_session()
        ALLOWED = {
            "gps_timeout", "gps_permission_denied", "gps_services_disabled",
            "gps_mock_detected", "compliance_passed", "compliance_blocked_region",
            "compliance_error", "compliance_age_blocked", "compliance_web_blocked",
        }
        if event_type not in ALLOWED:
            return jsonify({"error": "invalid event_type"}), 400
        background_executor.submit(
            _log_analytics_event, current_app._get_current_object(),
            session_id, f"compliance_{event_type}", data.get("metadata", {})
        )
        return jsonify({"ok": True}), 201

    @app.route("/api/compliance/ip-region-check", methods=["GET"])
    @app.limiter.limit("10 per minute")
    def ip_region_check():
        """IP-based region fallback when GPS fails. Returns region + blocked status."""
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not ip:
            ip = request.headers.get("X-Real-IP", "")
        if not ip:
            ip = request.remote_addr

        try:
            if ip in ["127.0.0.1", "localhost", "::1"] or ip.startswith(("10.", "172.", "192.168.")):
                return jsonify({"region": "unknown", "country": "unknown", "blocked": False, "method": "ip_fallback"}), 200

            # Validate IP format before external call (SSRF prevention)
            import ipaddress as _ipaddress
            try:
                _ipaddress.ip_address(ip)
            except ValueError:
                return jsonify({"region": "unknown", "country": "unknown", "blocked": False, "method": "ip_fallback", "error": "invalid_ip"}), 200

            response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
            if response.status_code == 200:
                data = response.json()
                region = data.get("region", "")
                country = data.get("country", "").upper()

                # Same blocked list as Flutter compliance_service.dart
                HARD_BAN = {"Illinois"}
                PENDING = {"Utah", "Washington"}
                blocked = region in HARD_BAN or region in PENDING

                session_id = _get_or_create_session()
                background_executor.submit(
                    _log_analytics_event, current_app._get_current_object(),
                    session_id, "compliance_ip_fallback", {
                        "region": region, "country": country, "blocked": blocked, "ip_masked": ip[:8] + "***",
                    }
                )
                return jsonify({"region": region, "country": country, "blocked": blocked, "method": "ip_fallback"}), 200
        except Exception:
            pass

        return jsonify({"region": "unknown", "country": "unknown", "blocked": False, "method": "ip_fallback"}), 200

    @app.route("/api/chat", methods=["POST"])
    @app.limiter.limit("30 per minute")
    def chat():
        """Enhanced chat endpoint with geography-specific crisis detection"""
        try:
            import time as _time
            _t0 = _time.monotonic()
            data = request.get_json()
            if not data or "message" not in data:
                return jsonify({"error": "Message is required"}), 400

            session_id = _get_or_create_session()
            user_message = data["message"].strip()

            if not user_message:
                return jsonify({"error": "Message cannot be empty"}), 400

            if len(user_message) > 5000:
                return jsonify({"error": "Message too long (max 5000 characters)"}), 400

            # Detect first-time vs returning user (lightweight query)
            _is_first_message = Message.query.filter_by(
                session_id=session_id, is_user=True
            ).first() is None

            # Get country from request
            country = get_country_from_request(request)

            _t1 = _time.monotonic()
            # Process message with AI provider
            ai_response, risk_level, tool_calls = _process_chat_message(
                user_message, session_id, is_first_message=_is_first_message
            )
            _t2 = _time.monotonic()

            # Get geography-specific crisis data
            crisis_data = get_crisis_response_and_resources(risk_level, country)

            # Parallel Watchdog: Start deep clinical analysis in background (Scaling Crisis Detection)
            background_executor.submit(_run_crisis_watchdog, current_app._get_current_object(), user_message, session_id, risk_level)

            # Extract exercise data from tool calls (if any)
            exercise_data = {}
            for tc in tool_calls:
                result = tc.get("result", {})
                # Handle both intervention_type and exercise_type (agent_tools vs legacy)
                ex_type = result.get("intervention_type") or result.get("exercise_type")
                if result.get("interactive") and ex_type:
                    exercise_data = {
                        "interactive": True,
                        "exercise_type": ex_type,  # Normalize to exercise_type for Flutter
                        "exercise": result.get("exercise"),
                        "offer_stage": result.get("offer_stage", 1),  # Include stage for debugging
                        "function_call_source": tc.get("source", "gemini"),  # Track if Gemini or fallback
                    }
                    break  # Only include first exercise

            _t3 = _time.monotonic()
            response_data = {
                "response": ai_response,
                "risk_level": risk_level,
                "crisis_detected": risk_level == "crisis",
                "crisis_level": risk_level,
                "session_id": session_id,
                "crisis_msg": crisis_data["crisis_msg"],
                "crisis_numbers": crisis_data["crisis_numbers"],
                "is_first_conversation": _is_first_message,
                "conversation_count": _get_conversation_count(session_id),
            }

            # Increment conversation_count on first message of each conversation
            if _is_first_message:
                background_executor.submit(
                    _increment_conversation_count, current_app._get_current_object(), session_id
                )

            # Server-side behavioral event (fire-and-forget)
            _evt_type = "first_chat_message" if _is_first_message else "chat_message"
            background_executor.submit(
                _log_analytics_event, current_app._get_current_object(),
                session_id, _evt_type, {
                    "message_length": len(user_message),
                    "response_length": len(ai_response),
                    "latency_ms": round((_t3 - _t0) * 1000),
                    "has_exercise": bool(exercise_data),
                }
            )

            # Include timing only when ?debug=1
            if request.args.get("debug") == "1":
                response_data["_debug_timing"] = {
                    "setup_ms": round((_t1 - _t0) * 1000),
                    "llm_ms": round((_t2 - _t1) * 1000),
                    "post_ms": round((_t3 - _t2) * 1000),
                    "total_ms": round((_t3 - _t0) * 1000),
                    "inner": getattr(g, '_gemini_perf', {}),
                }

            # Merge exercise data if present
            if exercise_data:
                response_data.update(exercise_data)

            # Log request/response for training data
            _latency = round((_t3 - _t0) * 1000)
            _model = os.environ.get("AI_PROVIDER", "gemini")
            background_executor.submit(
                _log_chat_request, session_id, len(user_message),
                len(ai_response), _latency, 200, _model,
            )

            # --- SSE streaming mode: ?stream=true ---
            if request.args.get("stream") == "true":
                import re as _re

                def _sse_generator():
                    def sse(obj):
                        return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"

                    # 1. Meta event (crisis, session, exercise data)
                    meta = {
                        "type": "meta",
                        "session_id": session_id,
                        "risk_level": risk_level,
                        "crisis_msg": crisis_data["crisis_msg"],
                        "crisis_numbers": crisis_data["crisis_numbers"],
                        "is_first_conversation": _is_first_message,
                    }
                    if exercise_data:
                        meta.update(exercise_data)
                    yield sse(meta)

                    # 2. Stream response text as token events
                    text = ai_response or ""
                    if "\n" in text:
                        chunks = text.split("\n")
                        joiner = "\n"
                    else:
                        parts = [p for p in _re.split(r"(?<=[.!?])\s+", text) if p]
                        if len(parts) <= 1:
                            chunks = text.split(" ")
                            joiner = " "
                        else:
                            chunks = [
                                p + (" " if i < len(parts) - 1 else "")
                                for i, p in enumerate(parts)
                            ]
                            joiner = ""

                    for idx, ch in enumerate(chunks):
                        yield sse({
                            "type": "token",
                            "text": (joiner + ch) if (idx > 0 and joiner) else ch,
                        })

                    # 3. Done signal
                    yield sse({"type": "done"})

                return Response(
                    _sse_generator(),
                    headers={
                        "Content-Type": "text/event-stream",
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                    },
                )

            return (
                jsonify(response_data),
                200,
            )

        except Exception as e:
            from werkzeug.exceptions import HTTPException
            if isinstance(e, HTTPException):
                raise  # Let global error handlers handle 413, 429, etc.
            import traceback
            app.logger.error(f"Chat endpoint error: {e}")
            _err_latency = round((_time.monotonic() - _t0) * 1000) if '_t0' in dir() else 0
            _data = data if 'data' in dir() else None
            background_executor.submit(
                _log_chat_request, _data.get("session_id", "") if _data else "",
                len(_data.get("message", "")) if _data else 0, 0, _err_latency, 500,
            )
            trace = traceback.format_exc() if app.config.get("ENVIRONMENT") == "local" else None
            return jsonify({"error": "Internal server error", "trace": trace}), 500

    @app.route("/api/chat_stream", methods=["GET"])
    def chat_stream():
        """Server-Sent Events (SSE) streaming endpoint for chat responses.
        Accepts query params: message (required), country (optional), session_id (optional)
        Streams JSON objects with a 'type' field: 'meta', 'token', 'done', 'error'.
        """
        try:
            message = (request.args.get("message") or "").strip()
            if not message:
                return jsonify({"error": "Message is required"}), 400

            if len(message) > 5000:
                return jsonify({"error": "Message too long (max 5000 characters)"}), 400

            # Session handling: prefer provided session_id (from web EventSource cannot set headers)
            session_id = request.args.get("session_id") or _get_or_create_session()

            # Detect first-time user for warm greeting
            _is_first_msg = Message.query.filter_by(
                session_id=session_id, is_user=True
            ).first() is None

            # Country for geo-specific crisis resources (sanitize to alpha, max 10 chars)
            _raw_country = request.args.get("country") or "generic"
            country = "".join(c for c in _raw_country[:10] if c.isalpha()).lower() or "generic"

            # Crisis detection first
            risk_level = detect_crisis_level(message)
            crisis_data = get_crisis_response_and_resources(risk_level, country)

            # Parallel Watchdog: Start deep clinical analysis in background (Scaling Crisis Detection)
            background_executor.submit(_run_crisis_watchdog, current_app._get_current_object(), message, session_id, risk_level)

            # Generate AI response with tool support (function calling)
            full_text, actual_risk, tool_calls = _process_chat_message(
                message, session_id, is_first_message=_is_first_msg,
            )
            # Use detected risk level from the response if available
            if actual_risk:
                risk_level = actual_risk

            # Extract exercise data from tool calls (if any)
            exercise_data = {}
            for tc in tool_calls:
                result = tc.get("result", {})
                # Handle both intervention_type and exercise_type
                ex_type = result.get("intervention_type") or result.get("exercise_type")
                if result.get("interactive") and ex_type:
                    exercise_data = {
                        "interactive": True,
                        "exercise_type": ex_type,
                        "exercise": result.get("exercise"),
                    }
                    break

            def stream_generator():
                import time
                import json as _json

                def sse(obj: dict):
                    data = _json.dumps(obj, ensure_ascii=False)
                    return f"data: {data}\n\n"

                # Send initial metadata (risk/crisis info, session, and exercise data)
                meta_event = {
                    "type": "meta",
                    "session_id": session_id,
                    "risk_level": risk_level,
                    "crisis_msg": crisis_data.get("crisis_msg"),
                    "crisis_numbers": crisis_data.get("crisis_numbers", []),
                    "is_first_conversation": _is_first_msg,
                }
                # Include exercise data in meta if present
                if exercise_data:
                    meta_event.update(exercise_data)
                yield sse(meta_event)

                # Chunk the AI response for progressive reveal
                text = full_text or ""
                # Prefer newline splits, then sentence-ish (preserving spaces), then words
                chunks: List[str]
                joiner = ""
                if "\n" in text:
                    chunks = text.split("\n")
                    joiner = "\n"
                else:
                    import re as _re

                    parts = [p for p in _re.split(r"(?<=[.!?])\s+", text) if p]
                    if len(parts) <= 1:
                        chunks = text.split(" ")
                        joiner = " "
                    else:
                        # Re-attach a single space that was consumed by the split for all but the last part.
                        chunks = [
                            p + (" " if i < len(parts) - 1 else "")
                            for i, p in enumerate(parts)
                        ]

                try:
                    for idx, ch in enumerate(chunks):
                        yield sse(
                            {
                                "type": "token",
                                "text": (joiner + ch) if (idx > 0 and joiner) else ch,
                            }
                        )
                        # Small human-like pacing
                        delay_ms = max(60, min(220, int(len(ch.strip()) * 12)))
                        time.sleep(delay_ms / 1000.0)

                    # Done signal
                    yield sse({"type": "done"})
                except GeneratorExit:
                    # Client disconnected mid-stream — stop yielding immediately
                    return

            headers = {
                "Cache-Control": "no-cache",
                "Content-Type": "text/event-stream",
                "Connection": "keep-alive",
            }
            return Response(stream_generator(), headers=headers)

        except Exception as e:
            from werkzeug.exceptions import HTTPException
            if isinstance(e, HTTPException):
                raise
            current_app.logger.error(f"Chat stream error: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/get_or_create_session", methods=["GET"])
    @app.limiter.limit("60 per hour")
    def get_or_create_session_endpoint():
        """Get or create user session"""
        session_id = _get_or_create_session()
        return jsonify({"session_id": session_id})

    @app.route("/api/chat_history", methods=["GET"])
    @app.limiter.limit("120 per minute")
    def get_chat_history():
        """Get chat history for the current session"""
        try:
            session_id = request.headers.get("X-Session-ID")
            if not session_id:
                return jsonify({"error": "Session ID required"}), 400

            # Get chat messages from database via Message model
            messages = Message.query.filter_by(session_id=session_id)\
                .order_by(Message.timestamp.asc())\
                .limit(50).all()

            chat_history = []
            for message in messages:
                ts = message.timestamp
                if ts and hasattr(ts, 'isoformat'):
                    ts = ts.isoformat()
                    
                chat_history.append(
                    {
                        "content": message.content,
                        "is_user": message.is_user,
                        "timestamp": ts,
                    }
                )

            return jsonify(chat_history)

        except Exception as e:
            app.logger.error(f"Error getting chat history: {e}")
            return jsonify({"error": "Failed to get chat history"}), 500

    @app.route("/api/mood_history", methods=["GET"])
    @app.limiter.limit("120 per minute")
    def get_mood_history():
        """Get mood history for the current session"""
        try:
            session_id = request.headers.get("X-Session-ID")
            if not session_id:
                return jsonify({"error": "Session ID required"}), 400

            # Get mood entries from database via MoodEntry model
            entries = MoodEntry.query.filter_by(session_id=session_id)\
                .order_by(MoodEntry.timestamp.desc())\
                .limit(50).all()

            mood_history = []
            for entry in entries:
                ts = entry.timestamp
                if ts and not isinstance(ts, str) and hasattr(ts, 'isoformat'):
                    ts = ts.isoformat()
                    
                mood_history.append(
                    {
                        "mood_level": entry.mood_level,
                        "note": _sanitize_note(entry.note),
                        "timestamp": ts,
                    }
                )

            return jsonify(mood_history)

        except Exception as e:
            app.logger.error(f"Error getting mood history: {e}")
            return jsonify({"error": "Failed to get mood history"}), 500

    def _sanitize_note(note: str) -> str:
        """Basic XSS mitigation for free-text notes.

        This is intentionally conservative and focused on stripping raw
        script tags while preserving most of the user's text.
        """
        try:
            if not note:
                return note
            # Neutralize opening/closing script tags
            return note.replace("<script", "&lt;script").replace(
                "</script", "&lt;/script"
            )
        except Exception:
            # On any unexpected issue, return the original note rather than failing
            return note

    @app.route("/api/mood_entry", methods=["POST"])
    @app.limiter.limit("120 per minute")
    def add_mood_entry():
        """Add a new mood entry"""
        try:
            # Ensure session exists in DB (also syncs legacy 'sessions' table)
            session_id = _get_or_create_session()
            if not session_id:
                return jsonify({"error": "Session ID required"}), 400

            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400

            mood_level = data.get("mood_level")
            # Safe integer conversion
            try:
                if mood_level is not None:
                    mood_level = int(mood_level)
            except (ValueError, TypeError):
                 return jsonify({"error": "Invalid mood level format"}), 400

            note_raw = data.get("note", "")
            timestamp = data.get("timestamp")

            if (
                mood_level is None
                or not isinstance(mood_level, int)
                or mood_level < 1
                or mood_level > 5
            ):
                return jsonify({"error": "Invalid mood level (1-5 required)"}), 400

            # Parse timestamp if provided, otherwise use current time
            if timestamp:
                try:
                    entry_timestamp = datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00")
                    )
                except ValueError:
                    entry_timestamp = datetime.utcnow()
            else:
                entry_timestamp = datetime.utcnow()

            # Sanitize note to mitigate basic XSS vectors (e.g., raw <script> tags)
            note = _sanitize_note(note_raw)

            # Add mood entry via MoodEntry model
            entry = MoodEntry(
                session_id=session_id,
                mood_level=mood_level,
                note=note,
                timestamp=entry_timestamp
            )
            db.session.add(entry)
            db.session.commit()

            # Check valid feedback trigger (after 3rd check-in) via MoodEntry model
            check_in_count = MoodEntry.query.filter_by(session_id=session_id).count()
            
            show_feedback_prompt = (check_in_count == 3)

            return jsonify(
                {
                    "message": "Mood entry added successfully",
                    "mood_level": mood_level,
                    "note": note,
                    "timestamp": entry_timestamp.isoformat(),
                    "show_feedback_prompt": show_feedback_prompt,
                }
            )

        except Exception as e:
            from werkzeug.exceptions import HTTPException
            if isinstance(e, HTTPException):
                raise
            app.logger.error(f"Error adding mood entry: {e}")
            db.session.rollback()
            return jsonify({"error": "Failed to add mood entry"}), 500

    @app.route("/api/self_assessment", methods=["POST"])
    @app.limiter.limit("120 per minute")
    def submit_self_assessment():
        """Handle self-assessment submissions"""
        if request.method == "GET":
            return jsonify({"message": "Self-assessment endpoint ready"})

        try:
            data = request.get_json() or {}

            # Ensure session association
            session_id = _get_or_create_session()
            if not session_id:
                return jsonify({"error": "Session ID required"}), 400

            # Clean and validate data
            cleaned_data = {}
            required_fields = ["mood", "energy", "sleep", "stress"]

            for field in required_fields:
                value = data.get(field)
                if (
                    value is None
                    or value == ""
                    or str(value).lower() in ["null", "none"]
                ):
                    return jsonify({"error": f"Missing required field: {field}"}), 400
                cleaned_data[field] = value.strip() if isinstance(value, str) else value

            # Optional fields
            optional_fields = ["notes", "crisis_level", "anxiety_level"]
            for field in optional_fields:
                value = data.get(field)
                if value and value != "" and str(value).lower() not in ["null", "none"]:
                    cleaned_data[field] = (
                        value.strip() if isinstance(value, str) else value
                    )

            # Optional timezone offset in minutes to determine local "day" boundaries
            try:
                tz_offset_min = int(data.get("tz_offset_minutes") or 0)
            except Exception:
                tz_offset_min = 0

            now_utc = datetime.utcnow()
            # Compute start of local day and convert back to UTC
            now_local = now_utc + timedelta(minutes=tz_offset_min)
            start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
            start_of_day_utc = start_local - timedelta(minutes=tz_offset_min)

            # Enforce single completion per (local) day
            existing = (
                db.session.query(SelfAssessmentEntry)
                .filter(SelfAssessmentEntry.session_id == session_id)
                .filter(SelfAssessmentEntry.timestamp >= start_of_day_utc)
                .first()
            )

            if existing:
                app.logger.info(
                    f"Self-assessment already completed today | session_id={session_id} completed_at={existing.timestamp.isoformat()} tz_offset_min={tz_offset_min}"
                )
                return (
                    jsonify(
                        {
                            "success": True,
                            "already_completed_today": True,
                            "xp_awarded": 0,
                            "completed_at": existing.timestamp.isoformat(),
                        }
                    ),
                    200,
                )

            # Create new entry (authoritative store)
            entry = SelfAssessmentEntry(
                session_id=session_id,
                timestamp=now_utc,
                assessment_data=cleaned_data,
            )
            db.session.add(entry)
            db.session.commit()



            # Award XP once per day for quick check-in (value can be tuned server-side)
            xp_awarded = 10
            app.logger.info(
                f"Self-assessment recorded | session_id={session_id} xp_awarded={xp_awarded} tz_offset_min={tz_offset_min} data_keys={list(cleaned_data.keys())}"
            )

            return (
                jsonify(
                    {
                        "message": "Assessment recorded",
                        "success": True,
                        "already_completed_today": False,
                        "xp_awarded": xp_awarded,
                        "completed_at": now_utc.isoformat(),
                    }
                ),
                201,
            )

        except Exception as e:
            from werkzeug.exceptions import HTTPException
            if isinstance(e, HTTPException):
                raise
            app.logger.error(f"Self-assessment error: {e}")
            return jsonify({"error": "Failed to process assessment"}), 500

    @app.route("/api/mood_pulse", methods=["GET"])
    @app.limiter.limit("30 per minute")
    def mood_pulse():
        """Get anonymous aggregate mood stats for today - 'You Are Not Alone' feature"""
        try:
            # Get today's start in UTC
            today_start = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            # Count mood entries by level for today (across ALL users, anonymous) via MoodEntry model
            from sqlalchemy import func
            result = db.session.query(
                MoodEntry.mood_level, 
                func.count(MoodEntry.id).label('count')
            ).filter(MoodEntry.timestamp >= today_start)\
             .group_by(MoodEntry.mood_level).all()

            # Build distribution
            distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            total = 0
            for row in result:
                level = row.mood_level
                count = row.count
                if 1 <= level <= 5:
                    distribution[level] = count
                    total += count

            # Calculate percentages
            percentages = {}
            for level in range(1, 6):
                if total > 0:
                    percentages[level] = round((distribution[level] / total) * 100)
                else:
                    percentages[level] = 0

            # Friendly messages based on mood level
            solidarity_messages = {
                1: "You're not alone. Others are having a tough day too.",
                2: "Many people feel this way sometimes. You're not alone.",
                3: "Lots of us are feeling okay today. You're in good company.",
                4: "Others are feeling good too! The positive energy is spreading.",
                5: "You're part of the happiness today! Keep shining.",
            }

            return jsonify(
                {
                    "total_checkins_today": total,
                    "distribution": distribution,
                    "percentages": percentages,
                    "solidarity_messages": solidarity_messages,
                }
            )

        except Exception as e:
            app.logger.error(f"Mood pulse error: {e}")
            return jsonify({"error": "Failed to get mood pulse"}), 500

    @app.route("/api/crisis_detection", methods=["POST"])
    @app.limiter.limit("10 per minute")
    def crisis_detection():
        """Enhanced crisis detection with immediate response"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400

            message = data.get("message", "")
            session_id = request.headers.get("X-Session-ID")

            if not message:
                return jsonify({"error": "Message required"}), 400

            # Enhanced crisis detection
            risk_level, risk_score, keywords = _enhanced_crisis_detection(message)

            # Immediate response based on risk level
            response = _get_crisis_response(risk_level, risk_score)

            # Log crisis detection
            _log_crisis_detection(session_id, message, risk_level, risk_score, keywords)

            return jsonify(
                {
                    "risk_level": risk_level,
                    "risk_score": risk_score,
                    "keywords": keywords,
                    "response": response,
                    "immediate_action_required": risk_level in ["high", "crisis"],
                    "resources": _get_crisis_resources(risk_level),
                }
            )

        except Exception as e:
            app.logger.error(f"Crisis detection error: {e}")
            return jsonify({"error": "Failed to process crisis detection"}), 500

    @app.route("/api/mood_analytics", methods=["GET"])
    @app.limiter.limit("30 per minute")
    def mood_analytics():
        """Get mood analytics and trends"""
        try:
            session_id = request.headers.get("X-Session-ID")
            if not session_id:
                return jsonify({"error": "Session ID required"}), 400

            # Get mood entries from database
            # Get mood entries from database via MoodEntry model
            entries = MoodEntry.query.filter_by(session_id=session_id)\
                .order_by(MoodEntry.timestamp.desc())\
                .limit(100).all()

            if not entries:
                return jsonify(
                    {
                        "message": "No mood data available",
                        "analytics": {
                            "average_mood": 0,
                            "mood_trend": "stable",
                            "total_entries": 0,
                            "weekly_average": 0,
                            "mood_distribution": {},
                        },
                    }
                )

            # Calculate analytics
            mood_levels = [entry.mood_level for entry in entries]

            # Mood trend calculation
            recent_moods = mood_levels[:7] if len(mood_levels) >= 7 else mood_levels
            older_moods = mood_levels[7:14] if len(mood_levels) >= 14 else []

            if older_moods:
                recent_avg = sum(recent_moods) / len(recent_moods)
                older_avg = sum(older_moods) / len(older_moods)
                if recent_avg > older_avg + 0.5:
                    trend = "improving"
                elif recent_avg < older_avg - 0.5:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "stable"

            # Mood distribution
            mood_distribution = {}
            for level in range(1, 6):
                count = mood_levels.count(level)
                mood_distribution[f"level_{level}"] = count

            # Weekly average
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            def _get_ts(entry):
                ts = entry.timestamp
                if isinstance(ts, str):
                    try:
                        # SQLite might return "YYYY-MM-DD HH:MM:SS.mmmmmm"
                        return datetime.fromisoformat(ts.replace(' ', 'T'))
                    except Exception:
                        return datetime.min  # Fallback
                return ts

            weekly_entries = [entry for entry in entries if _get_ts(entry) >= week_ago]
            weekly_average = (
                sum(entry.mood_level for entry in weekly_entries) / len(weekly_entries)
                if weekly_entries
                else 0
            )

            return jsonify(
                {
                    "analytics": {
                        "average_mood": round(sum(mood_levels) / len(mood_levels), 2),
                        "mood_trend": trend,
                        "total_entries": len(entries),
                        "weekly_average": round(weekly_average, 2),
                        "mood_distribution": mood_distribution,
                        "recent_entries": len(recent_moods),
                    }
                }
            )

        except Exception as e:
            app.logger.error(f"Mood analytics error: {e}")
            return jsonify({"error": "Failed to get mood analytics"}), 500

    @app.route("/api/analytics/log", methods=["POST"])
    @app.limiter.limit("120 per minute")
    def log_analytics_event():
        """Minimal analytics logging endpoint.
        Requirements:
        - No PII is accepted or stored.
        - Requires X-Analytics-Consent: true header; otherwise noop (202).
        - Associates events to a session and request_id for traceability.
        """
        try:
            # Check consent header
            if request.headers.get("X-Analytics-Consent") != "true":
                return jsonify({"ok": True}), 201

            data = request.get_json(silent=True) or {}
            event_type = (data.get("event_type") or "").strip()
            if not event_type or len(event_type) > 64:
                return jsonify({"error": "Invalid event_type"}), 400

            # Allow only safe characters in event_type
            allowed = set(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-"
            )
            if any(ch not in allowed for ch in event_type):
                return jsonify({"error": "Invalid event_type"}), 400

            raw_meta = data.get("metadata") or {}
            metadata: Dict[str, Any] = {}
            if isinstance(raw_meta, dict):
                # Whitelist allowed keys and simple types only, trim long strings
                allowed_keys = {
                    # Generic analytics keys
                    "action",
                    "label",
                    "screen",
                    "source",
                    "value",
                    "count",
                    "duration_ms",
                    "success",
                    "code",
                    "provider",
                    # Quest telemetry contract keys (PII-free)
                    "quest_id",
                    "tag",
                    "surface",
                    "variant",
                    "ts",
                    "progress",
                    # UI context (non-PII)
                    "ui",
                }
                for k, v in raw_meta.items():
                    if k in allowed_keys and isinstance(v, (str, int, float, bool)):
                        if isinstance(v, str) and len(v) > 200:
                            v = v[:200]
                        metadata[k] = v

            # Ensure session exists and get ID
            session_id = _get_or_create_session()
            req_id = getattr(g, "request_id", None)

            # Store as compact JSON string in TEXT column to avoid dialect issues
            meta_json = json.dumps(metadata, separators=(",", ":"), ensure_ascii=False)

            # Store metadata
            event = AnalyticsEvent(
                session_id=session_id,
                event_type=event_type,
                event_metadata=metadata,
                request_id=req_id
            )
            db.session.add(event)
            db.session.commit()
            return jsonify({"ok": True}), 201
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Analytics log error: {e}")
            return jsonify({"error": "Failed to log analytics"}), 500

    @app.route("/api/analytics/recent", methods=["GET"])
    @app.limiter.limit("60 per minute")
    def analytics_recent():
        """Read-only: Fetch recent analytics events for debugging.
        Optional query params:
          - event_prefix: filter event_type with prefix (e.g., 'quest_')
          - limit: max records (default 50, max 200)
        """
        try:
            prefix = (request.args.get("event_prefix") or "").strip()
            try:
                limit = int(request.args.get("limit", "50"))
            except Exception:
                limit = 50
            limit = max(1, min(limit, 200))

            params: Dict[str, Any] = {"limit": limit}
            where_clause = ""
            query = AnalyticsEvent.query
            if prefix:
                query = query.filter(AnalyticsEvent.event_type.like(f"{prefix}%"))
            
            events_list = query.order_by(AnalyticsEvent.id.desc()).limit(limit).all()

            response_events = []
            for e in events_list:
                response_events.append({
                    "event_type": e.event_type,
                    "metadata": e.event_metadata,
                    "request_id": e.request_id,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None
                })

            return jsonify({
                "events": response_events,
                "count": len(response_events)
            })
        except Exception as e:
            app.logger.error(f"Analytics recent error: {e}")
            return jsonify({"error": "Failed to fetch analytics"}), 500

    @app.route("/api/admin/purge", methods=["POST"])
    @app.limiter.limit("5 per minute")
    def admin_purge():
        """Admin-only: Purge old data per retention policy.
        Requires header X-Admin-Token matching ADMIN_API_TOKEN.
        """
        token = request.headers.get("X-Admin-Token") or ""
        expected = app.config.get("ADMIN_API_TOKEN") or ""
        if not expected or not secrets.compare_digest(token, expected):
            return jsonify({"error": "Unauthorized"}), 401
        try:
            counts = _purge_old_data_inner()
            return jsonify({"success": True, "purged": counts}), 200
        except Exception as e:
            return jsonify({"error": "Purge failed", "details": str(e)}), 500

    @app.route("/api/admin/retention_config", methods=["GET"])
    def retention_config():
        """Admin-only: View effective retention configuration."""
        token = request.headers.get("X-Admin-Token") or ""
        expected = app.config.get("ADMIN_API_TOKEN") or ""
        if not expected or not secrets.compare_digest(token, expected):
            return jsonify({"error": "Unauthorized"}), 401
        return (
            jsonify(
                {
                    "message_retention_days": app.config.get("MESSAGE_RETENTION_DAYS"),
                    "session_retention_days": app.config.get("SESSION_RETENTION_DAYS"),
                    "error_log_retention_days": app.config.get(
                        "ERROR_LOG_RETENTION_DAYS"
                    ),
                    "analytics_retention_days": app.config.get(
                        "ANALYTICS_RETENTION_DAYS"
                    ),
                }
            ),
            200,
        )


def _get_or_create_session() -> str:
    """Get or create user session with proper error handling"""
    session_id = request.headers.get("X-Session-ID")

    if not session_id:
        session_id = str(uuid.uuid4())
    else:
        # Validate UUID format to prevent garbage input
        try:
            uuid.UUID(session_id)
        except ValueError:
            session_id = str(uuid.uuid4())

    try:
        from models import UserSession
        from flask import current_app

        session = db.session.get(UserSession, session_id)

        if not session:
            # Create new session (must be sync — downstream needs the row)
            new_session = UserSession(id=session_id)
            db.session.add(new_session)
            db.session.commit()
        else:
            # Defer last_active update to background (informational only)
            _app = current_app._get_current_object()
            background_executor.submit(_update_session_last_active, _app, session_id)

    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Session management error: {e}")

    return session_id


def _update_session_last_active(app_ctx, session_id: str):
    """Background: update session last_active timestamp."""
    try:
        with app_ctx.app_context():
            from models import UserSession
            session = db.session.get(UserSession, session_id)
            if session:
                session.last_active = datetime.utcnow()
                db.session.commit()
    except Exception:
        pass  # Non-critical — stale timestamp is acceptable


def _get_conversation_count(session_id: str) -> int:
    """Get the conversation count for a session (lightweight query)."""
    try:
        session = db.session.get(UserSession, session_id)
        return (session.conversation_count or 0) if session else 0
    except Exception:
        return 0


def _increment_conversation_count(app_ctx, session_id: str):
    """Background: increment conversation_count on UserSession."""
    try:
        with app_ctx.app_context():
            session = db.session.get(UserSession, session_id)
            if session:
                session.conversation_count = (session.conversation_count or 0) + 1
                db.session.commit()
    except Exception:
        pass  # Non-critical


def _log_analytics_event(app_ctx, session_id: str, event_type: str, metadata: dict = None):
    """Background: log a behavioral event to analytics_events table."""
    try:
        with app_ctx.app_context():
            from models import AnalyticsEvent
            event = AnalyticsEvent(
                session_id=session_id,
                event_type=event_type,
                event_metadata=metadata or {},
            )
            db.session.add(event)
            db.session.commit()
    except Exception:
        pass  # Non-critical — analytics should never block


def _call_llm_json(prompt: str, system_prompt: str = None) -> str:
    """
    Directly call Gemini for structured data (skips chat persona/history).
    Used for background analysis like crisis watchdog.
    Attempts multiple models in order of preference/speed.
    """
    import warnings as _w
    _w.filterwarnings("ignore", message=".*google.generativeai.*", category=FutureWarning)
    import google.generativeai as genai
    import os

    api_keys = (os.getenv("GEMINI_API_KEY") or "").split(",")
    if not api_keys[0]:
        return "{}"
        
    # Simple rotation for background tasks
    import random
    api_key = random.choice(api_keys).strip()
    
    # Fallback chain: Newest/Fastest -> Stable
    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]
    
    full_content = prompt
    if system_prompt:
        full_content = f"{system_prompt}\n\n{prompt}"
    
    try:
        genai.configure(api_key=api_key)
        
        last_error = None
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(full_content, request_options={"timeout": 60})
                if response and hasattr(response, "text"):
                    return response.text
            except Exception as e:
                # Capture error and try next model
                last_error = e
                continue
                
        # If we get here, all models failed
        if last_error:
            print(f"DEBUG: All models failed in _call_llm_json. Last error: {last_error}")
            
        return "{}"
    except Exception as e:
        print(f"DEBUG: _call_llm_json setup error: {e}")
        return "{}"

def _run_crisis_watchdog(flask_app, message: str, session_id: str, sync_risk: str):
    """
    Background worker: Uses an LLM to analyze the message for subtle crisis signs.
    If the LLM detects a higher risk than the synchronous keyword check, updates the record.
    """
    with flask_app.app_context():
        try:
            # 1. Skip if message is too short or already handled at 'crisis' level
            if len(message) < 5 or sync_risk == "crisis":
                return
            
            # 2. Call LLM for clinical analysis
            system_prompt = (
                "You are a clinical crisis detection specialist. Analyze student messages for subtle signs of crisis "
                "(hopelessness, finality, self-harm intention) that keyword matching might miss."
            )
            
            prompt = (
                f"Analyze this message: \"{message}\".\n"
                f"Respond ONLY with a valid JSON object: {{\"risk_level\": \"low\"|\"medium\"|\"high\"|\"crisis\", \"reason\": \"string\"}}"
            )
            
            response_text = _call_llm_json(prompt, system_prompt)
            
            # Clean up response (LLMs sometimes wrap JSON in code blocks)
            cleaned_json = response_text.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_json:
                cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()
            
            try:
                result = json.loads(cleaned_json)
                llm_risk = result.get("risk_level", "low").lower()
            except (json.JSONDecodeError, AttributeError):
                flask_app.logger.warning(f"⚠️ Crisis Watchdog failed to parse JSON from provider: {response_text[:100]}")
                return
                
            # 3. Only escalate if the LLM thinks it's high/crisis and sync check missed it
            risk_hierarchy = {"low": 0, "medium": 1, "high": 2, "crisis": 3}
            if risk_hierarchy.get(llm_risk, 0) > risk_hierarchy.get(sync_risk, 0):
                new_event = CrisisEvent(
                    session_id=session_id,
                    message=message,
                    risk_level=llm_risk,
                    risk_score=1.0 if llm_risk == "crisis" else 0.5,
                    keywords="LLM_WATCHDOG_DETECTION",
                    intervention_taken="Escalated to CAPS Dashboard",
                    escalated=True
                )
                db.session.add(new_event)
                db.session.commit()
                flask_app.logger.info(f"🛡️ Crisis Watchdog escalated risk: {sync_risk} -> {llm_risk} for session {session_id}")
        except Exception as e:
            flask_app.logger.error(f"❌ Crisis Watchdog error: {e}")


def _process_chat_message(message: str, session_id: str, is_first_message: bool = False) -> Tuple[str, str, List[Dict]]:
    """Process chat message with AI provider and crisis detection.

    When using Gemini, this enables function calling for wellness tools.

    Returns:
        Tuple of (ai_response, risk_level, tool_calls)
    """
    try:
        from flask import current_app # Force local scope to fix UnboundLocalError
        # Detect crisis level FIRST
        risk_level = detect_crisis_level(message)
        
        # Guardrail Layer 1: Immediate Crisis Blocking
        if risk_level == "crisis":
             # Use the function defined in this file (available at runtime)
             crisis_data = get_crisis_response_and_resources(risk_level)
             crisis_msg = crisis_data.get("crisis_msg", "Please seek help immediately.")
             
             _log_conversation(session_id, message, f"BLOCKED_CRISIS: {crisis_msg}", risk_level)
             # Return early with crisis message and no tool calls
             return crisis_msg, risk_level, []

        # Check if we should use function calling (Gemini only, non-crisis)
        ai_provider = os.environ.get("AI_PROVIDER", "gemini").lower()
        use_function_calling = (
            ai_provider == "gemini"
            and risk_level != "crisis"
            and os.environ.get("ENABLE_FUNCTION_CALLING", "true").lower() == "true"
        )



        tool_calls = []

        if use_function_calling:
            # Use function calling enabled response
            from providers.gemini import get_gemini_response_with_tools

            ai_response, tool_calls = get_gemini_response_with_tools(
                message, session_id, risk_level, is_first_message=is_first_message,
            )

            # Guardrail Layer 2: Output Safety Verification (async — don't block response)
            # Crisis is already caught by Layer 1 above. Layer 2 runs in background
            # and logs unsafe outputs for review without adding ~15s LLM latency.
            if ai_response:
                def _async_safety_check(app_ctx, sess_id, u_msg, a_resp, r_level):
                    try:
                        with app_ctx.app_context():
                            from providers.safety import check_safety_llm
                            is_safe, safety_msg = check_safety_llm(u_msg, a_resp)
                            if not is_safe:
                                app_ctx.logger.warning(f"Guardrail Layer 2 Block (async): {safety_msg}")
                                _log_conversation(sess_id, u_msg, f"BLOCKED_UNSAFE: {safety_msg} (Sent: {a_resp[:50]}...)", r_level)
                    except Exception:
                        pass  # Safety check is non-critical for response latency

                threading.Thread(
                    target=_async_safety_check,
                    args=(current_app._get_current_object(), session_id, message, ai_response, risk_level)
                ).start()



            
            # KEYWORD FALLBACK: If Gemini didn't call function but should have
            # This ensures wellness interventions ALWAYS trigger when needed
            if not tool_calls:
                msg_lower = message.lower()
                
                # Detect wellness issues
                issue = None
                intensity = "moderate"  # Default
                
                # Check for severity indicators
                if any(word in msg_lower for word in ["very", "really", "so", "extremely", "severe"]):
                    intensity = "severe"
                elif any(word in msg_lower for word in ["little", "bit", "slightly", "mild"]):
                    intensity = "mild"
                
                # Detect issue type
                if any(word in msg_lower for word in ["anxious", "anxiety", "nervous", "worried", "panic"]):
                    issue = "anxiety"
                elif any(word in msg_lower for word in ["stressed", "stress", "overwhelmed", "pressure"]):
                    issue = "stress"  
                elif any(word in msg_lower for word in ["sad", "depressed", "down", "lonely", "hopeless"]):
                    issue = "sadness"
                elif any(word in msg_lower for word in ["tired", "exhausted", "sleep", "insomnia", "can't sleep"]):
                    issue = "sleep"
                
                # If we detected an issue, manually inject the tool call
                if issue:
                    from providers.agent_tools import execute_tool
                    # Removed shadowing import

                    result = execute_tool(
                        "get_wellness_intervention",
                        {"issue": issue, "intensity": intensity},
                        session_id
                    )
                    tool_calls = [{
                        "name": "get_wellness_intervention",
                        "args": {"issue": issue, "intensity": intensity},
                        "result": result,
                        "source": "keyword_fallback"  # Track that this was fallback, not Gemini
                    }]
                    current_app.logger.info(f"💡 Keyword fallback triggered: {issue}/{intensity}")
        else:
            # Regular response with failover
            ai_response, _used_provider = _get_ai_response_with_failover(
                message, session_id, risk_level
            )

        # Log conversation
        _log_conversation(session_id, message, ai_response, risk_level)

        # Log tool calls for audit (if any)
        if tool_calls:
            _log_tool_calls(session_id, tool_calls)

        # Store memory for long-term context (non-blocking)
        try:
            from providers.memory import (
                summarize_interaction_llm,
                MEMORY_ENABLED,
            )

            if MEMORY_ENABLED:
                # Run memory extraction in background thread with app context
                def _async_mem_worker(app_ctx, sess_id, u_msg, a_resp):
                    with app_ctx.app_context():
                        summarize_interaction_llm(sess_id, u_msg, a_resp)

                threading.Thread(
                    target=_async_mem_worker,
                    args=(current_app._get_current_object(), session_id, message, ai_response)
                ).start()
        except Exception:
            pass  # Non-critical, continue if memory fails

        return ai_response, risk_level, tool_calls

    except Exception as e:
        # Use current_app for logging in request context
        from flask import current_app

        current_app.logger.error(f"Message processing error: {e}")
        return (
            "I'm having trouble processing your message right now. Please try again.",
            "low",
            [],
        )


def _log_tool_calls(session_id: str, tool_calls: List[Dict]) -> None:
    """Log tool calls for audit purposes."""
    try:
        from flask import current_app

        for tc in tool_calls:
            current_app.logger.info(
                f"tool_call session={session_id} name={tc.get('name')} "
                f"success={tc.get('result', {}).get('success', False)}"
            )
    except Exception as exc:
        logging.warning(f"Tool call logging failed: {exc}")


def _log_conversation(
    session_id: str, user_message: str, ai_response: str, risk_level: str
) -> None:
    """Log conversation to database using Message table"""
    try:
        from flask import current_app

        # 1. Save User Message
        user_msg_entry = Message(
            session_id=session_id,
            content=user_message,
            is_user=True,
            risk_level=risk_level, # Log risk with user message too? Or just generic.
            timestamp=datetime.utcnow()
        )
        db.session.add(user_msg_entry)

        # 2. Save AI Response
        ai_msg_entry = Message(
            session_id=session_id,
            content=ai_response,
            is_user=False,
            risk_level=risk_level,
            timestamp=datetime.utcnow()
        )
        db.session.add(ai_msg_entry)
        
        db.session.commit()

        # Trigger Counselor Alert for High/Crisis risks
        # AlertManager handles deduplication
        if risk_level in ["high", "crisis"]:
             AlertManager.create_alert(
                session_id=session_id,
                trigger_message=user_message,
                risk_level=risk_level,
                risk_score=1.0 if risk_level == "crisis" else 0.8,
                keywords=["chat_risk_detected"]
            )

    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Failed to log conversation: {e}")


def _convert_risk_level_to_score(risk_level: str) -> float:
    """Convert risk level string to numeric score"""
    risk_mapping = {"low": 0.0, "medium": 0.5, "high": 0.8, "crisis": 1.0}
    return risk_mapping.get(risk_level.lower(), 0.0)


def _check_database_health() -> str:
    """Check database connection health"""
    try:
        engine = db.session.bind
        dialect = engine.dialect.name if engine else None
        if dialect == "postgresql":
            # Run within a short transaction with a statement timeout
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(sql_text("SET LOCAL statement_timeout = 2000"))
                    conn.execute(sql_text("SELECT 1"))
        else:
            db.session.execute(sql_text("SELECT 1"))
        return "healthy"
    except Exception as e:
        try:
            from flask import current_app

            current_app.logger.error(f"Database health check failed: {e}")
        except Exception:
            pass
        return "unhealthy"


def _check_redis_health() -> str:
    """Check Redis connection health"""
    try:
        from flask import current_app

        if current_app.config.get("SESSION_TYPE") == "redis":
            redis_client = current_app.config.get("SESSION_REDIS")
            if redis_client:
                # ping uses the socket timeouts configured in _setup_session
                redis_client.ping()
                return "healthy"
            else:
                return "not configured"
        else:
            return "using filesystem"
    except Exception as e:
        try:
            from flask import current_app
            current_app.logger.error(f"Redis health check failed: {e}")
        except Exception:
            pass
        return "unhealthy"


def _check_ollama_health() -> dict:
    """Check Ollama reachability and whether the third-brother model is loaded."""
    base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    result = {"status": "unknown", "model_loaded": False}
    try:
        resp = requests.get(f"{base}/api/tags", timeout=2)
        resp.raise_for_status()
        models = [m.get("name", "") for m in resp.json().get("models", [])]
        result["status"] = "healthy"
        result["models"] = models
        # Check if any third-brother variant is loaded
        result["model_loaded"] = any("third-brother" in m for m in models)
    except requests.ConnectionError:
        result["status"] = "unreachable"
    except requests.Timeout:
        result["status"] = "timeout"
    except Exception as e:
        result["status"] = f"unhealthy: {str(e)}"
    return result


def _detect_platform() -> str:
    """Detect deployment platform for single codebase usage"""
    if os.environ.get("RENDER"):
        return "render"
    elif os.environ.get("DOCKER_ENV") or os.environ.get("DOCKER"):
        return "docker"
    else:
        return "local"


def _get_fallback_html(app: Flask) -> str:
    """Generate fallback HTML page with environment info"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>GentleQuest – AI Mental Health Assistant</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .api-link {{ display: block; margin: 10px 0; padding: 10px; background: #f0f0f0; text-decoration: none; color: #333; }}
            .api-link:hover {{ background: #e0e0e0; }}
            .env-info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>AI Mental Health Assistant</h1>
            <div class="env-info">
                <h3>Environment Information</h3>
                <p><strong>Environment:</strong> {app.config.get('ENVIRONMENT')}</p>
                <p><strong>Platform:</strong> {_detect_platform()}</p>
                <p><strong>Port:</strong> {app.config.get('PORT')}</p>
                <p><strong>Static Folder:</strong> {app.static_folder}</p>
                <p><strong>Static Folder Exists:</strong> {os.path.exists(app.static_folder)}</p>
                <p><strong>Index.html Exists:</strong> {os.path.exists(os.path.join(app.static_folder, 'index.html'))}</p>
            </div>
            <p>The Flutter web app is not available. Here are the API endpoints:</p>
            <a href="/api/health" class="api-link">Health Check</a>
            <a href="/api/deploy-test" class="api-link">Deploy Test</a>
            <a href="/api/metrics" class="api-link">Metrics</a>
        </div>
    </body>
    </html>
    """


def _is_failure_response(text: str) -> bool:
    """Heuristic to detect unusable provider responses."""
    if not text:
        return True
    t = str(text).strip().lower()
    if not t:
        return True
    markers = (
        "configuration error:",
        "error generating response:",
        "i'm having trouble connecting to my ai services",
    )
    return any(m in t for m in markers)


def _is_quota_or_rate_limit_error(text: str) -> bool:
    """Detect when a provider error clearly indicates quota / rate limits.

    This inspects the final error text from a provider chain, so it matches both
    raw provider messages and wrapped forms like "Error generating response: ...".
    """
    if not text:
        return False
    t = str(text).strip().lower()
    if not t:
        return False
    tokens = (
        "quota exceeded",
        "quota",
        "rate limit",
        "ratelimit",
        "resource_exhausted",
        "resource exhausted",
        "429",
        "limit: 0",
    )
    return any(tok in t for tok in tokens)


def _parse_csv_env(val: str) -> List[str]:
    try:
        return [p.strip() for p in (val or "").split(",") if p.strip()]
    except Exception:
        return []


def _provider_keys_available() -> Dict[str, bool]:
    """Infer provider availability from environment variables."""
    import os as _os

    gem_keys = _parse_csv_env(_os.getenv("GEMINI_API_KEY") or "") + _parse_csv_env(
        _os.getenv("GEMINI_API_KEYS") or ""
    )
    has_gemini = len(gem_keys) > 0
    has_openai = bool((_os.getenv("OPENAI_API_KEY") or "").strip())
    has_pplx = bool(
        ((_os.getenv("PERPLEXITY_API_KEY") or _os.getenv("PPLX_API_KEY") or "").strip())
    )
    return {"gemini": has_gemini, "openai": has_openai, "perplexity": has_pplx}


def _build_failover_chain() -> List[str]:
    """Prefer configured provider if available, then gemini -> openai -> perplexity."""
    from flask import current_app

    available = _provider_keys_available()
    configured = str(current_app.config.get("AI_PROVIDER", "gemini")).lower()
    default_order = ["gemini", "openai", "perplexity"]
    chain: List[str] = []
    if available.get(configured):
        chain.append(configured)
    for p in default_order:
        if available.get(p) and p not in chain:
            chain.append(p)
    return chain or ["gemini"]


def _call_provider(
    provider: str, message: str, session_id: str, risk_level: str
) -> str:
    """Call providers with correct signatures and minimal side effects."""
    from providers.gemini import get_gemini_response
    from providers.openai import get_openai_response
    from providers.perplexity import get_perplexity_response
    import os as _os

    if provider == "gemini":
        return get_gemini_response(
            message, session_id=session_id, risk_level=risk_level
        )
    elif provider == "openai":
        return get_openai_response(message)
    elif provider == "perplexity":
        # Support alias if only PPLX_API_KEY is present at runtime
        if not (_os.getenv("PERPLEXITY_API_KEY") or "").strip():
            alt = (_os.getenv("PPLX_API_KEY") or "").strip()
            if alt:
                _os.environ["PERPLEXITY_API_KEY"] = alt
        return get_perplexity_response(message)
    else:
        return get_gemini_response(
            message, session_id=session_id, risk_level=risk_level
        )


def _get_ai_response_with_failover(
    message: str, session_id: str, risk_level: str
) -> Tuple[str, str]:
    """Try providers in order until a viable response is obtained. Returns (text, used_provider)."""
    chain = _build_failover_chain()
    last_err_text = None
    for prov in chain:
        try:
            resp = _call_provider(prov, message, session_id, risk_level)
            if not _is_failure_response(resp):
                return resp, prov
            last_err_text = resp
        except Exception as _e:
            last_err_text = f"Error generating response: {_e}"
            continue

    # All providers failed. If the last error clearly looks like a quota or
    # rate-limit issue (for example Gemini free-tier 429s), surface a
    # user-friendly "daily limit" style message instead of a vague failure.
    fallback = last_err_text
    if _is_quota_or_rate_limit_error(last_err_text or ""):
        fallback = "Today's AI chat limit has been reached. Please try again tomorrow."
    return (
        fallback
        or "I'm having trouble connecting to my AI services. Please try again in a moment."
    ), (chain[-1] if chain else "unknown")


def _enhanced_crisis_detection(message: str) -> Tuple[str, float, List[str]]:
    """Enhanced crisis detection with keyword analysis"""
    message_lower = message.lower()

    # Crisis keywords with weights
    crisis_keywords = {
        "suicide": 1.0,
        "kill myself": 1.0,
        "want to die": 1.0,
        "end it all": 1.0,
        "take me from this earth": 1.0,
        "take me from earth": 1.0,
        "remove me from earth": 1.0,
        "self harm": 0.9,
        "cut myself": 0.9,
        "hurt myself": 0.9,
        "hopeless": 0.8,
        "no hope": 0.8,
        "worthless": 0.8,
        "useless": 0.8,
        "depressed": 0.7,
        "depression": 0.7,
        "anxiety": 0.6,
        "panic": 0.6,
        "lonely": 0.5,
        "alone": 0.5,
        "isolated": 0.5,
        "stress": 0.4,
        "overwhelmed": 0.4,
        "can't cope": 0.4,
    }

    found_keywords = []
    total_score = 0.0

    for keyword, weight in crisis_keywords.items():
        if keyword in message_lower:
            found_keywords.append(keyword)
            total_score += weight

    # Normalize score
    max_possible_score = sum(crisis_keywords.values())
    normalized_score = total_score / max_possible_score if max_possible_score > 0 else 0

    # Determine risk level
    if normalized_score >= 0.8:
        risk_level = "crisis"
    elif normalized_score >= 0.6:
        risk_level = "high"
    elif normalized_score >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    return risk_level, normalized_score, found_keywords


def get_crisis_response_and_resources(
    risk_level: str, country: str = "generic"
) -> Dict[str, Any]:
    """Get geography-specific crisis response and resources"""
    if risk_level == "crisis":
        # Get country-specific crisis resources
        country_resources = CRISIS_RESOURCES_BY_COUNTRY.get(
            country, CRISIS_RESOURCES_BY_COUNTRY["generic"]
        )
        return {
            "crisis_msg": country_resources["crisis_msg"],
            "crisis_numbers": country_resources["crisis_numbers"],
            "risk_level": risk_level,
        }
    else:
        # For non-crisis levels, return standard responses
        responses = {
            "high": "I'm worried about what you're experiencing. These feelings are serious and you deserve support. Please consider reaching out to a mental health professional or calling your local crisis helpline. You don't have to face this alone.",
            "medium": "I can see you're going through a difficult time. It's important to take these feelings seriously. Consider talking to someone you trust or reaching out to a mental health professional. You're showing strength by sharing this.",
            "low": "Thank you for sharing how you're feeling. It's normal to have difficult moments, and it's okay to not be okay. Consider reaching out to friends, family, or a mental health professional for support.",
        }
        return {
            "crisis_msg": responses.get(risk_level, responses["low"]),
            "crisis_numbers": [],
            "risk_level": risk_level,
        }


def _get_crisis_response(risk_level: str, risk_score: float) -> str:
    """Get appropriate crisis response based on risk level (legacy function)"""
    if risk_level == "crisis":
        return CRISIS_RESOURCES_BY_COUNTRY["generic"]["crisis_msg"]
    else:
        responses = {
            "high": "I'm worried about what you're experiencing. These feelings are serious and you deserve support. Please consider reaching out to a mental health professional or calling your local crisis helpline. You don't have to face this alone.",
            "medium": "I can see you're going through a difficult time. It's important to take these feelings seriously. Consider talking to someone you trust or reaching out to a mental health professional. You're showing strength by sharing this.",
            "low": "Thank you for sharing how you're feeling. It's normal to have difficult moments, and it's okay to not be okay. Consider reaching out to friends, family, or a mental health professional for support.",
        }
        return responses.get(risk_level, responses["low"])


def _get_crisis_resources(risk_level: str) -> Dict[str, Any]:
    """Get crisis resources based on risk level"""
    resources = {
        "crisis": {
            "immediate": [
                {
                    "name": "National Suicide Prevention Lifeline",
                    "number": "988",
                    "available": "24/7",
                },
                {
                    "name": "Crisis Text Line",
                    "text": "HOME to 741741",
                    "available": "24/7",
                },
                {"name": "Emergency Services", "number": "911", "available": "24/7"},
            ],
            "online": [
                {"name": "Crisis Chat", "url": "https://www.crisischat.org/"},
                {"name": "IMAlive", "url": "https://www.imalive.org/"},
            ],
        },
        "high": {
            "immediate": [
                {
                    "name": "National Suicide Prevention Lifeline",
                    "number": "988",
                    "available": "24/7",
                },
                {
                    "name": "Crisis Text Line",
                    "text": "HOME to 741741",
                    "available": "24/7",
                },
            ],
            "online": [
                {
                    "name": "Find a Therapist",
                    "url": "https://www.psychologytoday.com/us/therapists",
                },
                {"name": "Mental Health Resources", "url": "https://www.nami.org/help"},
            ],
        },
        "medium": {
            "immediate": [
                {
                    "name": "Crisis Text Line",
                    "text": "HOME to 741741",
                    "available": "24/7",
                }
            ],
            "online": [
                {
                    "name": "Find a Therapist",
                    "url": "https://www.psychologytoday.com/us/therapists",
                },
                {"name": "Mental Health Resources", "url": "https://www.nami.org/help"},
            ],
        },
        "low": {
            "immediate": [],
            "online": [
                {"name": "Mental Health Resources", "url": "https://www.nami.org/help"},
                {
                    "name": "Self-Care Tips",
                    "url": "https://www.mind.org.uk/information-support/tips-for-everyday-living/",
                },
            ],
        },
    }
    return resources.get(risk_level, resources["low"])


def _get_personalized_recommendations(
    avg_mood: float, recent_entries: List
) -> List[Dict[str, Any]]:
    """Get personalized wellness recommendations based on mood"""
    recommendations = []

    if avg_mood <= 2.0:
        # Low mood recommendations
        recommendations.extend(
            [
                {
                    "type": "immediate",
                    "title": "Reach Out for Support",
                    "description": "Consider talking to a trusted friend, family member, or mental health professional.",
                    "action": "Call a friend or family member",
                },
                {
                    "type": "activity",
                    "title": "Gentle Physical Activity",
                    "description": "Even a short walk can help improve your mood and energy levels.",
                    "action": "Take a 10-minute walk outside",
                },
                {
                    "type": "self_care",
                    "title": "Practice Self-Compassion",
                    "description": "Be kind to yourself. It's okay to not be okay.",
                    "action": "Write down 3 things you're grateful for",
                },
            ]
        )
    elif avg_mood <= 3.5:
        # Moderate mood recommendations
        recommendations.extend(
            [
                {
                    "type": "activity",
                    "title": "Engage in Enjoyable Activities",
                    "description": "Do something you normally enjoy, even if you don't feel like it initially.",
                    "action": "Listen to your favorite music or watch a movie",
                },
                {
                    "type": "social",
                    "title": "Social Connection",
                    "description": "Connect with others, even if it's just a brief conversation.",
                    "action": "Send a message to a friend",
                },
                {
                    "type": "routine",
                    "title": "Maintain Daily Routine",
                    "description": "Stick to your regular schedule to provide structure and stability.",
                    "action": "Follow your usual daily routine",
                },
            ]
        )
    else:
        # Good mood recommendations
        recommendations.extend(
            [
                {
                    "type": "maintenance",
                    "title": "Maintain Positive Habits",
                    "description": "Keep up with activities that contribute to your well-being.",
                    "action": "Continue your current positive routines",
                },
                {
                    "type": "growth",
                    "title": "Personal Development",
                    "description": "Use your positive energy to work on personal goals.",
                    "action": "Set a small goal for the week",
                },
                {
                    "type": "gratitude",
                    "title": "Practice Gratitude",
                    "description": "Reflect on what's going well in your life.",
                    "action": "Write down 5 things you appreciate today",
                },
            ]
        )

    return recommendations


def _get_default_recommendations() -> List[Dict[str, Any]]:
    """Get default wellness recommendations"""
    return [
        {
            "type": "general",
            "title": "Start with Small Steps",
            "description": "Begin with simple activities that can improve your mood.",
            "action": "Take a few deep breaths and stretch",
        },
        {
            "type": "connection",
            "title": "Reach Out",
            "description": "Connect with someone you trust.",
            "action": "Send a message to a friend or family member",
        },
        {
            "type": "self_care",
            "title": "Practice Self-Care",
            "description": "Do something kind for yourself.",
            "action": "Take a warm shower or bath",
        },
    ]


def _analyze_mood_pattern(entries: List) -> Dict[str, Any]:
    """Analyze mood patterns from recent entries"""
    if not entries:
        return {"pattern": "insufficient_data", "trend": "unknown"}

    mood_levels = [entry.mood_level for entry in entries]

    # Calculate trend
    if len(mood_levels) >= 2:
        recent_avg = sum(mood_levels[:3]) / min(3, len(mood_levels))
        older_avg = sum(mood_levels[3:6]) / min(3, len(mood_levels[3:]))

        if recent_avg > older_avg + 0.5:
            trend = "improving"
        elif recent_avg < older_avg - 0.5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    # Identify patterns
    if len(mood_levels) >= 3:
        if all(level <= 2 for level in mood_levels[:3]):
            pattern = "consistently_low"
        elif all(level >= 4 for level in mood_levels[:3]):
            pattern = "consistently_high"
        elif mood_levels[0] < mood_levels[1] < mood_levels[2]:
            pattern = "improving"
        elif mood_levels[0] > mood_levels[1] > mood_levels[2]:
            pattern = "declining"
        else:
            pattern = "fluctuating"
    else:
        pattern = "insufficient_data"

    return {
        "pattern": pattern,
        "trend": trend,
        "recent_moods": mood_levels[:5],
        "average": round(sum(mood_levels) / len(mood_levels), 2),
    }


def _log_crisis_detection(
    session_id: str,
    message: str,
    risk_level: str,
    risk_score: float,
    keywords: List[str],
) -> None:
    """Log crisis detection for monitoring"""
    try:
        event = CrisisEvent(
            session_id=session_id,
            message=message,
            risk_level=risk_level,
            risk_score=risk_score,
            keywords=",".join(keywords),
            timestamp=datetime.utcnow()
        )
        db.session.add(event)
        db.session.commit()
        
        # Trigger Counselor Alert
        # AlertManager handles severity determination and rate limiting
        alert_id = AlertManager.create_alert(
            session_id=session_id,
            trigger_message=message,
            risk_level=risk_level,
            risk_score=risk_score,
            keywords=keywords
        )
        if alert_id:
            current_app.logger.info(f"Counselor Alert created: ID {alert_id}")
    except Exception as e:
        # Use current_app for logging in request context
        from flask import current_app

        current_app.logger.error(f"Failed to log crisis detection: {e}")
        db.session.rollback()


def _purge_old_data_inner():
    """Inner function to purge old data based on retention settings"""
    counts = {}

    # Purge old messages
    message_days = app.config.get("MESSAGE_RETENTION_DAYS", 30)
    if message_days > 0:
        cutoff = datetime.utcnow() - timedelta(days=message_days)
        result = Message.query.filter(Message.timestamp < cutoff).delete()
        counts["messages"] = result

    # Purge old sessions
    session_days = app.config.get("SESSION_RETENTION_DAYS", 90)
    if session_days > 0:
        cutoff = datetime.utcnow() - timedelta(days=session_days)
        result = UserSession.query.filter(UserSession.created_at < cutoff).delete()
        counts["sessions"] = result

    # Purge expired memories (pgvector)
    try:
        from providers.memory import cleanup_expired_memories, MEMORY_ENABLED
        if MEMORY_ENABLED:
            expired = cleanup_expired_memories()
            counts["expired_memories"] = expired
    except Exception:
        pass

    return counts


def _register_additional_routes(app: Flask) -> None:
    """Register additional API routes"""

    @app.route("/api/clear_memory", methods=["POST"])
    @app.limiter.limit("5 per hour")
    def clear_memory():
        """Clear all stored memories for the current user session."""
        try:
            session_id = request.headers.get("X-Session-ID")
            if not session_id:
                return jsonify({"error": "Session ID required"}), 400

            from providers.memory import clear_user_memory, MEMORY_ENABLED

            if not MEMORY_ENABLED:
                return jsonify({"message": "Memory system not enabled"}), 200

            success = clear_user_memory(session_id)

            if success:
                return (
                    jsonify(
                        {
                            "message": "Your memory has been cleared",
                            "session_id": session_id,
                        }
                    ),
                    200,
                )
            else:
                return jsonify({"error": "Failed to clear memory"}), 500

        except Exception as e:
            app.logger.error(f"Clear memory error: {e}")
            return jsonify({"error": "Failed to clear memory"}), 500

    @app.route("/api/memory_status", methods=["GET"])
    def memory_status():
        """Check if memory system is enabled and healthy."""
        try:
            from providers.memory import MEMORY_ENABLED, PGVECTOR_ENABLED

            return (
                jsonify(
                    {
                        "memory_enabled": MEMORY_ENABLED,
                        "pgvector_enabled": PGVECTOR_ENABLED,
                    }
                ),
                200,
            )
        except Exception:
            return (
                jsonify(
                    {
                        "memory_enabled": False,
                        "pgvector_enabled": False,
                    }
                ),
                200,
            )

    @app.route("/api/intervention/outcome", methods=["POST"])
    @app.limiter.limit("30 per minute")
    def log_intervention_outcome():
        """
        Log intervention start/complete/skip for learning and analytics.
        
        Request body:
        {
            "session_id": "...",
            "intervention_id": "calm_478",
            "exercise_type": "breathing",  // breathing, grounding, journaling
            "outcome": "started" | "completed" | "skipped",
            "time_spent_seconds": 180,     // How long user spent on exercise
            "mood_before": 3,              // 1-10 scale before exercise
            "mood_after": 7,               // 1-10 scale after exercise
            "effectiveness": 0.8,          // 0-1 scale
            "feedback": "It helped"        // Optional text feedback
        }
        """
        try:
            session_id = request.headers.get("X-Session-ID") or request.json.get("session_id")
            if not session_id:
                return jsonify({"error": "Session ID required"}), 400
            
            data = request.get_json() or {}
            intervention_id = data.get("intervention_id")
            exercise_type = data.get("exercise_type")
            outcome = data.get("outcome", "started")
            time_spent = data.get("time_spent_seconds")
            mood_before = data.get("mood_before")
            mood_after = data.get("mood_after")
            effectiveness = data.get("effectiveness")
            feedback = data.get("feedback")
            
            if not intervention_id:
                return jsonify({"error": "intervention_id required"}), 400
            
            if outcome not in ["started", "completed", "skipped"]:
                return jsonify({"error": "outcome must be 'started', 'completed', or 'skipped'"}), 400
            
            # Validate mood ratings if provided
            if mood_before is not None and not (1 <= mood_before <= 10):
                return jsonify({"error": "mood_before must be between 1 and 10"}), 400
            if mood_after is not None and not (1 <= mood_after <= 10):
                return jsonify({"error": "mood_after must be between 1 and 10"}), 400
            
            from providers.session_memory import update_intervention_outcome
            
            success = update_intervention_outcome(
                session_id=session_id,
                intervention_id=intervention_id,
                outcome=outcome,
                exercise_type=exercise_type,
                time_spent_seconds=time_spent,
                mood_before=mood_before,
                mood_after=mood_after,
                effectiveness_rating=effectiveness,
                feedback=feedback,
            )
            
            if success:
                app.logger.info(f"Intervention outcome: {intervention_id} → {outcome}")
                return jsonify({
                    "success": True,
                    "message": f"Outcome '{outcome}' recorded",
                    "intervention_id": intervention_id,
                }), 200
            else:
                return jsonify({"error": "Failed to record outcome"}), 500
                
        except Exception as e:
            app.logger.error(f"Intervention outcome error: {e}")
            return jsonify({"error": "Failed to record outcome"}), 500

    # ========================================================================
    # ANALYTICS ENDPOINTS
    # ========================================================================

    @app.route("/api/analytics/overview", methods=["GET"])
    def analytics_overview():
        """
        Get high-level analytics overview.
        Query params: days (default: 30)
        """
        try:
            from providers.analytics import get_intervention_stats, get_completion_rates_by_type
            
            days = int(request.args.get('days', 30))
            
            overall_stats = get_intervention_stats(days)
            by_type = get_completion_rates_by_type(days)
            
            return jsonify({
                "period_days": days,
                "overall": overall_stats,
                "by_type": by_type,
                "timestamp": datetime.utcnow().isoformat()
            }), 200
            
        except Exception as e:
            app.logger.error(f"Analytics overview error: {e}")
            return jsonify({"error": "Failed to fetch analytics"}), 500

    @app.route("/api/analytics/interventions", methods=["GET"])
    def intervention_analytics():
        """
        Get detailed intervention effectiveness breakdown.
        Query params: days (default: 30)
        """
        try:
            from providers.analytics import (
                get_completion_rates_by_type,
                get_mood_improvement_by_type,
                get_intervention_recommendations
            )
            
            days = int(request.args.get('days', 30))
            
            completion_rates = get_completion_rates_by_type(days)
            mood_improvements = get_mood_improvement_by_type(days)
            recommendations = get_intervention_recommendations(days)
            
            return jsonify({
                "period_days": days,
                "completion_rates": completion_rates,
                "mood_improvements": mood_improvements,
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }), 200
            
        except Exception as e:
            app.logger.error(f"Intervention analytics error: {e}")
            return jsonify({"error": "Failed to fetch intervention analytics"}), 500

    @app.route("/api/analytics/user/<session_id>", methods=["GET"])
    def user_analytics(session_id):
        """
        Get analytics for a specific user session.
        Query params: days (default: 30)
        """
        try:
            from providers.analytics import get_user_engagement_metrics, get_best_intervention_for_user
            
            days = int(request.args.get('days', 30))
            
            engagement = get_user_engagement_metrics(session_id, days)
            best_intervention = get_best_intervention_for_user(session_id)
            
            return jsonify({
                "session_id": session_id,
                "period_days": days,
                "engagement": engagement,
                "recommended_intervention": best_intervention,
                "timestamp": datetime.utcnow().isoformat()
            }), 200
            
        except Exception as e:
            app.logger.error(f"User analytics error: {e}")
            return jsonify({"error": "Failed to fetch user analytics"}), 500

    @app.route("/api/analytics/function-calling", methods=["GET"])
    def function_calling_analytics():
        """
        Get function calling statistics (Gemini vs keyword fallback).
        Query params: days (default: 7)
        """
        try:
            from providers.analytics import get_function_calling_stats
            
            days = int(request.args.get('days', 7))
            stats = get_function_calling_stats(days)
            
            return jsonify({
                "period_days": days,
                "stats": stats,
                "timestamp": datetime.utcnow().isoformat()
            }), 200
            
        except Exception as e:
            app.logger.error(f"Function calling analytics error: {e}")
            return jsonify({"error": "Failed to fetch function calling stats"}), 500

    # ========================================================================
    # ADMIN DASHBOARD
    # ========================================================================

    @app.route("/api/admin/analytics")
    def admin_analytics_dashboard():
        """Render the analytics dashboard HTML page."""
        return render_template("admin_dashboard.html")

    # ========================================================================
    # SYSTEM OPS ENDPOINTS
    # ========================================================================

    @app.route("/api/admin/setup_pgvector", methods=["POST"])
    @app.limiter.limit("5 per minute")
    def admin_setup_pgvector():
        """Enable pgvector extension on production database."""
        # Simple security check using existing chat ID as a secret key header
        auth_key = request.headers.get("X-Admin-Key")
        expected_key = os.getenv("TELEGRAM_CHAT_ID")
        
        # Allow if secret matches, or just log warning if open (security tradeoff for immediate fix)
        if not auth_key or (expected_key and auth_key != expected_key):
            app.logger.warning(f"Unauthorized access attempt to setup_pgvector from {request.remote_addr}")
            return jsonify({"error": "Unauthorized"}), 403
            
        try:
            # enable extensions
            db.session.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector"))
            db.session.commit()
            
            # verify
            result = db.session.execute(sql_text("SELECT * FROM pg_extension WHERE extname = 'vector'")).fetchone()
            
            return jsonify({
                "ok": True, 
                "message": "Vector extension check completed",
                "installed": bool(result),
                "details": str(result) if result else "Not found"
            })
        except Exception as e:
            app.logger.error(f"Error enabling pgvector: {e}")
            db.session.rollback()
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/admin/init_brain_tables", methods=["POST"])
    @app.limiter.limit("5 per minute")
    def admin_init_brain_tables():
        """Initialize brain state tables on demand"""
        auth_header = request.headers.get("X-Admin-Key")
        expected_key = os.getenv("TELEGRAM_CHAT_ID", "")
        if not auth_header or auth_header != expected_key:
            return jsonify({"error": "Unauthorized"}), 403

        try:
            from providers.brain_state import init_brain_tables
            result = init_brain_tables()
            return jsonify({
                "ok": True,
                "message": "Brain tables initialized" if result else "Tables already exist or creation skipped",
                "initialized": result
            })
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/admin/init_memory_tables", methods=["POST"])
    @app.limiter.limit("5 per minute")
    def admin_init_memory_tables():
        """Initialize memory system tables on demand with cache invalidation"""
        auth_header = request.headers.get("X-Admin-Key")
        expected_key = os.getenv("TELEGRAM_CHAT_ID", "")
        if not auth_header or auth_header != expected_key:
            return jsonify({"error": "Unauthorized"}), 403

        try:
            from providers import memory
            # Invalidate the cache to force re-check
            memory._memory_tables_ready = None
            
            # Run initialization
            result = memory.init_memory_tables(app)
            
            # Re-check status
            tables_exist = memory._check_memory_tables_exist()
            
            return jsonify({
                "ok": True,
                "message": "Memory tables initialized" if result else "Initialization returned false",
                "initialized": result,
                "tables_exist": tables_exist,
                "pgvector_enabled": memory.PGVECTOR_ENABLED,
                "memory_enabled": memory.MEMORY_ENABLED
            })
        except Exception as e:
            app.logger.error(f"Memory init error: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/admin/debug/db", methods=["GET"])
    @app.limiter.limit("10 per minute")
    def admin_debug_db():
        auth_header = request.headers.get("X-Admin-Key")
        expected_key = os.getenv("TELEGRAM_CHAT_ID", "")
        if not auth_header or auth_header != expected_key:
            return jsonify({"error": "Unauthorized"}), 403

        try:
            # Check extensions
            extensions = db.session.execute(sql_text("SELECT extname FROM pg_extension")).fetchall()
            ext_list = [row[0] for row in extensions]

            # Check memory tables
            tables = db.session.execute(sql_text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            )).fetchall()
            table_list = [row[0] for row in tables]

            # Check brain state (handle table not existing)
            brain_state_rows = 0
            if "brain_state" in table_list:
                try:
                    brain_state_rows = BrainState.query.count()
                except Exception:
                    pass

            return jsonify({
                "ok": True,
                "dialect": db.session.bind.dialect.name if db.session.bind else "unknown",
                "extensions": ext_list,
                "pgvector_installed": "vector" in ext_list,
                "brain_state_rows": brain_state_rows,
                "brain_state_exists": "brain_state" in table_list,
                "tables": table_list
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({"ok": False, "error": str(e)}), 500


    # ========================================================================
    # MEMORY STATUS ENDPOINT
    # ========================================================================

    @app.route("/api/memory/status", methods=["GET"])
    def memory_system_status():
        """Check memory system status for graceful degradation"""
        try:
            from providers.memory import MEMORY_ENABLED, PGVECTOR_ENABLED, _check_memory_tables_exist
            
            tables_exist = _check_memory_tables_exist()
            
            return jsonify({
                "memory_enabled": MEMORY_ENABLED,
                "pgvector_enabled": PGVECTOR_ENABLED,
                "tables_initialized": tables_exist,
                "status": "active" if (MEMORY_ENABLED and PGVECTOR_ENABLED and tables_exist) else "inactive",
                "message": "Memory system operational" if tables_exist else "Memory system disabled or unavailable"
            }), 200
            
        except Exception as e:
            app.logger.error(f"Memory status check error: {e}")
            return jsonify({
                "memory_enabled": False,
                "pgvector_enabled": False,
                "tables_initialized": False,
                "status": "error",
                "message": str(e)
            }), 200  # Return 200 even on error - this is a status check

def run_auto_migrations(app):
    """Automatically add missing columns to existing tables for Agentic Wellness features."""
    migration_statements = [
        "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20) DEFAULT 'none'",
        "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS resources TEXT",
        "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS message_type VARCHAR(50) DEFAULT 'text'",
        "ALTER TABLE quests ADD COLUMN IF NOT EXISTS target INTEGER DEFAULT 1",
        "ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS exercise_type VARCHAR(50)",
        "ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS time_spent_seconds INTEGER",
        "ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS mood_before INTEGER",
        "ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS mood_after INTEGER",
        "ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS offer_stage INTEGER DEFAULT 1",
        "ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS effectiveness_rating FLOAT",
        "ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS feedback TEXT",
        "ALTER TABLE sessions RENAME TO user_sessions"
    ]
    
    try:
        with app.app_context():
            for statement in migration_statements:
                try:
                    db.session.execute(sql_text(statement))
                    db.session.commit()
                    app.logger.info(f"Migration successful: {statement}")
                except Exception as e:
                    db.session.rollback()
                    if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                        app.logger.info(f"Migration column already exists (ignored): {statement}")
                    else:
                        app.logger.warning(f"Migration error for '{statement}': {e}")
    except Exception as e:
        app.logger.error(f"Failed to initialize auto-migrations: {e}")

# Create the application instance
print("DEBUG: calling create_app()")
app = create_app()
print("DEBUG: app instance created successfully")

if __name__ == "__main__":
    # Run auto-migrations first
    run_auto_migrations(app)
    
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Database initialization error: {e}")

    app.run(host="0.0.0.0", port=app.config.get("PORT", 5055), debug=False)
