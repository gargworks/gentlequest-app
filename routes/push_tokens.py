from datetime import datetime

from flask import Blueprint, jsonify, request

from extensions import limiter
from helpers.session_helpers import _get_or_create_session
from models import PushToken, db

push_tokens_bp = Blueprint("push_tokens", __name__)
VALID_PLATFORMS = {"ios", "android", "web"}


def _token_json(token: PushToken):
    return {
        "id": token.id,
        "token": token.token,
        "platform": token.platform,
        "createdAt": token.created_at.isoformat() if token.created_at else None,
    }


@push_tokens_bp.route("/api/user/push-tokens", methods=["POST"])
@limiter.limit("120 per minute")
def upsert_push_token():
    session_id = _get_or_create_session()
    payload = request.get_json() or {}
    token = payload.get("token")
    platform = payload.get("platform")
    if not isinstance(token, str) or not token.strip():
        return jsonify({"error": "token is required"}), 400
    if platform not in VALID_PLATFORMS:
        return jsonify({"error": "platform must be ios, android, or web"}), 400
    token = token.strip()
    push_token = PushToken.query.filter_by(session_id=session_id, token=token).first()
    if not push_token:
        push_token = PushToken(session_id=session_id, token=token, platform=platform)
        db.session.add(push_token)
    else:
        push_token.platform = platform
        push_token.created_at = datetime.utcnow()
        push_token.revoked_at = None
    db.session.commit()
    return jsonify(_token_json(push_token)), 200


@push_tokens_bp.route("/api/user/push-tokens/<path:token>", methods=["DELETE"])
@limiter.limit("120 per minute")
def revoke_push_token(token):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        return jsonify({"error": "Session ID required"}), 400
    push_token = PushToken.query.filter_by(session_id=session_id, token=token, revoked_at=None).first()
    if not push_token:
        return jsonify({"error": "Push token not found"}), 404
    push_token.revoked_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"revoked": True})


@push_tokens_bp.route("/api/user/push-tokens", methods=["GET"])
@limiter.limit("120 per minute")
def list_push_tokens():
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        return jsonify([])
    tokens = PushToken.query.filter_by(session_id=session_id, revoked_at=None).order_by(PushToken.created_at.desc()).all()
    return jsonify([_token_json(token) for token in tokens])
