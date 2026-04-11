"""
Compliance log and IP-region-check endpoints.
Extracted from app.py monolith.
"""

import requests as http_requests

from flask import Blueprint, jsonify, request, current_app
from extensions import limiter

compliance_bp = Blueprint("compliance", __name__)


@compliance_bp.route("/api/compliance/log", methods=["POST"])
@limiter.limit("60 per minute")
def log_compliance_event():
    """Log compliance check outcomes from Flutter for funnel analysis."""
    from helpers.session_helpers import _get_or_create_session, _log_analytics_event, background_executor

    data = request.get_json() or {}
    event_type = data.get("event_type", "")
    session_id = _get_or_create_session()
    ALLOWED = {
        "gps_timeout", "gps_permission_denied", "gps_services_disabled",
        "gps_mock_detected", "compliance_passed", "compliance_blocked_region",
        "compliance_error", "compliance_age_blocked", "compliance_web_blocked",
    }
    if event_type not in ALLOWED:
        return jsonify({"error": "invalid event_type"}), 400
    background_executor.submit(
        _log_analytics_event, current_app._get_current_object(),
        session_id, f"compliance_{event_type}", data.get("metadata", {})
    )
    return jsonify({"ok": True}), 201


@compliance_bp.route("/api/compliance/ip-region-check", methods=["GET"])
@limiter.limit("10 per minute")
def ip_region_check():
    """IP-based region fallback when GPS fails. Returns region + blocked status."""
    from helpers.session_helpers import _get_or_create_session, _log_analytics_event, background_executor

    ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not ip:
        ip = request.headers.get("X-Real-IP", "")
    if not ip:
        ip = request.remote_addr

    try:
        if ip in ["127.0.0.1", "localhost", "::1"] or ip.startswith(("10.", "172.", "192.168.")):
            return jsonify({"region": "unknown", "country": "unknown", "blocked": False, "method": "ip_fallback"}), 200

        import ipaddress as _ipaddress
        try:
            _ipaddress.ip_address(ip)
        except ValueError:
            return jsonify({"region": "unknown", "country": "unknown", "blocked": False, "method": "ip_fallback", "error": "invalid_ip"}), 200

        response = http_requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            region = data.get("region", "")
            country = data.get("country", "").upper()

            HARD_BAN = {"Illinois"}
            PENDING = {"Utah", "Washington"}
            blocked = region in HARD_BAN or region in PENDING

            session_id = _get_or_create_session()
            background_executor.submit(
                _log_analytics_event, current_app._get_current_object(),
                session_id, "compliance_ip_fallback", {
                    "region": region, "country": country, "blocked": blocked, "ip_masked": ip[:8] + "***",
                }
            )
            return jsonify({"region": region, "country": country, "blocked": blocked, "method": "ip_fallback"}), 200
    except Exception:
        pass

    return jsonify({"region": "unknown", "country": "unknown", "blocked": False, "method": "ip_fallback"}), 200
