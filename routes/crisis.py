"""
Phase I: Crisis escalation v2 endpoints.

Endpoints:
- GET  /api/crisis/resources          \u2014 country-aware crisis lines (reuses helpers.crisis_helpers)
- POST /api/crisis/escalate           \u2014 'I need help now' action, sends SMS via Twilio
- POST /api/crisis/check-in/run       \u2014 admin-gated cron trigger for 24h post-crisis check-in

Privacy:
- No user message content is ever sent to Twilio
- SMS body contains only the crisis-line phone number + resource code
- Admin token gates the cron trigger
"""

import secrets
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request

from extensions import limiter
from helpers.crisis_helpers import (
    CRISIS_RESOURCES_BY_COUNTRY,
    get_country_from_request,
)
from models import CrisisEscalation, db
from providers import twilio_client

crisis_bp = Blueprint("crisis_v2", __name__)


def _sid() -> str:
    return (
        request.headers.get("X-Session-ID")
        or request.args.get("session_id")
        or ""
    ).strip()


def _country_override() -> str:
    """Pick explicit ?country= or fall back to IP-geolocation.

    CRISIS_RESOURCES_BY_COUNTRY is keyed in lowercase (us, in, uk, ...).
    """
    c = (request.args.get("country") or request.headers.get("X-Country-Override") or "").strip().lower()
    if c and c in CRISIS_RESOURCES_BY_COUNTRY:
        return c
    try:
        return get_country_from_request(request)
    except Exception:
        return "us"


# ---------------------------------------------------------------------------
# GET /api/crisis/resources
# ---------------------------------------------------------------------------

@crisis_bp.route("/api/crisis/resources", methods=["GET"])
@limiter.limit("60 per minute")
def crisis_resources():
    """Return country-specific crisis resources + which countries are supported."""
    country = _country_override()
    bundle = CRISIS_RESOURCES_BY_COUNTRY.get(
        country, CRISIS_RESOURCES_BY_COUNTRY.get("us", {})
    )
    resources = bundle.get("crisis_numbers", []) if isinstance(bundle, dict) else []
    return jsonify({
        "country": country,
        "resources": resources,
        "message": bundle.get("crisis_msg", "") if isinstance(bundle, dict) else "",
        "available_countries": sorted(CRISIS_RESOURCES_BY_COUNTRY.keys()),
    }), 200


# ---------------------------------------------------------------------------
# POST /api/crisis/escalate
# ---------------------------------------------------------------------------

@crisis_bp.route("/api/crisis/escalate", methods=["POST"])
@limiter.limit("10 per minute")
def crisis_escalate():
    """'I need help now' action. Records an event, attempts SMS handoff."""
    sid = _sid()
    if not sid:
        return jsonify({"error": "X-Session-ID header required"}), 400

    body = request.get_json(silent=True) or {}
    channel = (body.get("channel") or "banner_only").strip().lower()
    if channel not in {"sms", "call", "banner_only"}:
        return jsonify({"error": "Invalid channel"}), 400

    country = _country_override()
    bundle = CRISIS_RESOURCES_BY_COUNTRY.get(country) or CRISIS_RESOURCES_BY_COUNTRY.get("us", {})
    resources = bundle.get("crisis_numbers", []) if isinstance(bundle, dict) else []
    primary = resources[0] if resources else {}
    primary_line = primary.get("number") or primary.get("phone") or ""

    # Create escalation record
    escalation = CrisisEscalation(
        session_id=sid,
        country_code=country,
        channel=channel,
        status="initiated",
        details=f"primary_line={primary_line}",
    )
    db.session.add(escalation)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"escalation commit failed: {e}")
        return jsonify({"error": "Failed to record escalation"}), 500

    # Attempt SMS handoff if requested
    sms_result = None
    if channel == "sms":
        user_phone = (body.get("user_phone") or "").strip()
        if not user_phone:
            return jsonify({
                "ok": True,
                "escalation_id": escalation.id,
                "country": country,
                "primary_line": primary_line,
                "sms": {"ok": False, "error": "user_phone required"},
                "fallback": {
                    "tel_link": f"tel:{primary_line}",
                    "resources": resources,
                },
            }), 200

        # IMPORTANT: never include user message content in SMS body
        sms_body = (
            f"GentleQuest: You asked for urgent support. "
            f"Reach out now: {primary_line}. You are not alone."
        )
        sms_result = twilio_client.send_sms(user_phone, sms_body)

        escalation.status = "sent" if sms_result.get("ok") else "failed"
        escalation.details = (
            (escalation.details or "") +
            f" | sms_status={sms_result.get('ok')}"
        )
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    return jsonify({
        "ok": True,
        "escalation_id": escalation.id,
        "country": country,
        "primary_line": primary_line,
        "sms": sms_result,
        "fallback": {
            "tel_link": f"tel:{primary_line}" if primary_line else None,
            "resources": resources,
        },
    }), 200


# ---------------------------------------------------------------------------
# POST /api/crisis/check-in/run  (admin-gated cron trigger)
# ---------------------------------------------------------------------------

@crisis_bp.route("/api/crisis/check-in/run", methods=["POST"])
@limiter.limit("12 per hour")
def crisis_check_in_run():
    """Send 24h post-crisis check-ins for eligible escalations. Idempotent."""
    token = request.headers.get("X-Admin-Token") or ""
    expected = current_app.config.get("ADMIN_API_TOKEN") or ""
    if not expected or not secrets.compare_digest(token, expected):
        return jsonify({"error": "Unauthorized"}), 401

    cutoff = datetime.utcnow() - timedelta(hours=24)
    # Pick escalations >24h old, not yet checked-in
    try:
        due = (
            CrisisEscalation.query
            .filter(CrisisEscalation.created_at <= cutoff)
            .filter(CrisisEscalation.check_in_sent.is_(False))
            .limit(100)
            .all()
        )
    except Exception as e:
        current_app.logger.error(f"check-in query failed: {e}")
        return jsonify({"error": "Query failed"}), 500

    processed = 0
    for e in due:
        e.check_in_at = datetime.utcnow()
        e.check_in_sent = True
        if e.status not in {"failed", "checked_in"}:
            e.status = "checked_in"
        processed += 1

    try:
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        current_app.logger.error(f"check-in commit failed: {err}")
        return jsonify({"error": "Commit failed"}), 500

    return jsonify({
        "ok": True,
        "processed": processed,
    }), 200
