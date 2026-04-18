"""
Blueprint and legacy-module route registration orchestrator.
Extracted from app.py monolith.

`register_all_blueprints(app)` wires up:
- Legacy app-level blueprints (quest, resource, alert, clinical dashboard)
- Extracted `routes/` blueprints (health, chat, session, analytics, admin, static, compliance, assessment)
- Community routes
- Brain/Telegram integration
- Enterprise fallback endpoints
- Security headers
- Session-id coercion before_request hook
"""

from flask import Flask, request

from routes.brain_routes import register_brain_routes
from routes.enterprise_routes import register_enterprise_routes
from setup.extensions import _setup_security_headers


def _register_session_id_middleware(app: Flask) -> None:
    """Ensure session ID is always a string for consistency."""

    @app.before_request
    def ensure_session_id_is_str():
        session_id = request.headers.get("X-Session-ID")
        if session_id and not isinstance(session_id, str):
            request.headers["X-Session-ID"] = str(session_id)


def _register_legacy_blueprints(app: Flask, dashboard_available: bool) -> None:
    """Register legacy per-feature blueprints (quest, resource, alert, clinical)."""
    try:
        from app_quest_routes import quest_bp
        app.register_blueprint(quest_bp)
        app.logger.info("Quest Blueprint registered successfully")
    except Exception as e:
        app.logger.error(f"Failed to register Quest Blueprint: {e}")

    try:
        from app_resource_routes import register_resource_routes
        register_resource_routes(app)
        app.logger.info("Resource Routes registered successfully")
    except Exception as e:
        app.logger.error(f"Failed to register Resource Routes: {e}")

    try:
        from app_alert_routes import register_alert_routes
        register_alert_routes(app)
        app.logger.info("Alert Routes registered successfully")
    except Exception as e:
        app.logger.error(f"Failed to register Alert Routes: {e}")

    if dashboard_available:
        try:
            from api_clinical_dashboard import clinical_dashboard
            app.register_blueprint(clinical_dashboard)
            app.logger.info("Clinical Dashboard Blueprint registered successfully")
        except Exception as e:
            app.logger.error(f"Failed to register Clinical Dashboard Blueprint: {e}")
    else:
        app.logger.info("Clinical Dashboard skipped: DASHBOARD_AVAILABLE is False")


def register_all_blueprints(app: Flask, dashboard_available: bool) -> None:
    """Orchestrate full route registration in the correct order."""
    # Session-id coercion (before_request hook) + security headers
    _register_session_id_middleware(app)
    _setup_security_headers(app)

    # Legacy per-feature blueprints
    _register_legacy_blueprints(app, dashboard_available)

    # Extracted routes/ blueprints (health, chat, session, analytics, admin, ...)
    from routes import register_blueprints
    register_blueprints(app)

    # Community routes
    try:
        from community import register_community_routes
        register_community_routes(app)
        app.logger.info("Community routes registered")
    except Exception as e:
        app.logger.warning(f"Community routes failed to register: {e}")

    # Nuclear Brain / Telegram integration
    register_brain_routes(app)

    # Enterprise fallback endpoints
    register_enterprise_routes(app)
