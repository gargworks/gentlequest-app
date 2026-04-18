"""
Mood Insights Dashboard — read-only analytics endpoints.

All endpoints are session-scoped via X-Session-ID header. They aggregate
existing MoodEntry, Message, and InterventionOutcome data; no new writes.

Endpoints:
- GET /api/insights/weekly           — mean/stdev/daily-bucket trend
- GET /api/insights/keywords         — crisis-keyword heatmap (anonymized)
- GET /api/insights/quest-correlation — pre/post mood delta per quest type
- GET /api/insights/next-steps       — personalized 3 CTAs
"""

from flask import Blueprint, current_app, jsonify, request

from extensions import limiter
from helpers.insights_helpers import (
    compute_keyword_heatmap,
    compute_next_steps,
    compute_quest_correlation,
    compute_weekly_trend,
)
from models import InterventionOutcome, Message, MoodEntry

insights_bp = Blueprint("insights", __name__)

# Allowed windows (days) — tighter than analytics to keep responses fast
ALLOWED_WINDOWS = {7, 30, 90}


def _get_session_id() -> str:
    """Require X-Session-ID; fall back to query param for convenience."""
    return (
        request.headers.get("X-Session-ID")
        or request.args.get("session_id")
        or ""
    ).strip()


def _parse_window(default: int = 7) -> int:
    """Parse ?window=N query arg; must be one of ALLOWED_WINDOWS."""
    try:
        w = int(request.args.get("window", default))
    except (TypeError, ValueError):
        w = default
    return w if w in ALLOWED_WINDOWS else default


@insights_bp.route("/api/insights/weekly", methods=["GET"])
@limiter.limit("30 per minute")
def insights_weekly():
    """Mood trend for the session — mean/stdev/daily buckets."""
    sid = _get_session_id()
    if not sid:
        return jsonify({"error": "X-Session-ID header required"}), 400

    window = _parse_window(7)
    try:
        entries = MoodEntry.query.filter_by(session_id=sid).all()
        trend = compute_weekly_trend(entries, window_days=window)
        return jsonify(trend), 200
    except Exception as e:
        current_app.logger.error(f"insights/weekly error: {e}")
        return jsonify({"error": "Failed to compute trend"}), 500


@insights_bp.route("/api/insights/keywords", methods=["GET"])
@limiter.limit("30 per minute")
def insights_keywords():
    """Anonymized crisis-keyword frequency heatmap (buckets × dates)."""
    sid = _get_session_id()
    if not sid:
        return jsonify({"error": "X-Session-ID header required"}), 400

    window = _parse_window(30)
    try:
        messages = Message.query.filter_by(session_id=sid).all()
        heatmap = compute_keyword_heatmap(messages, window_days=window)
        return jsonify(heatmap), 200
    except Exception as e:
        current_app.logger.error(f"insights/keywords error: {e}")
        return jsonify({"error": "Failed to compute heatmap"}), 500


@insights_bp.route("/api/insights/quest-correlation", methods=["GET"])
@limiter.limit("30 per minute")
def insights_quest_correlation():
    """Average mood delta per intervention type (pre/post)."""
    sid = _get_session_id()
    if not sid:
        return jsonify({"error": "X-Session-ID header required"}), 400

    try:
        outcomes = InterventionOutcome.query.filter_by(session_id=sid).all()
        return jsonify(compute_quest_correlation(outcomes)), 200
    except Exception as e:
        current_app.logger.error(f"insights/quest-correlation error: {e}")
        return jsonify({"error": "Failed to compute correlation"}), 500


@insights_bp.route("/api/insights/next-steps", methods=["GET"])
@limiter.limit("30 per minute")
def insights_next_steps():
    """Personalized 3 CTAs based on session patterns."""
    sid = _get_session_id()
    if not sid:
        return jsonify({"error": "X-Session-ID header required"}), 400

    try:
        entries = MoodEntry.query.filter_by(session_id=sid).all()
        messages = Message.query.filter_by(session_id=sid).all()
        outcomes = InterventionOutcome.query.filter_by(session_id=sid).all()

        trend = compute_weekly_trend(entries, window_days=7)
        heatmap = compute_keyword_heatmap(messages, window_days=30)
        corr = compute_quest_correlation(outcomes)

        ctas = compute_next_steps(trend, heatmap, corr)
        return jsonify({"next_steps": ctas}), 200
    except Exception as e:
        current_app.logger.error(f"insights/next-steps error: {e}")
        return jsonify({"error": "Failed to compute next steps"}), 500
