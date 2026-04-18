"""
Admin, memory, brain, and system ops endpoints.
Extracted from app.py monolith.
"""

import os

from flask import Blueprint, current_app, jsonify, render_template, request
from sqlalchemy import text as sql_text

from extensions import limiter
from models import db

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/api/clear_memory", methods=["POST"])
@limiter.limit("5 per hour")
def clear_memory():
    """Clear all stored memories for the current user session."""
    try:
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            return jsonify({"error": "Session ID required"}), 400

        from providers.memory import MEMORY_ENABLED, clear_user_memory

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
        current_app.logger.error(f"Clear memory error: {e}")
        return jsonify({"error": "Failed to clear memory"}), 500


@admin_bp.route("/api/memory_status", methods=["GET"])
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


@admin_bp.route("/api/admin/analytics")
def admin_analytics_dashboard():
    """Render the analytics dashboard HTML page."""
    return render_template("admin_dashboard.html")


@admin_bp.route("/api/admin/setup_pgvector", methods=["POST"])
@limiter.limit("5 per minute")
def admin_setup_pgvector():
    """Enable pgvector extension on production database."""
    auth_key = request.headers.get("X-Admin-Key")
    expected_key = os.getenv("TELEGRAM_CHAT_ID")

    if not auth_key or (expected_key and auth_key != expected_key):
        current_app.logger.warning(f"Unauthorized access attempt to setup_pgvector from {request.remote_addr}")
        return jsonify({"error": "Unauthorized"}), 403

    try:
        db.session.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector"))
        db.session.commit()

        result = db.session.execute(sql_text("SELECT * FROM pg_extension WHERE extname = 'vector'")).fetchone()

        return jsonify({
            "ok": True,
            "message": "Vector extension check completed",
            "installed": bool(result),
            "details": str(result) if result else "Not found"
        })
    except Exception as e:
        current_app.logger.error(f"Error enabling pgvector: {e}")
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@admin_bp.route("/api/admin/init_brain_tables", methods=["POST"])
@limiter.limit("5 per minute")
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


@admin_bp.route("/api/admin/init_memory_tables", methods=["POST"])
@limiter.limit("5 per minute")
def admin_init_memory_tables():
    """Initialize memory system tables on demand with cache invalidation"""
    auth_header = request.headers.get("X-Admin-Key")
    expected_key = os.getenv("TELEGRAM_CHAT_ID", "")
    if not auth_header or auth_header != expected_key:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        from providers import memory
        memory._memory_tables_ready = None

        result = memory.init_memory_tables(current_app._get_current_object())

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
        current_app.logger.error(f"Memory init error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@admin_bp.route("/api/admin/debug/db", methods=["GET"])
@limiter.limit("10 per minute")
def admin_debug_db():
    auth_header = request.headers.get("X-Admin-Key")
    expected_key = os.getenv("TELEGRAM_CHAT_ID", "")
    if not auth_header or auth_header != expected_key:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        extensions = db.session.execute(sql_text("SELECT extname FROM pg_extension")).fetchall()
        ext_list = [row[0] for row in extensions]

        tables = db.session.execute(sql_text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        )).fetchall()
        table_list = [row[0] for row in tables]

        brain_state_rows = 0
        if "brain_state" in table_list:
            try:
                brain_state_rows = db.session.execute(
                    sql_text("SELECT COUNT(*) FROM brain_state")
                ).scalar() or 0
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


@admin_bp.route("/api/memory/status", methods=["GET"])
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
        current_app.logger.error(f"Memory status check error: {e}")
        return jsonify({
            "memory_enabled": False,
            "pgvector_enabled": False,
            "tables_initialized": False,
            "status": "error",
            "message": str(e)
        }), 200
