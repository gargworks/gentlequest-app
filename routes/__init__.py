"""
GentleQuest route blueprints.

Extracted from the monolithic app.py to improve maintainability.
Each module registers a Flask Blueprint with related endpoints.
"""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    """Register all route blueprints with the Flask application."""
    from routes.admin import admin_bp
    from routes.alerts import alerts_bp
    from routes.analytics_routes import analytics_bp
    from routes.assessment import assessment_bp
    from routes.chat import chat_bp
    from routes.compliance import compliance_bp
    from routes.crisis import crisis_bp
    from routes.health import health_bp
    from routes.insights import insights_bp
    from routes.journal import journal_bp
    from routes.push_tokens import push_tokens_bp
    from routes.quests import quests_bp
    from routes.session import session_bp
    from routes.user_resources import user_resources_bp
    from routes.static import static_bp
    from routes.user_settings import user_settings_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(static_bp)
    app.register_blueprint(compliance_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(insights_bp)
    app.register_blueprint(journal_bp)
    app.register_blueprint(user_resources_bp)
    app.register_blueprint(push_tokens_bp)
    app.register_blueprint(quests_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(crisis_bp)
    app.register_blueprint(user_settings_bp)

    app.logger.info(
        "Registered 16 route blueprints: health, chat, session, analytics, "
        "admin, static, compliance, assessment, insights, quests_v2, "
        "journal, user_resources, push_tokens, alerts_v2, crisis_v2, user_settings"
    )
