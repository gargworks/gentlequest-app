import os

from flask import Blueprint, jsonify, request

from extensions import limiter
from services.push_delivery import send_push

debug_push_bp = Blueprint("debug_push", __name__)


@debug_push_bp.route("/api/debug/push-test", methods=["POST"])
@limiter.limit("20 per hour")
def push_test():
    if os.getenv("DEBUG_PUSH_ENABLED", "false").lower() != "true":
        return jsonify({"error": "debug push disabled"}), 404
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        return jsonify({"error": "Session ID required"}), 400
    payload = request.get_json() or {}
    title = payload.get("title")
    body = payload.get("body")
    category = payload.get("category", "generic")
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "title is required"}), 400
    if not isinstance(body, str) or not body.strip():
        return jsonify({"error": "body is required"}), 400
    return jsonify(send_push(session_id, title.strip(), body.strip(), category=category))
