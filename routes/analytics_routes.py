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
from models import AnalyticsEvent, FunnelSnapshot, Message, db

# Bot-filter rule set for the qualified-human funnel (Qualified Activation
# Proof, Task 5). Imported here (rather than reimplemented) so the funnel
# endpoint (Task 6) and the dashboard script share a single source of truth.
from scripts.analytics_dashboard import is_qualified_human  # noqa: F401

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


def _classify_user_agent(raw_ua: str) -> str:
    """Classify a User-Agent as "human", "bot", or "unknown".

    Deliberately fails to "bot" rather than "human" on anything suspicious:
    an over-counted funnel is the failure mode this whole change exists to fix.
    "unknown" is reserved for a genuinely absent UA, so a reader can tell
    "we looked and it was not a browser" apart from "we never looked".
    """
    if not raw_ua:
        return "unknown"
    try:
        from scripts.analytics_dashboard import is_qualified_human

        # Duration/pageview rules need session context this endpoint does not
        # have; pass values that exempt those rules so this call decides on the
        # UA alone. The session-shape rules still run later, at read time.
        return "human" if is_qualified_human({}, raw_ua, 60.0, 5) else "bot"
    except Exception:  # pragma: no cover - never break logging over this
        return "unknown"


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
                # Activation proof attribution metadata (Issue B2).
                "action_type", "utm_source", "utm_medium", "utm_campaign",
                "landing_path", "cta_id", "target_url", "referrer",
                "result", "method", "source_cta",
            }
            for k, v in raw_meta.items():
                if k in allowed_keys and isinstance(v, (str, int, float, bool)):
                    if isinstance(v, str) and len(v) > 200:
                        v = v[:200]
                    metadata[k] = v

        # Classify the REAL User-Agent, server-side, at write time.
        #
        # 2026-09-03. The funnel's bot filter was dead by construction. It read
        # the UA from event metadata (analytics_routes.py:443) — but this
        # endpoint's `allowed_keys` above has never included user_agent/ua, so
        # the writer strips exactly the key the reader looks for. The UA was
        # therefore ALWAYS absent, and the reader substituted DEFAULT_UA, a
        # hardcoded desktop-Chrome string. is_qualified_human() rejects a
        # missing UA correctly; it never got the chance, because every session
        # was handed the same synthetic human.
        #
        # We store a CLASSIFICATION, not the UA itself: the raw string is a
        # fingerprinting surface and this endpoint promises to hold no PII. The
        # underscore prefix marks it server-set — it is written AFTER the
        # allowlist filter above, so a client cannot forge it.
        raw_ua = request.headers.get("User-Agent") or ""
        metadata["_ua_class"] = _classify_user_agent(raw_ua)

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


def compute_funnel_metrics(start_dt=None, end_dt=None):
    """Compute qualified-human funnel counts and conversion rates."""
    now = datetime.utcnow()
    query = AnalyticsEvent.query
    if start_dt:
        query = query.filter(AnalyticsEvent.timestamp >= start_dt)
    if end_dt:
        query = query.filter(AnalyticsEvent.timestamp <= end_dt)

    all_events = query.all()

    session_events_map: Dict[str, list] = {}
    for event in all_events:
        sid = event.session_id or f"anon_{event.id}"
        if sid not in session_events_map:
            session_events_map[sid] = []
        session_events_map[sid].append(event)

    landing_sessions = 0
    # Sessions we could not classify because they predate the 2026-09-03
    # server-side UA classification. Reported, never folded into the counts:
    # "we don't know" is a third answer, not a quiet zero.
    unclassified_sessions = 0
    cta_clicks = 0
    web_app_opens = 0
    compliance_passed = 0
    first_value_actions = 0
    returning_users = 0

    min_window_ts = None
    max_window_ts = None

    DEFAULT_UA = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    first_val_types = {"first_chat_message", "first_chat_message_sent", "mood_tracked", "first_value_action"}

    for sid, events in session_events_map.items():
        session_meta: Dict[str, Any] = {}
        user_agent = None
        timestamps = []

        has_landing = False
        has_cta_click = False
        has_web_app_open = False
        has_compliance_passed = False
        has_first_value = False

        for e in events:
            if e.timestamp:
                timestamps.append(e.timestamp)
            meta = e.event_metadata or {}
            if isinstance(meta, dict):
                session_meta.update(meta)
                if not user_agent:
                    user_agent = meta.get("user_agent") or meta.get("ua") or meta.get("user_agent_string")

            etype = e.event_type
            if etype == "cta_impression":
                has_landing = True
            elif etype == "cta_click":
                has_cta_click = True
            elif etype == "web_app_open_from_cta":
                has_web_app_open = True
            elif etype == "compliance_passed":
                has_compliance_passed = True

            if etype in first_val_types or (isinstance(meta, dict) and meta.get("action_type") == "mood_tracked"):
                has_first_value = True

        if timestamps:
            min_ts = min(timestamps)
            max_ts = max(timestamps)
            if min_window_ts is None or min_ts < min_window_ts:
                min_window_ts = min_ts
            if max_window_ts is None or max_ts > max_window_ts:
                max_window_ts = max_ts
            duration_sec = (max_ts - min_ts).total_seconds()
        else:
            duration_sec = 0.0

        pageviews = len(events)

        # Use the server-set classification, never a synthetic default.
        #
        # 2026-09-03. This used to be `user_agent if user_agent else
        # DEFAULT_UA`, where DEFAULT_UA is a real desktop-Chrome string. Since
        # the log endpoint stripped user_agent from metadata, the fallback was
        # not a fallback — it was the ONLY path, and it handed a working bot
        # filter the same hardcoded human for every session. The filter could
        # not reject anything on UA grounds.
        #
        # Events written before that fix carry no classification. We do not
        # know whether they were human, and pretending either way is the
        # mistake this is correcting — so they are counted separately as
        # UNCLASSIFIED rather than silently included or silently dropped.
        ua_class = session_meta.get("_ua_class")
        if ua_class is None:
            unclassified_sessions += 1
            continue
        if ua_class != "human":
            continue

        # Session-shape rules (duration, pageviews) still apply on top of the
        # UA verdict; the write-time call deliberately exempted them because it
        # had no session context.
        if not is_qualified_human(session_meta, user_agent or DEFAULT_UA, duration_sec, pageviews):
            continue

        if has_landing:
            landing_sessions += 1
        if has_cta_click:
            cta_clicks += 1
        if has_web_app_open:
            web_app_opens += 1
        if has_compliance_passed:
            compliance_passed += 1
        if has_first_value:
            first_value_actions += 1

        if timestamps:
            sorted_ts = sorted(timestamps)
            first_ts = sorted_ts[0]
            if any((t - first_ts).total_seconds() >= 86400 for t in sorted_ts):
                returning_users += 1

    cta_ctr = round(cta_clicks / landing_sessions, 4) if landing_sessions > 0 else 0.0
    first_value_conversion = round(first_value_actions / landing_sessions, 4) if landing_sessions > 0 else 0.0

    w_start = (start_dt or min_window_ts or now).isoformat()
    w_end = (end_dt or max_window_ts or now).isoformat()

    return {
        "window": {
            "start": w_start,
            "end": w_end
        },
        "counts": {
            "landing_sessions": landing_sessions,
            "cta_clicks": cta_clicks,
            "web_app_opens": web_app_opens,
            "compliance_passed": compliance_passed,
            "first_value_actions": first_value_actions,
            "returning_users": returning_users,
            "unclassified_sessions": unclassified_sessions
        },
        "cta_ctr": cta_ctr,
        "first_value_conversion": first_value_conversion,
        # True when unclassified sessions outnumber the ones we could verify.
        # The counts above are then a floor, not a measurement, and must not be
        # quoted as a funnel result.
        "insufficient_data": unclassified_sessions > landing_sessions
    }


@analytics_bp.route("/api/metrics/funnel", methods=["GET"])
def funnel_metrics():
    """Returns qualified-human funnel counts and conversion rates (Activation Proof Task 6)."""
    try:
        now = datetime.utcnow()
        days = request.args.get("days", type=int)
        if days:
            start_dt = now - timedelta(days=days)
            end_dt = now
        else:
            start_str = request.args.get("start")
            end_str = request.args.get("end")
            start_dt = datetime.fromisoformat(start_str) if start_str else None
            end_dt = datetime.fromisoformat(end_str) if end_str else None

        res = compute_funnel_metrics(start_dt, end_dt)
        return jsonify(res), 200

    except Exception as e:
        current_app.logger.error(f"Funnel metrics error: {e}")
        return jsonify({"error": "Failed to compute funnel metrics"}), 500


@analytics_bp.route("/api/metrics/onboarding_funnel", methods=["GET"])
def onboarding_funnel_metrics():
    """GA4-sourced install -> compliance -> first-chat funnel, native only.

    2026-08-31: the backend's own analytics_events table (compliance_passed,
    first_chat_message) is gated behind the dead `analytics_consent` opt-in
    (see lib/services/analytics_service.dart) and is not a representative
    signal of real usage. This route reads GA4 directly instead, which is
    gated only by the shipped Anonymity Mode opt-out. See
    metrics/onboarding_funnel_ga4.py for the full rationale.
    """
    try:
        from metrics.onboarding_funnel_ga4 import collect_onboarding_funnel

        days = request.args.get("days", type=int) or 7
        result = collect_onboarding_funnel(days=days)
        status_code = 200 if result.get("status") == "ok" else 502
        return jsonify(result), status_code
    except Exception as e:
        current_app.logger.error(f"Onboarding funnel error: {e}")
        return jsonify({"status": "error", "reason": "unexpected_error"}), 500


@analytics_bp.route("/api/feedback", methods=["POST"])
def submit_feedback():
    """In-app feedback widget submission.

    ADR-005 criterion (iii) — human voice. Each row here is a candidate
    entry for the human_voice_ledger (source_type='feedback_backend').
    Uses raw SQL to avoid ORM model issues with PG reserved word 'trigger'.
    """
    from sqlalchemy import text

    data = request.get_json() or {}
    rating = data.get("rating")
    feedback_text = (data.get("feedback") or "").strip() or None
    session_id = data.get("session_id")
    trigger = data.get("trigger", "after_3rd_checkin")
    country = data.get("country")
    app_version = data.get("app_version")

    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({"error": "rating must be an integer 1-5"}), 400

    try:
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        dialect = inspector.dialect.name

        # Check if "trigger" column exists (PG migration creates it, SQLite db.create_all doesn't)
        has_trigger_col = False
        try:
            cols = inspector.get_columns("user_feedback")
            has_trigger_col = any(c["name"] == "trigger" for c in cols)
        except Exception:
            pass  # Table may not exist yet

        if dialect == "sqlite":
            db.session.execute(text(
                'INSERT INTO user_feedback (session_id, rating, feedback_text, country, app_version, created_at) '
                "VALUES (:sid, :rating, :ftext, :country, :ver, datetime('now'))"
            ), {
                "sid": session_id, "rating": rating, "ftext": feedback_text,
                "country": country, "ver": app_version,
            })
            db.session.commit()
            new_id = db.session.execute(text("SELECT last_insert_rowid()")).scalar()
        else:
            # Postgres — use trigger column
            result = db.session.execute(text(
                'INSERT INTO user_feedback (session_id, rating, feedback_text, "trigger", country, app_version, created_at) '
                "VALUES (:sid, :rating, :ftext, :trig, :country, :ver, NOW()) RETURNING id"
            ), {
                "sid": session_id, "rating": rating, "ftext": feedback_text,
                "trig": trigger, "country": country, "ver": app_version,
            })
            new_id = result.scalar()
            db.session.commit()

        current_app.logger.info(
            f"UserFeedback: rating={rating} id={new_id} session={session_id}"
        )
        return jsonify({"success": True, "id": new_id}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Feedback submit error: {e}")
        return jsonify({"error": "Failed to store feedback"}), 500


def _simulator_filter():
    """Build a GA4 dimension filter that excludes simulator/emulator device models.

    Excluded patterns:
    - "arm64" (exact) — iOS simulators report this generic model
    - "sdk_gphone*" (contains) — Android emulators
    - "Android SDK built for*" (contains) — Android emulators
    """
    try:
        from google.analytics.data_v1beta.types import (
            FilterExpression, FilterExpressionList, Filter
        )

        def _not_match(field, value, match_type):
            return FilterExpression(
                not_expression=FilterExpression(
                    filter=Filter(
                        field_name=field,
                        string_filter=Filter.StringFilter(
                            value=value,
                            match_type=match_type,
                        )
                    )
                )
            )

        return FilterExpression(
            and_group=FilterExpressionList(
                expressions=[
                    _not_match("deviceModel", "arm64", Filter.StringFilter.MatchType.EXACT),
                    _not_match("deviceModel", "sdk_gphone", Filter.StringFilter.MatchType.CONTAINS),
                    _not_match("deviceModel", "Android SDK built for", Filter.StringFilter.MatchType.CONTAINS),
                ]
            )
        )
    except ImportError:
        return None


@analytics_bp.route("/api/metrics/funnel/history", methods=["GET"])
def funnel_history():
    """Historical funnel snapshots from the database.

    Query params:
      limit — number of snapshots to return (default 30, max 100)

    Response freshness:
      ok    — latest snapshot <= 36 hours old with a retention_gate
      stale — latest snapshot > 36 hours old
      empty — no snapshots
    """
    try:
        limit = min(int(request.args.get("limit", 30)), 100)
        snapshots = FunnelSnapshot.query.order_by(
            FunnelSnapshot.created_at.desc()
        ).limit(limit).all()

        freshness = {
            "status": "empty",
            "latest_created_at": None,
            "age_hours": None,
            "retention_gate_status": None,
        }

        if snapshots:
            latest = snapshots[0]
            latest_dt = latest.created_at
            freshness["latest_created_at"] = latest_dt.isoformat()
            now = datetime.utcnow()
            age = now - latest_dt
            freshness["age_hours"] = round(age.total_seconds() / 3600, 2)
            freshness["status"] = "ok" if age <= timedelta(hours=36) else "stale"

            snapshot_data = latest.snapshot_data or {}
            rg = snapshot_data.get("retention_gate")
            if rg is None:
                freshness["retention_gate_status"] = "missing"
            else:
                freshness["retention_gate_status"] = rg.get("status", "error")

        return jsonify({
            "count": len(snapshots),
            "freshness": freshness,
            "snapshots": [
                {
                    "id": s.id,
                    "created_at": s.created_at.isoformat(),
                    "data": s.snapshot_data,
                }
                for s in snapshots
            ],
        }), 200
    except Exception as e:
        current_app.logger.error(f"Funnel history error: {e}")
        return jsonify({"error": "Failed to fetch funnel history"}), 500


@analytics_bp.route("/metrics", methods=["GET"])
def metrics_dashboard():
    """Integrated dashboard: funnel + interventions + trends + recent events.
    Auto-refreshes every 60 seconds."""
    try:
        repo_root = os.path.dirname(os.path.dirname(__file__))
        template_path = os.path.join(repo_root, "templates", "metrics_dashboard.html")
        with open(template_path) as f:
            return f.read(), 200, {"Content-Type": "text/html"}
    except Exception as e:
        current_app.logger.error(f"Dashboard error: {e}")
        return jsonify({"error": "Dashboard unavailable"}), 500
