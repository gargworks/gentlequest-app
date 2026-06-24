"""
Analytics, intervention outcome, admin purge, and retention config endpoints.
Extracted from app.py monolith.
"""

import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict

from flask import Blueprint, current_app, g, jsonify, request

from extensions import limiter
from models import AnalyticsEvent, Message, db

analytics_bp = Blueprint("analytics", __name__)


def _load_blocklist():
    """Load test/internal session IDs to exclude from the true metric."""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "test_session_blocklist.json")
    try:
        with open(path) as f:
            data = json.load(f)
            return set(data.get("blocked_session_ids", []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


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
        from helpers.mood_helpers import _purge_old_data_inner
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
        from providers.analytics import get_completion_rates_by_type, get_intervention_stats

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
            get_intervention_recommendations,
            get_mood_improvement_by_type,
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
        from providers.analytics import get_best_intervention_for_user, get_user_engagement_metrics

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


@analytics_bp.route("/api/metrics/true", methods=["GET"])
def true_metric():
    """The one metric that matters: unique sessions that sent their first chat message.

    Excludes all session IDs in config/test_session_blocklist.json (test/internal noise).
    No auth, no PII — just a count.
    """
    try:
        blocked = _load_blocklist()

        # All-time unique sessions with ≥1 user message, excluding blocklist
        all_sessions = db.session.query(Message.session_id).filter(
            Message.is_user == True
        ).distinct().all()
        all_count = sum(1 for (sid,) in all_sessions if sid not in blocked)

        # Today (UTC midnight boundary)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_sessions = db.session.query(Message.session_id).filter(
            Message.is_user == True,
            Message.timestamp >= today_start
        ).distinct().all()
        today_count = sum(1 for (sid,) in today_sessions if sid not in blocked)

        # Yesterday
        yesterday_start = today_start - timedelta(days=1)
        yesterday_sessions = db.session.query(Message.session_id).filter(
            Message.is_user == True,
            Message.timestamp >= yesterday_start,
            Message.timestamp < today_start
        ).distinct().all()
        yesterday_count = sum(1 for (sid,) in yesterday_sessions if sid not in blocked)

        # Last 7 days trend (unique per day)
        trend = []
        for i in range(6, -1, -1):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            day_sessions = db.session.query(Message.session_id).filter(
                Message.is_user == True,
                Message.timestamp >= day_start,
                Message.timestamp < day_end
            ).distinct().all()
            day_count = sum(1 for (sid,) in day_sessions if sid not in blocked)
            trend.append({"date": day_start.strftime("%Y-%m-%d"), "count": day_count})

        # Blocked count (for transparency)
        blocked_count = sum(1 for (sid,) in all_sessions if sid in blocked)

        return jsonify({
            "metric": "first_chat_sent",
            "description": "Unique sessions that sent their first chat message (test sessions excluded)",
            "all_time": all_count,
            "today": today_count,
            "yesterday": yesterday_count,
            "trend_7d": trend,
            "blocked_sessions": blocked_count,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        current_app.logger.error(f"True metric error: {e}")
        return jsonify({"error": "Failed to compute metric"}), 500


@analytics_bp.route("/api/metrics/funnel", methods=["GET"])
def funnel_metrics():
    """Full acquisition funnel: web visits → installs → app opens → first chat.

    Stage 1: Web visits (GA4 web stream — starts collecting after GA4 tag deployed)
    Stage 2: App installs (GA4 newUsers = first_open, iOS + Android)
    Stage 3: App opens (GA4 app_open events)
    Stage 4: First chat sent (backend DB, test sessions excluded)

    GA4 data is cached for 1 hour to avoid API rate limits.
    """
    import tempfile
    from datetime import timedelta

    try:
        # --- Stage 4: First chat (from DB, always fresh) ---
        blocked = _load_blocklist()
        all_chat_sessions = db.session.query(Message.session_id).filter(
            Message.is_user == True
        ).distinct().all()
        first_chat_count = sum(1 for (sid,) in all_chat_sessions if sid not in blocked)

        # --- Stages 1-3: GA4 data (cached) ---
        cache_path = os.path.join(tempfile.gettempdir(), "gq_funnel_cache.json")
        cache_valid = False
        ga4_data = None

        if os.path.exists(cache_path):
            cache_age = datetime.utcnow().timestamp() - os.path.getmtime(cache_path)
            if cache_age < 3600:  # 1 hour cache
                with open(cache_path) as f:
                    ga4_data = json.load(f)
                cache_valid = True

        if not cache_valid:
            try:
                from google.oauth2 import service_account
                from google.analytics.data_v1beta import BetaAnalyticsDataClient
                from google.analytics.data_v1beta.types import (
                    RunReportRequest, DateRange, Dimension, Metric
                )

                sa_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                       "secret", "gentlequest-prod-sa.json")
                if os.path.exists(sa_path):
                    creds = service_account.Credentials.from_service_account_file(
                        sa_path, scopes=["https://www.googleapis.com/auth/analytics.readonly"]
                    )
                    client = BetaAnalyticsDataClient(credentials=creds)

                    # Installs (newUsers) by platform — last 90 days
                    req = RunReportRequest(
                        property="properties/516568186",
                        date_ranges=[DateRange(start_date="90daysAgo", end_date="today")],
                        dimensions=[Dimension(name="platform")],
                        metrics=[Metric(name="newUsers"), Metric(name="activeUsers")],
                    )
                    resp = client.run_report(request=req)
                    installs_90d = {}
                    active_90d = {}
                    for row in resp.rows:
                        platform = row.dimension_values[0].value
                        installs_90d[platform] = int(row.metric_values[0].value)
                        active_90d[platform] = int(row.metric_values[1].value)

                    # App opens (last 90 days)
                    req2 = RunReportRequest(
                        property="properties/516568186",
                        date_ranges=[DateRange(start_date="90daysAgo", end_date="today")],
                        dimensions=[Dimension(name="eventName")],
                        metrics=[Metric(name="eventCount")],
                    )
                    resp2 = client.run_report(request=req2)
                    app_opens_90d = 0
                    for row in resp2.rows:
                        if row.dimension_values[0].value == "app_open":
                            app_opens_90d = int(row.metric_values[0].value)

                    ga4_data = {
                        "installs_90d": installs_90d,
                        "active_90d": active_90d,
                        "app_opens_90d": app_opens_90d,
                        "web_visits_90d": None,  # Web stream just created, no data yet
                    }
                    with open(cache_path, "w") as f:
                        json.dump(ga4_data, f, indent=2)
            except Exception as ga4_err:
                current_app.logger.warning(f"GA4 fetch failed: {ga4_err}")
                ga4_data = {
                    "installs_90d": {},
                    "active_90d": {},
                    "app_opens_90d": 0,
                    "web_visits_90d": None,
                    "error": str(ga4_err),
                }

        return jsonify({
            "funnel": {
                "stage_1_web_visits": ga4_data.get("web_visits_90d") if ga4_data else None,
                "stage_2_installs": ga4_data.get("installs_90d", {}) if ga4_data else {},
                "stage_3_app_opens": ga4_data.get("app_opens_90d", 0) if ga4_data else 0,
                "stage_4_first_chat": first_chat_count,
            },
            "period": "last_90_days",
            "active_users_90d": ga4_data.get("active_90d", {}) if ga4_data else {},
            "blocked_test_sessions": len(blocked),
            "ga4_property": "516568186",
            "cached": cache_valid,
            "timestamp": datetime.utcnow().isoformat(),
        }), 200

    except Exception as e:
        current_app.logger.error(f"Funnel metrics error: {e}")
        return jsonify({"error": "Failed to fetch funnel metrics"}), 500
