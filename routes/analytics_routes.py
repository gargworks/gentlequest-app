"""
Analytics, intervention outcome, admin purge, and retention config endpoints.
Extracted from app.py monolith.
"""

import secrets
from datetime import datetime
from typing import Dict, Any

from flask import Blueprint, jsonify, request, g, current_app
from extensions import limiter
from models import db, AnalyticsEvent

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/api/analytics/log", methods=["POST"])
@limiter.limit("120 per minute")
def log_analytics_event():
    """Minimal analytics logging endpoint.
    Requirements:
    - No PII is accepted or stored.
    - Requires X-Analytics-Consent: true header; otherwise noop (202).
    - Associates events to a session and request_id for traceability.
    """
    try:
        from helpers.session_helpers import _get_or_create_session

        if request.headers.get("X-Analytics-Consent") != "true":
            return jsonify({"ok": True}), 201

        data = request.get_json(silent=True) or {}
        event_type = (data.get("event_type") or "").strip()
        if not event_type or len(event_type) > 64:
            return jsonify({"error": "Invalid event_type"}), 400

        allowed = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-"
        )
        if any(ch not in allowed for ch in event_type):
            return jsonify({"error": "Invalid event_type"}), 400

        raw_meta = data.get("metadata") or {}
        metadata: Dict[str, Any] = {}
        if isinstance(raw_meta, dict):
            allowed_keys = {
                "action", "label", "screen", "source", "value", "count",
                "duration_ms", "success", "code", "provider",
                "quest_id", "tag", "surface", "variant", "ts", "progress",
                "ui",
            }
            for k, v in raw_meta.items():
                if k in allowed_keys and isinstance(v, (str, int, float, bool)):
                    if isinstance(v, str) and len(v) > 200:
                        v = v[:200]
                    metadata[k] = v

        session_id = _get_or_create_session()
        req_id = getattr(g, "request_id", None)

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
        current_app.logger.error(f"Analytics log error: {e}")
        return jsonify({"error": "Failed to log analytics"}), 500


@analytics_bp.route("/api/analytics/recent", methods=["GET"])
@limiter.limit("60 per minute")
def analytics_recent():
    """Read-only: Fetch recent analytics events for debugging."""
    try:
        prefix = (request.args.get("event_prefix") or "").strip()
        try:
            limit = int(request.args.get("limit", "50"))
        except Exception:
            limit = 50
        limit = max(1, min(limit, 200))

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
        current_app.logger.error(f"Analytics recent error: {e}")
        return jsonify({"error": "Failed to fetch analytics"}), 500


@analytics_bp.route("/api/admin/purge", methods=["POST"])
@limiter.limit("5 per minute")
def admin_purge():
    """Admin-only: Purge old data per retention policy."""
    token = request.headers.get("X-Admin-Token") or ""
    expected = current_app.config.get("ADMIN_API_TOKEN") or ""
    if not expected or not secrets.compare_digest(token, expected):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        from app import _purge_old_data_inner  # stays in app.py (uses app.config)
        counts = _purge_old_data_inner()
        return jsonify({"success": True, "purged": counts}), 200
    except Exception as e:
        return jsonify({"error": "Purge failed", "details": str(e)}), 500


@analytics_bp.route("/api/admin/retention_config", methods=["GET"])
def retention_config():
    """Admin-only: View effective retention configuration."""
    token = request.headers.get("X-Admin-Token") or ""
    expected = current_app.config.get("ADMIN_API_TOKEN") or ""
    if not expected or not secrets.compare_digest(token, expected):
        return jsonify({"error": "Unauthorized"}), 401
    return (
        jsonify(
            {
                "message_retention_days": current_app.config.get("MESSAGE_RETENTION_DAYS"),
                "session_retention_days": current_app.config.get("SESSION_RETENTION_DAYS"),
                "error_log_retention_days": current_app.config.get("ERROR_LOG_RETENTION_DAYS"),
                "analytics_retention_days": current_app.config.get("ANALYTICS_RETENTION_DAYS"),
            }
        ),
        200,
    )


@analytics_bp.route("/api/intervention/outcome", methods=["POST"])
@limiter.limit("30 per minute")
def log_intervention_outcome():
    """Log intervention start/complete/skip for learning and analytics."""
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
            current_app.logger.info(f"Intervention outcome: {intervention_id} → {outcome}")
            return jsonify({
                "success": True,
                "message": f"Outcome '{outcome}' recorded",
                "intervention_id": intervention_id,
            }), 200
        else:
            return jsonify({"error": "Failed to record outcome"}), 500

    except Exception as e:
        current_app.logger.error(f"Intervention outcome error: {e}")
        return jsonify({"error": "Failed to record outcome"}), 500


@analytics_bp.route("/api/analytics/overview", methods=["GET"])
def analytics_overview():
    """Get high-level analytics overview."""
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
        current_app.logger.error(f"Analytics overview error: {e}")
        return jsonify({"error": "Failed to fetch analytics"}), 500


@analytics_bp.route("/api/analytics/interventions", methods=["GET"])
def intervention_analytics():
    """Get detailed intervention effectiveness breakdown."""
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
        current_app.logger.error(f"Intervention analytics error: {e}")
        return jsonify({"error": "Failed to fetch intervention analytics"}), 500


@analytics_bp.route("/api/analytics/user/<session_id>", methods=["GET"])
def user_analytics(session_id):
    """Get analytics for a specific user session."""
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
        current_app.logger.error(f"User analytics error: {e}")
        return jsonify({"error": "Failed to fetch user analytics"}), 500


@analytics_bp.route("/api/analytics/function-calling", methods=["GET"])
def function_calling_analytics():
    """Get function calling statistics (Gemini vs keyword fallback)."""
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
        current_app.logger.error(f"Function calling analytics error: {e}")
        return jsonify({"error": "Failed to fetch function calling stats"}), 500
