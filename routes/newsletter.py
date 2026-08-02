"""Newsletter subscription endpoint for the GentleQuest blog."""
import re
from flask import Blueprint, request, jsonify, current_app
from models import db, NewsletterSubscriber

newsletter_bp = Blueprint("newsletter", __name__)

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@newsletter_bp.route("/api/newsletter/subscribe", methods=["POST", "OPTIONS"])
def subscribe():
    """Subscribe an email to the newsletter."""
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    source = (data.get("source") or "blog").strip()[:50]

    if not email or not EMAIL_RE.match(email):
        return jsonify({"error": "Valid email required"}), 400

    if len(email) > 255:
        return jsonify({"error": "Email too long"}), 400

    try:
        existing = NewsletterSubscriber.query.filter_by(email=email).first()
        if existing:
            if not existing.active:
                existing.active = True
                existing.source = source
                db.session.commit()
                return jsonify({"ok": True, "message": "Welcome back! You're resubscribed."}), 200
            return jsonify({"ok": True, "message": "You're already subscribed."}), 200

        sub = NewsletterSubscriber(email=email, source=source)
        db.session.add(sub)
        db.session.commit()
        current_app.logger.info(f"Newsletter subscription: {email} (source={source})")
        return jsonify({"ok": True, "message": "Subscribed! Check your inbox soon."}), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Newsletter subscribe error: {e}")
        return jsonify({"error": "Something went wrong. Please try again."}), 500


@newsletter_bp.route("/api/newsletter/unsubscribe", methods=["POST", "OPTIONS"])
def unsubscribe():
    """Unsubscribe an email from the newsletter."""
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"error": "Email required"}), 400

    try:
        sub = NewsletterSubscriber.query.filter_by(email=email).first()
        if sub:
            sub.active = False
            db.session.commit()
        return jsonify({"ok": True, "message": "Unsubscribed."}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Newsletter unsubscribe error: {e}")
        return jsonify({"error": "Something went wrong."}), 500
