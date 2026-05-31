"""
Health, ping, and deploy-test endpoints.
Extracted from app.py monolith.
"""

import os
import time
from datetime import datetime

from flask import Blueprint, current_app, g, jsonify

from extensions import limiter

health_bp = Blueprint("health", __name__)


def _build_health_note(db_down: bool, ai_available: bool):
    """Build health note with DB status and expiry warning."""
    notes = []
    if db_down and ai_available:
        notes.append("Chat works without DB; history/analytics need DB")
    db_expires = os.environ.get("DB_EXPIRES_AT")
    if db_expires:
        try:
            expires_dt = datetime.fromisoformat(db_expires.replace("Z", "+00:00"))
            days_left = (expires_dt - datetime.now(expires_dt.tzinfo)).days
            if days_left <= 7:
                notes.append(f"DB expires in {days_left} days — create new Postgres before {db_expires[:10]}")
            elif days_left <= 14:
                notes.append(f"DB expires in {days_left} days ({db_expires[:10]})")
        except Exception:
            pass
    return "; ".join(notes) if notes else None


@health_bp.route("/api/health", methods=["GET"])
@limiter.exempt
def health():
    """Enhanced health check endpoint with environment info"""
    try:
        from helpers.health_helpers import (
            _check_database_health,
            _check_ollama_health,
            _check_redis_health,
            _detect_platform,
        )

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

        # Core service: AI provider must be available for chat to work
        ai_available = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEYS"))

        # Status logic: core AI chat is what matters most
        # DB/Redis down = degraded (chat still works, persistence doesn't)
        # AI provider missing = unhealthy (app can't serve its purpose)
        db_down = "unhealthy" in db_status.lower()
        redis_down = "unhealthy" in str(redis_status).lower()

        if not ai_available:
            overall = "unhealthy"
        elif db_down or redis_down:
            overall = "degraded"
        else:
            overall = "healthy"

        health_data = {
            "status": overall,
            "ai_chat_available": ai_available,
            "note": _build_health_note(db_down, ai_available),
            "timestamp": datetime.utcnow().isoformat(),
            "environment": current_app.config.get("ENVIRONMENT"),
            "port": current_app.config.get("PORT"),
            "provider": current_app.config.get("AI_PROVIDER"),
            "database": db_status,
            "redis": redis_status,
            "ollama": ollama_status,
            "latency_ms": {
                "db_check": db_ms,
                "redis_check": redis_ms,
                "ollama_check": ollama_ms,
            },
            "cors_enabled": True,
            "cors_origins": current_app.config.get("CORS_ORIGINS", []),
            "deployment": {
                "platform": _detect_platform(),
                "environment": current_app.config.get("ENVIRONMENT"),
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
                "/api/enterprise/metrics",
            ],
        }
        try:
            rid = getattr(g, "request_id", None)
        except Exception:
            rid = None
        current_app.logger.info(
            f"health endpoint status={overall} db={db_status} db_ms={db_ms} redis={redis_status} redis_ms={redis_ms} rid={rid}"
        )

        return jsonify(health_data), 200

    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@health_bp.route("/api/ping", methods=["GET", "HEAD"])
@limiter.exempt
def ping():
    """Ultra-lightweight keep-alive endpoint. Does not touch DB or Redis."""
    try:
        resp = jsonify({"ok": True, "ts": datetime.utcnow().isoformat()})
        resp.headers["Cache-Control"] = "no-store"
        return resp, 200
    except Exception:
        # Always return 200 to avoid failing external pingers
        return jsonify({"ok": False}), 200


@health_bp.route("/api/deploy-test", methods=["GET"])
@limiter.exempt
def deploy_test():
    """Simple deploy verification endpoint"""
    return (
        jsonify(
            {
                "ok": True,
                "version": current_app.config.get("VERSION"),
                "environment": current_app.config.get("ENVIRONMENT"),
            }
        ),
        200,
    )


@health_bp.route("/api/health/deep", methods=["GET"])
@limiter.exempt
def health_deep():
    """Deep health probe for staff debugging (admin-token gated).

    Returns:
        - db_latency_ms: Database round-trip time
        - redis_latency_ms: Redis PING round-trip
        - ollama_reachable: bool
        - disk_free_gb: Available disk on the app volume
        - memory_percent: Process + system memory %
    """
    import secrets

    from flask import request

    # Admin-token gate
    token = request.headers.get("X-Admin-Token") or ""
    expected = current_app.config.get("ADMIN_API_TOKEN") or ""
    if not expected or not secrets.compare_digest(token, expected):
        return jsonify({"error": "Unauthorized"}), 401

    from helpers.health_helpers import (
        _check_database_health,
        _check_ollama_health,
        _check_redis_health,
    )

    # Measure DB latency
    t0 = time.monotonic()
    db_status = _check_database_health()
    db_ms = int((time.monotonic() - t0) * 1000)

    # Measure Redis latency
    t1 = time.monotonic()
    redis_status = _check_redis_health()
    redis_ms = int((time.monotonic() - t1) * 1000)

    # Ollama reachability
    ollama_status = _check_ollama_health()

    # Disk + memory
    disk_free_gb = None
    memory_percent = None
    try:
        import psutil
        disk = psutil.disk_usage("/")
        disk_free_gb = round(disk.free / (1024 ** 3), 2)
        memory_percent = psutil.virtual_memory().percent
    except Exception as e:
        current_app.logger.warning(f"psutil probe failed: {e}")

    return (
        jsonify({
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "db": {
                "status": db_status,
                "latency_ms": db_ms,
            },
            "redis": {
                "status": redis_status,
                "latency_ms": redis_ms,
            },
            "ollama": {
                "status": ollama_status,
            },
            "system": {
                "disk_free_gb": disk_free_gb,
                "memory_percent": memory_percent,
            },
            "environment": current_app.config.get("ENVIRONMENT"),
            "version": current_app.config.get("VERSION"),
        }),
        200,
    )
