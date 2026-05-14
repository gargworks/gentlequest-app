from datetime import datetime

from flask import Blueprint, jsonify, request

from extensions import limiter
from helpers.session_helpers import _get_or_create_session
from models import JournalEntry, db

journal_bp = Blueprint("journal", __name__)

MAX_BODY_BYTES = 50 * 1024
MAX_TITLE_CHARS = 200
MAX_MOOD_TAG_CHARS = 40


def _iso(value):
    return value.isoformat() if value and hasattr(value, "isoformat") else value


def _entry_json(entry: JournalEntry):
    return {
        "id": entry.id,
        "title": entry.title,
        "body": entry.body,
        "moodTag": entry.mood_tag,
        "createdAt": _iso(entry.created_at),
        "updatedAt": _iso(entry.updated_at),
    }


def _validate_payload(data, partial: bool = False):
    if not isinstance(data, dict):
        return None, (jsonify({"error": "JSON body required"}), 400)
    cleaned = {}
    if "body" in data or not partial:
        body = data.get("body")
        if not isinstance(body, str) or not body.strip():
            return None, (jsonify({"error": "body is required"}), 400)
        body = body.strip()
        if len(body.encode("utf-8")) > MAX_BODY_BYTES:
            return None, (jsonify({"error": "body must be at most 50 KB"}), 400)
        cleaned["body"] = body
    if "title" in data:
        title = data.get("title")
        if title is not None:
            if not isinstance(title, str):
                return None, (jsonify({"error": "title must be a string"}), 400)
            title = title.strip()
            if len(title) > MAX_TITLE_CHARS:
                return None, (jsonify({"error": "title must be at most 200 characters"}), 400)
            cleaned["title"] = title or None
        else:
            cleaned["title"] = None
    if "moodTag" in data:
        mood_tag = data.get("moodTag")
        if mood_tag is not None:
            if not isinstance(mood_tag, str):
                return None, (jsonify({"error": "moodTag must be a string"}), 400)
            mood_tag = mood_tag.strip()
            if len(mood_tag) > MAX_MOOD_TAG_CHARS:
                return None, (jsonify({"error": "moodTag must be at most 40 characters"}), 400)
            cleaned["mood_tag"] = mood_tag or None
        else:
            cleaned["mood_tag"] = None
    return cleaned, None


def _parse_before(value):
    if not value:
        return None, None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")), None
    except ValueError:
        return None, (jsonify({"error": "before must be an ISO-8601 timestamp"}), 400)


def _parse_limit(value):
    if not value:
        return 50, None
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return None, (jsonify({"error": "limit must be an integer"}), 400)
    if limit < 1 or limit > 100:
        return None, (jsonify({"error": "limit must be between 1 and 100"}), 400)
    return limit, None


@journal_bp.route("/api/journal", methods=["POST"])
@limiter.limit("120 per minute")
def create_journal_entry():
    session_id = _get_or_create_session()
    data, error = _validate_payload(request.get_json() or {})
    if error:
        return error
    entry = JournalEntry(
        session_id=session_id,
        title=data.get("title"),
        body=data["body"],
        mood_tag=data.get("mood_tag"),
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(_entry_json(entry)), 201


@journal_bp.route("/api/journal", methods=["GET"])
@limiter.limit("120 per minute")
def list_journal_entries():
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        return jsonify({"error": "Session ID required"}), 400
    limit, limit_error = _parse_limit(request.args.get("limit"))
    if limit_error:
        return limit_error
    before, before_error = _parse_before(request.args.get("before"))
    if before_error:
        return before_error
    query = JournalEntry.query.filter_by(session_id=session_id, deleted_at=None)
    if before:
        query = query.filter(JournalEntry.created_at < before)
    entries = query.order_by(JournalEntry.created_at.desc()).limit(limit).all()
    return jsonify([_entry_json(entry) for entry in entries])


@journal_bp.route("/api/journal/<entry_id>", methods=["PATCH"])
@limiter.limit("120 per minute")
def update_journal_entry(entry_id):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        return jsonify({"error": "Session ID required"}), 400
    entry = JournalEntry.query.filter_by(id=entry_id, session_id=session_id, deleted_at=None).first()
    if not entry:
        return jsonify({"error": "Journal entry not found"}), 404
    data, error = _validate_payload(request.get_json() or {}, partial=True)
    if error:
        return error
    if not data:
        return jsonify({"error": "No fields provided"}), 400
    for key, value in data.items():
        setattr(entry, key, value)
    entry.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_entry_json(entry))


@journal_bp.route("/api/journal/<entry_id>", methods=["DELETE"])
@limiter.limit("120 per minute")
def delete_journal_entry(entry_id):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        return jsonify({"error": "Session ID required"}), 400
    entry = JournalEntry.query.filter_by(id=entry_id, session_id=session_id, deleted_at=None).first()
    if not entry:
        return jsonify({"error": "Journal entry not found"}), 404
    entry.deleted_at = datetime.utcnow()
    entry.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"deleted": True})
