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

# Background executor + session/analytics helpers live in helpers.session_helpers
# to break circular 'from app import ...' in route blueprints.
from helpers.session_helpers import (  # noqa: E402
    background_executor,
    _get_or_create_session,
    _update_session_last_active,
    _get_conversation_count,
    _increment_conversation_count,
    _log_analytics_event,
    _log_chat_request,
)
from helpers.health_helpers import (  # noqa: E402
    _check_database_health,
    _check_redis_health,
    _check_ollama_health,
    _detect_platform,
)
from helpers.crisis_helpers import (  # noqa: E402
    CRISIS_RESOURCES_BY_COUNTRY,
    get_country_code_from_ip,
    get_country_from_request,
    _enhanced_crisis_detection,
    get_crisis_response_and_resources,
    _get_crisis_response,
    _get_crisis_resources,
    _log_crisis_detection,
    _run_crisis_watchdog,
)
from helpers.chat_helpers import (  # noqa: E402
    _safety_executor,
    _SAFETY_TIMEOUT_SECONDS,
    _call_llm_json,
    _apply_layer_2_safety,
    _process_chat_message,
    _log_tool_calls,
    _log_conversation,
    _convert_risk_level_to_score,
    _get_fallback_html,
    _is_failure_response,
    _is_quota_or_rate_limit_error,
    _parse_csv_env,
    _provider_keys_available,
    _build_failover_chain,
    _call_provider,
    _get_ai_response_with_failover,
)

import atexit


# _safety_executor, _SAFETY_TIMEOUT_SECONDS -> helpers.chat_helpers


# CRISIS_RESOURCES_BY_COUNTRY, get_country_code_from_ip, get_country_from_request -> helpers.crisis_helpers

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

    # Set SQLAlchemy database URI with explicit psycopg driver and SSL if needed.
    # Skip this block in test mode — the earlier test_mode branch at L450-454
    # already pointed at sqlite:///:memory:. Overwriting it caused 134 CI
    # errors (sqlite3.OperationalError: unable to open database file, because
    # instance/ does not exist in the CI checkout).
    if not app.config.get("TESTING") and Config.DATABASE_URL:
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
    elif not app.config.get("TESTING"):
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

    # Register routes (static pages, compliance, assessments still in _register_routes)
    _register_routes(app)

    # Register extracted route blueprints (health, chat, session, analytics, admin)
    from routes import register_blueprints
    register_blueprints(app)

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


# _CHAT_LOG_PATH, _chat_log_lock, _log_chat_request -> helpers.session_helpers

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


    # All route handlers extracted to routes/ blueprints


# _get_or_create_session .. _log_analytics_event -> helpers.session_helpers


# _call_llm_json .. _get_ai_response_with_failover -> helpers.chat_helpers

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

    # Calculate trend. Requires both a "recent" window and an "older" window to
    # compare; if the older window is empty we can't compute a trend.
    older_slice = mood_levels[3:6]
    if len(mood_levels) >= 2 and older_slice:
        recent_avg = sum(mood_levels[:3]) / min(3, len(mood_levels))
        older_avg = sum(older_slice) / len(older_slice)

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



# _log_crisis_detection -> helpers.crisis_helpers

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



# _register_additional_routes removed — all routes moved to routes/ blueprints

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
