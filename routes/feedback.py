from flask import Blueprint, jsonify, request

from extensions import limiter
from helpers.session_helpers import _get_or_create_session
from models import FeedbackSubmission, db

feedback_bp = Blueprint("feedback", __name__)

MAX_FEEDBACK_TEXT_CHARS = 2000
MAX_APP_VERSION_CHARS = 40
MAX_PLATFORM_CHARS = 20


def _clean_optional_str(value, max_chars):
    """Trim to max_chars, collapse blank-after-strip to None. None passes through."""
    if value is None:
        return None, None
    if not isinstance(value, str):
        return None, "must be a string"
    cleaned = value.strip()[:max_chars]
    return (cleaned or None), None


@feedback_bp.route("/api/feedback", methods=["POST"])
@limiter.limit("10 per minute")
def submit_feedback():
    """Store in-app user feedback (star rating + optional free text).

    Anonymous — no auth. Fields: rating (int, 1-5, required), feedback_text
    (optional str), app_version (optional str), platform (optional str).
    """
    data = request.get_json(silent=True) or {}

    rating = data.get("rating")
    if not isinstance(rating, int) or isinstance(rating, bool) or not (1 <= rating <= 5):
        return jsonify({"error": "rating must be an integer between 1 and 5"}), 400

    feedback_text, error = _clean_optional_str(data.get("feedback_text"), MAX_FEEDBACK_TEXT_CHARS)
    if error:
        return jsonify({"error": f"feedback_text {error}"}), 400

    app_version, error = _clean_optional_str(data.get("app_version"), MAX_APP_VERSION_CHARS)
    if error:
        return jsonify({"error": f"app_version {error}"}), 400

    platform, error = _clean_optional_str(data.get("platform"), MAX_PLATFORM_CHARS)
    if error:
        return jsonify({"error": f"platform {error}"}), 400

    session_id = _get_or_create_session()

    submission = FeedbackSubmission(
        session_id=session_id,
        rating=rating,
        feedback_text=feedback_text,
        app_version=app_version,
        platform=platform,
    )
    db.session.add(submission)
    db.session.commit()

    return jsonify({"success": True, "id": submission.id}), 201
