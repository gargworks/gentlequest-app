from flask import Blueprint, jsonify, request

from extensions import limiter
from helpers.session_helpers import _get_or_create_session
from models import FeedbackSubmission, db

feedback_bp = Blueprint("feedback", __name__)

MAX_FEEDBACK_TEXT_CHARS = 2000
MAX_APP_VERSION_CHARS = 40
MAX_PLATFORM_CHARS = 40

ALLOWED_TRIGGERS = {"after_3rd_checkin", "legacy_v150"}


def _clean_optional_str(value, max_chars):
    """Trim to max_chars, collapse blank-after-strip to None. None passes through."""
    if value is None:
        return None, None
    if not isinstance(value, str):
        return None, "must be a string"
    cleaned = value.strip()[:max_chars]
    return (cleaned or None), None


@feedback_bp.route("/api/feedback", methods=["POST"])
@limiter.limit("30 per minute")
def submit_feedback():
    """Store in-app user feedback (star rating + optional free text).

    Anonymous — no auth. Feedback is an EXPLICIT user act (the user typed text
    and pressed submit), which is its own consent to transmit that content —
    distinct from passive analytics telemetry. Therefore this endpoint does
    NOT require the X-Analytics-Consent header. The anonymity-mode gate is
    enforced client-side (anonymity ON = never transmit); the server persists
    whatever explicit submission it receives.

    Accepts BOTH payload shapes (backward compat with shipped v1.5.0 client):
      NEW:  {rating, text?, trigger?}
      LEGACY v1.5.0: {rating, feedback_text?, session_id, app_version?, platform?}
    - feedback_text maps to the same column as text
    - body session_id honored when X-Session-ID header is absent
    - unknown extras ignored, never 400
    - legacy submissions (no trigger field) get trigger='legacy_v150'
    """
    data = request.get_json(silent=True) or {}

    rating = data.get("rating")
    if not isinstance(rating, int) or isinstance(rating, bool) or not (1 <= rating <= 5):
        return jsonify({"error": "rating must be an integer between 1 and 5"}), 400

    # Text: accept both 'text' (new) and 'feedback_text' (legacy v1.5.0)
    raw_text = data.get("text")
    if raw_text is None:
        raw_text = data.get("feedback_text")
    feedback_text, error = _clean_optional_str(raw_text, MAX_FEEDBACK_TEXT_CHARS)
    if error:
        return jsonify({"error": f"text {error}"}), 400

    # Trigger: new clients send it; legacy v1.5.0 clients don't
    trigger_raw = data.get("trigger")
    if trigger_raw is not None:
        trigger = trigger_raw if isinstance(trigger_raw, str) else str(trigger_raw)
        trigger = trigger.strip()
        if trigger and trigger not in ALLOWED_TRIGGERS:
            return jsonify({"error": f"trigger must be one of {ALLOWED_TRIGGERS}"}), 400
    else:
        # Legacy v1.5.0 payload (no trigger field) — tag it for analytics
        trigger = "legacy_v150"

    app_version, error = _clean_optional_str(data.get("app_version"), MAX_APP_VERSION_CHARS)
    if error:
        return jsonify({"error": f"app_version {error}"}), 400

    platform, error = _clean_optional_str(data.get("platform"), MAX_PLATFORM_CHARS)
    if error:
        return jsonify({"error": f"platform {error}"}), 400

    request_id = request.headers.get("X-Request-ID")
    if request_id and len(request_id) > 64:
        request_id = request_id[:64]

    # Session: honor X-Session-ID header first, then body session_id (legacy),
    # then fall back to _get_or_create_session()
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        body_sid = data.get("session_id")
        if isinstance(body_sid, str) and body_sid.strip():
            session_id = body_sid.strip()
    if not session_id:
        session_id = _get_or_create_session()

    submission = FeedbackSubmission(
        session_id=session_id,
        rating=rating,
        feedback_text=feedback_text,
        trigger=trigger,
        request_id=request_id,
        app_version=app_version,
        platform=platform,
    )
    db.session.add(submission)
    db.session.commit()

    return jsonify({"id": submission.id}), 201
