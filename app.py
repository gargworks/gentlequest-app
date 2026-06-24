"""
GentleQuest / AI Mental Health Assistant — Flask application factory.

Slim orchestrator: delegates all wiring to `config/`, `setup/`, `helpers/`, and
`routes/` packages. See `helpers/README.md` for module responsibilities.
"""

import os
import sys

print("DEBUG: app.py start imports")
from dotenv import load_dotenv

# Load .env from the package directory (fix for missing API keys under gunicorn)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# mcp-server-nucleus local imports
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "mcp-server-nucleus", "src"))
)

from flask import Flask  # noqa: E402

from models import db  # noqa: E402, F401

# --- Optional feature integrations -----------------------------------------

try:
    from api_clinical_dashboard import clinical_dashboard  # noqa: F401
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


# --- Configuration + extracted helpers (re-exported for backward compat) ---

from config.settings import (  # noqa: E402, F401
    ENV_CONFIG,
    ENVIRONMENT,
    Config,
    _detect_environment,
    _get_environment_config,
)
from helpers.chat_helpers import (  # noqa: E402, F401
    _SAFETY_TIMEOUT_SECONDS,
    _apply_layer_2_safety,
    _build_failover_chain,
    _call_llm_json,
    _call_provider,
    _convert_risk_level_to_score,
    _get_ai_response_with_failover,
    _get_fallback_html,
    _is_failure_response,
    _is_quota_or_rate_limit_error,
    _log_conversation,
    _log_tool_calls,
    _parse_csv_env,
    _process_chat_message,
    _provider_keys_available,
    _safety_executor,
)
from helpers.crisis_helpers import (  # noqa: E402, F401
    CRISIS_RESOURCES_BY_COUNTRY,
    _enhanced_crisis_detection,
    _get_crisis_resources,
    _get_crisis_response,
    _log_crisis_detection,
    _run_crisis_watchdog,
    get_country_code_from_ip,
    get_country_from_request,
    get_crisis_response_and_resources,
)
from helpers.health_helpers import (  # noqa: E402, F401
    _check_database_health,
    _check_ollama_health,
    _check_redis_health,
    _detect_platform,
)
from helpers.mood_helpers import (  # noqa: E402, F401
    _analyze_mood_pattern,
    _get_default_recommendations,
    _get_personalized_recommendations,
    _purge_old_data_inner,
)
from helpers.session_helpers import (  # noqa: E402, F401
    _get_conversation_count,
    _get_or_create_session,
    _increment_conversation_count,
    _log_analytics_event,
    _log_chat_request,
    _update_session_last_active,
    background_executor,
)
from setup.ai_diagnostics import log_ai_startup_diagnostics  # noqa: E402
from setup.blueprints import register_all_blueprints  # noqa: E402
from setup.db_url import configure_database_url  # noqa: E402
from setup.error_handlers import (  # noqa: E402, F401
    register_error_handlers,
    register_request_id_middleware,
)
from setup.extensions import (  # noqa: E402, F401
    _init_database,
    _init_extensions,
    _rate_limit_enabled,
    _rate_limit_key,
    _setup_cors,
    _setup_rate_limiter,
    _setup_security_headers,
    _setup_session,
    configure_app,
)
from setup.logging import configure_logging, init_sentry  # noqa: E402
from setup.migrations import run_auto_migrations  # noqa: E402, F401
from setup.shutdown import register_graceful_shutdown  # noqa: E402


def create_app() -> Flask:
    """Application factory."""
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="",
        template_folder="templates",
    )
    app.config.from_object(Config)

    # Fail-fast if production uses default SECRET_KEY
    if (
        app.config.get("ENVIRONMENT") == "production"
        and app.config.get("SECRET_KEY") == "dev-secret-key-change-in-production"
    ):
        raise ValueError("SECRET_KEY must be explicitly set in production")

    # Cap request bodies at 5 MB
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    # Test mode: force sqlite + disable rate limits
    test_mode = bool(os.getenv("CI") or os.getenv("PYTEST_CURRENT_TEST"))
    if test_mode:
        app.config["TESTING"] = True
        app.config["RATE_LIMIT_ENABLED"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
            "TEST_DATABASE_URL", "sqlite:///:memory:"
        )

    # Early logging + Sentry
    configure_logging(app)
    init_sentry(app)

    # DB URL normalization + engine options (skip in test mode)
    if not test_mode:
        configure_database_url(app)

    # AI provider startup diagnostics
    log_ai_startup_diagnostics(app)

    # Extensions (DB init, sessions, rate limiter, CORS)
    _init_extensions(app)
    _init_database(app)

    # Memory system (pgvector) — non-fatal
    try:
        from providers.memory import MEMORY_ENABLED, init_memory_tables

        if MEMORY_ENABLED:
            if init_memory_tables(app):
                app.logger.info("Memory system initialized with pgvector")
            else:
                app.logger.info(
                    "Memory system running without pgvector (fallback mode)"
                )
    except Exception as e:
        app.logger.warning(f"Memory system initialization skipped: {e}")

    # Brain state tables (Telegram/Nucleus)
    try:
        with app.app_context():
            from providers.brain_state import init_brain_tables

            if init_brain_tables():
                app.logger.info("Brain state tables initialized")
    except Exception as e:
        app.logger.warning(f"Brain state initialization skipped: {e}")

    # Initialize DB again now that all models are imported
    _init_database(app)

    # Enterprise integrations
    if ENTERPRISE_FEATURES:
        try:
            integrate_with_app(app)
            app.logger.info("✅ Enterprise features integrated successfully")
        except Exception as e:
            app.logger.warning(f"⚠️ Enterprise features integration failed: {e}")
    else:
        app.logger.info("ℹ️ Enterprise features not enabled")

    # All blueprints + legacy routes + brain/enterprise fallback + security headers
    register_all_blueprints(app, DASHBOARD_AVAILABLE)

    # Request-ID middleware + global error handlers
    register_request_id_middleware(app)
    register_error_handlers(app)

    # Graceful shutdown (drains background_executor + closes Redis)
    register_graceful_shutdown(app)

    return app


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

    # Start daily funnel snapshot scheduler (self-snapshotting backend)
    try:
        from scheduler.funnel_scheduler import start_funnel_scheduler
        start_funnel_scheduler(app)
        app.logger.info("Funnel snapshot scheduler started")
    except Exception as e:
        app.logger.warning(f"Funnel scheduler failed to start: {e}")

    app.run(host="0.0.0.0", port=app.config.get("PORT", 5055), debug=False)
