"""
GentleQuest route blueprints.

Extracted from the monolithic app.py to improve maintainability.
Each module registers a Flask Blueprint with related endpoints.
"""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    """Register all route blueprints with the Flask application."""
    from routes.health import health_bp
    from routes.chat import chat_bp
    from routes.session import session_bp
    from routes.analytics_routes import analytics_bp
    from routes.admin import admin_bp
    from routes.static import static_bp
    from routes.compliance import compliance_bp
    from routes.assessment import assessment_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(static_bp)
    app.register_blueprint(compliance_bp)
    app.register_blueprint(assessment_bp)

    app.logger.info(
        f"Registered {8} route blueprints: health, chat, session, analytics, admin, static, compliance, assessment"
    )
