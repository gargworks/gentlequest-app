import json
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from extensions import limiter
from services.export_email import mask_email, send_user_export_email
from models import (
    AnalyticsEvent,
    AlertAcknowledgment,
    ClinicalAssessment,
    ConversationLog,
    CounselorAlert,
    CrisisEscalation,
    CrisisEvent,
    InterventionOutcome,
    JournalEntry,
    Message,
    MoodEntry,
    QuestProgress,
    SelfAssessmentEntry,
    User,
    UserProfile,
    UserResourceInteraction,
    UserResourcePref,
    UserSession,
    db,
)

user_settings_bp = Blueprint("user_settings", __name__)


def _session_id_from_request(create: bool = True):
    session_id = request.headers.get("X-Session-ID")
    if session_id and create and not db.session.get(UserSession, session_id):
        db.session.add(UserSession(id=session_id))
        db.session.commit()
    return session_id


def _get_or_create_user(session_id: str) -> User:
    if not db.session.get(UserSession, session_id):
        db.session.add(UserSession(id=session_id))
        db.session.flush()
    user = User.query.filter_by(session_id=session_id, deleted_at=None).first()
    if user:
        return user
    email = request.headers.get("X-User-Email") or None
    user = User(session_id=session_id, email=email)
    db.session.add(user)
    db.session.commit()
    return user


def _require_user(create: bool = True):
    session_id = _session_id_from_request(create=create)
    if not session_id:
        return None, None, (jsonify({"error": "Session ID required"}), 400)
    return session_id, _get_or_create_user(session_id), None


def _iso(value):
    return value.isoformat() if value and hasattr(value, "isoformat") else value


def _json_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return value
    return value


def _mood_entry(entry: MoodEntry):
    return {
        "mood_level": entry.mood_level,
        "note": entry.note,
        "contextChips": entry.context_chips or [],
        "timestamp": _iso(entry.timestamp),
    }


def _journal_entry(entry: JournalEntry):
    return {
        "id": entry.id,
        "title": entry.title,
        "body": entry.body,
        "moodTag": entry.mood_tag,
        "createdAt": _iso(entry.created_at),
        "updatedAt": _iso(entry.updated_at),
        "deletedAt": _iso(entry.deleted_at),
    }


def _message_entry(message: Message):
    return {
        "content": message.content,
        "is_user": message.is_user,
        "timestamp": _iso(message.timestamp),
        "risk_level": message.risk_level,
        "message_type": message.message_type,
    }


def _assessment_entry(entry: SelfAssessmentEntry):
    return {
        "timestamp": _iso(entry.timestamp),
        "assessment_data": entry.assessment_data,
    }


def _analytics_entry(entry: AnalyticsEvent, anonymity_mode: bool):
    metadata = dict(entry.event_metadata or {})
    if anonymity_mode:
        for key in ("ip", "ip_address", "ip_masked", "device_id", "firebase_app_instance_id"):
            metadata.pop(key, None)
    return {
        "event_type": entry.event_type,
        "metadata": metadata,
        "timestamp": _iso(entry.timestamp),
    }


@user_settings_bp.route("/api/user", methods=["GET"])
@limiter.limit("120 per minute")
def get_user_settings():
    session_id, user, error = _require_user(create=True)
    if error:
        return error
    return jsonify({
        "session_id": session_id,
        "email": None if user.anonymity_mode else user.email,
        "anonymity_mode": bool(user.anonymity_mode),
        "notification_prefs": user.notification_prefs or {},
        "deleted_at": _iso(user.deleted_at),
    })


@user_settings_bp.route("/api/user/export", methods=["POST"])
@limiter.limit("10 per hour")
def export_user_data():
    session_id, user, error = _require_user(create=True)
    if error:
        return error
    anonymity_mode = bool(user.anonymity_mode)
    bundle = {
        "delivery": "inline_json",
        "email_infra": "not_configured_for_user_exports",
        "session_id": session_id,
        "profile": {
            "email": None if anonymity_mode else user.email,
            "created_at": _iso(user.created_at),
            "anonymity_mode": anonymity_mode,
            "notification_prefs": user.notification_prefs or {},
        },
        "mood_entries": [_mood_entry(e) for e in MoodEntry.query.filter_by(session_id=session_id).all()],
        "journal_entries": [_journal_entry(e) for e in JournalEntry.query.filter_by(session_id=session_id).all()],
        "chat_history": [_message_entry(m) for m in Message.query.filter_by(session_id=session_id).order_by(Message.timestamp.asc()).all()],
        "self_assessments": [_assessment_entry(a) for a in SelfAssessmentEntry.query.filter_by(session_id=session_id).all()],
        "analytics_events": [_analytics_entry(a, anonymity_mode) for a in AnalyticsEvent.query.filter_by(session_id=session_id).all()],
        "counts": {
            "mood_entries": MoodEntry.query.filter_by(session_id=session_id).count(),
            "journal_entries": JournalEntry.query.filter_by(session_id=session_id).count(),
            "chat_messages": Message.query.filter_by(session_id=session_id).count(),
            "self_assessments": SelfAssessmentEntry.query.filter_by(session_id=session_id).count(),
            "analytics_events": AnalyticsEvent.query.filter_by(session_id=session_id).count(),
        },
    }
    if not anonymity_mode and user.email:
        try:
            result = send_user_export_email(user.email, bundle)
        except Exception as exc:
            current_app.logger.warning("user export email failed; falling back to inline", exc_info=exc)
        else:
            if result.get("sent"):
                return jsonify({"delivery": "email", "email": mask_email(user.email)}), 202

    return jsonify(bundle), 200


@user_settings_bp.route("/api/user", methods=["DELETE"])
@limiter.limit("10 per hour")
def delete_user_data():
    session_id, user, error = _require_user(create=False)
    if error:
        return error
    alert_ids = [
        alert_id
        for (alert_id,) in CounselorAlert.query.with_entities(CounselorAlert.id).filter_by(session_id=session_id).all()
    ]
    if alert_ids:
        AlertAcknowledgment.query.filter(AlertAcknowledgment.alert_id.in_(alert_ids)).delete(synchronize_session=False)
    CounselorAlert.query.filter_by(session_id=session_id).delete(synchronize_session=False)
    CrisisEscalation.query.filter_by(session_id=session_id).delete(synchronize_session=False)
    CrisisEvent.query.filter_by(session_id=session_id).delete(synchronize_session=False)
    ClinicalAssessment.query.filter_by(session_id=session_id).delete(synchronize_session=False)
    SelfAssessmentEntry.query.filter_by(session_id=session_id).delete(synchronize_session=False)
    InterventionOutcome.query.filter_by(session_id=session_id).delete(synchronize_session=False)
    UserResourceInteraction.query.filter_by(session_id=session_id).delete(synchronize_session=False)
    UserResourcePref.query.filter_by(session_id=session_id).delete(synchronize_session=False)
    QuestProgress.query.filter_by(session_id=session_id).delete(synchronize_session=False)
    UserProfile.query.filter_by(session_id=session_id).delete(synchronize_session=False)
    AnalyticsEvent.query.filter_by(session_id=session_id).delete(synchronize_session=False)
    ConversationLog.query.filter_by(session_id=session_id).delete(synchronize_session=False)
    Message.query.filter_by(session_id=session_id).delete(synchronize_session=False)
    MoodEntry.query.filter_by(session_id=session_id).delete(synchronize_session=False)
    JournalEntry.query.filter_by(session_id=session_id).delete(synchronize_session=False)
    user.deleted_at = datetime.utcnow()
    user.email = None
    user.anonymity_mode = True
    user.notification_prefs = {}
    user.session_id = None
    session = db.session.get(UserSession, session_id)
    if session:
        db.session.delete(session)
    db.session.commit()
    return jsonify({"deleted": True})


@user_settings_bp.route("/api/user/anonymity", methods=["POST"])
@limiter.limit("60 per minute")
def set_anonymity_mode():
    _, user, error = _require_user(create=True)
    if error:
        return error
    data = request.get_json() or {}
    if not isinstance(data.get("enabled"), bool):
        return jsonify({"error": "enabled must be a boolean"}), 400
    user.anonymity_mode = data["enabled"]
    db.session.commit()
    return jsonify({"anonymity_mode": bool(user.anonymity_mode)})


@user_settings_bp.route("/api/user/notification_prefs", methods=["GET"])
@limiter.limit("120 per minute")
def get_notification_prefs():
    _, user, error = _require_user(create=True)
    if error:
        return error
    return jsonify(user.notification_prefs or {})


@user_settings_bp.route("/api/user/notification_prefs", methods=["POST"])
@limiter.limit("60 per minute")
def set_notification_prefs():
    _, user, error = _require_user(create=True)
    if error:
        return error
    data = request.get_json() or {}
    if not isinstance(data, dict):
        return jsonify({"error": "notification preferences must be an object"}), 400
    if len(json.dumps(data)) > 4096:
        return jsonify({"error": "notification preferences payload too large"}), 400
    user.notification_prefs = data
    db.session.commit()
    return jsonify(user.notification_prefs or {})
