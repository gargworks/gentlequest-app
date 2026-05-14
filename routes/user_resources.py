from datetime import datetime

from flask import Blueprint, jsonify, request

from extensions import limiter
from helpers.session_helpers import _get_or_create_session
from models import UserResourcePref, db

user_resources_bp = Blueprint("user_resources", __name__)


def _resource_id_from_payload():
    payload = request.get_json() or {}
    resource_id = payload.get("resource_id")
    if not isinstance(resource_id, str) or not resource_id.strip():
        return None, (jsonify({"error": "resource_id is required"}), 400)
    return resource_id.strip(), None


def _get_or_create_pref(session_id, resource_id):
    pref = UserResourcePref.query.filter_by(session_id=session_id, resource_id=resource_id).first()
    if not pref:
        pref = UserResourcePref(session_id=session_id, resource_id=resource_id)
        db.session.add(pref)
    return pref


@user_resources_bp.route("/api/user/resources/favorite", methods=["POST"])
@limiter.limit("120 per minute")
def set_resource_favorite():
    session_id = _get_or_create_session()
    payload = request.get_json() or {}
    resource_id = payload.get("resource_id")
    if not isinstance(resource_id, str) or not resource_id.strip():
        return jsonify({"error": "resource_id is required"}), 400
    favorite = payload.get("favorite")
    if not isinstance(favorite, bool):
        return jsonify({"error": "favorite must be a boolean"}), 400
    pref = _get_or_create_pref(session_id, resource_id.strip())
    pref.is_favorite = favorite
    db.session.commit()
    return jsonify({"resource_id": pref.resource_id, "favorite": pref.is_favorite})


@user_resources_bp.route("/api/user/resources/opened", methods=["POST"])
@limiter.limit("120 per minute")
def mark_resource_opened():
    session_id = _get_or_create_session()
    resource_id, error = _resource_id_from_payload()
    if error:
        return error
    pref = _get_or_create_pref(session_id, resource_id)
    pref.last_opened_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"resource_id": pref.resource_id, "lastOpenedAt": pref.last_opened_at.isoformat()})


@user_resources_bp.route("/api/user/resources/favorites", methods=["GET"])
@limiter.limit("120 per minute")
def list_resource_favorites():
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        return jsonify([])
    prefs = UserResourcePref.query.filter_by(session_id=session_id, is_favorite=True).order_by(UserResourcePref.resource_id.asc()).all()
    return jsonify([pref.resource_id for pref in prefs])


@user_resources_bp.route("/api/user/resources/recents", methods=["GET"])
@limiter.limit("120 per minute")
def list_resource_recents():
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        return jsonify([])
    try:
        limit = int(request.args.get("limit", 3))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400
    limit = max(1, min(limit, 50))
    prefs = (
        UserResourcePref.query.filter(UserResourcePref.session_id == session_id, UserResourcePref.last_opened_at.isnot(None))
        .order_by(UserResourcePref.last_opened_at.desc())
        .limit(limit)
        .all()
    )
    return jsonify([pref.resource_id for pref in prefs])
