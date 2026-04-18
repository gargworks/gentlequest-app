"""
Session management, chat history, mood, assessment, and crisis detection endpoints.
Extracted from app.py monolith.
"""

from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request

from extensions import limiter
from models import Message, MoodEntry, SelfAssessmentEntry, db

session_bp = Blueprint("session", __name__)


def _sanitize_note(note: str) -> str:
    """Basic XSS mitigation for free-text notes."""
    try:
        if not note:
            return note
        return note.replace("<script", "&lt;script").replace(
            "</script", "&lt;/script"
        )
    except Exception:
        return note


@session_bp.route("/api/get_or_create_session", methods=["GET"])
@limiter.limit("60 per hour")
def get_or_create_session_endpoint():
    """Get or create user session"""
    from helpers.session_helpers import _get_or_create_session
    session_id = _get_or_create_session()
    return jsonify({"session_id": session_id})


@session_bp.route("/api/chat_history", methods=["GET"])
@limiter.limit("120 per minute")
def get_chat_history():
    """Get chat history for the current session"""
    try:
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            return jsonify({"error": "Session ID required"}), 400

        messages = Message.query.filter_by(session_id=session_id)\
            .order_by(Message.timestamp.asc())\
            .limit(50).all()

        chat_history = []
        for message in messages:
            ts = message.timestamp
            if ts and hasattr(ts, 'isoformat'):
                ts = ts.isoformat()

            chat_history.append(
                {
                    "content": message.content,
                    "is_user": message.is_user,
                    "timestamp": ts,
                }
            )

        return jsonify(chat_history)

    except Exception as e:
        current_app.logger.error(f"Error getting chat history: {e}")
        return jsonify({"error": "Failed to get chat history"}), 500


@session_bp.route("/api/mood_history", methods=["GET"])
@limiter.limit("120 per minute")
def get_mood_history():
    """Get mood history for the current session"""
    try:
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            return jsonify({"error": "Session ID required"}), 400

        entries = MoodEntry.query.filter_by(session_id=session_id)\
            .order_by(MoodEntry.timestamp.desc())\
            .limit(50).all()

        mood_history = []
        for entry in entries:
            ts = entry.timestamp
            if ts and not isinstance(ts, str) and hasattr(ts, 'isoformat'):
                ts = ts.isoformat()

            mood_history.append(
                {
                    "mood_level": entry.mood_level,
                    "note": _sanitize_note(entry.note),
                    "timestamp": ts,
                }
            )

        return jsonify(mood_history)

    except Exception as e:
        current_app.logger.error(f"Error getting mood history: {e}")
        return jsonify({"error": "Failed to get mood history"}), 500


@session_bp.route("/api/mood_entry", methods=["POST"])
@limiter.limit("120 per minute")
def add_mood_entry():
    """Add a new mood entry"""
    try:
        from helpers.session_helpers import _get_or_create_session

        session_id = _get_or_create_session()
        if not session_id:
            return jsonify({"error": "Session ID required"}), 400

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        mood_level = data.get("mood_level")
        try:
            if mood_level is not None:
                mood_level = int(mood_level)
        except (ValueError, TypeError):
             return jsonify({"error": "Invalid mood level format"}), 400

        note_raw = data.get("note", "")
        timestamp = data.get("timestamp")

        if (
            mood_level is None
            or not isinstance(mood_level, int)
            or mood_level < 1
            or mood_level > 5
        ):
            return jsonify({"error": "Invalid mood level (1-5 required)"}), 400

        if timestamp:
            try:
                entry_timestamp = datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00")
                )
            except ValueError:
                entry_timestamp = datetime.utcnow()
        else:
            entry_timestamp = datetime.utcnow()

        note = _sanitize_note(note_raw)

        entry = MoodEntry(
            session_id=session_id,
            mood_level=mood_level,
            note=note,
            timestamp=entry_timestamp
        )
        db.session.add(entry)
        db.session.commit()

        check_in_count = MoodEntry.query.filter_by(session_id=session_id).count()
        show_feedback_prompt = (check_in_count == 3)

        return jsonify(
            {
                "message": "Mood entry added successfully",
                "mood_level": mood_level,
                "note": note,
                "timestamp": entry_timestamp.isoformat(),
                "show_feedback_prompt": show_feedback_prompt,
            }
        )

    except Exception as e:
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            raise
        current_app.logger.error(f"Error adding mood entry: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to add mood entry"}), 500


@session_bp.route("/api/self_assessment", methods=["POST"])
@limiter.limit("120 per minute")
def submit_self_assessment():
    """Handle self-assessment submissions"""
    if request.method == "GET":
        return jsonify({"message": "Self-assessment endpoint ready"})

    try:
        from helpers.session_helpers import _get_or_create_session

        data = request.get_json() or {}

        session_id = _get_or_create_session()
        if not session_id:
            return jsonify({"error": "Session ID required"}), 400

        cleaned_data = {}
        required_fields = ["mood", "energy", "sleep", "stress"]

        for field in required_fields:
            value = data.get(field)
            if (
                value is None
                or value == ""
                or str(value).lower() in ["null", "none"]
            ):
                return jsonify({"error": f"Missing required field: {field}"}), 400
            cleaned_data[field] = value.strip() if isinstance(value, str) else value

        optional_fields = ["notes", "crisis_level", "anxiety_level"]
        for field in optional_fields:
            value = data.get(field)
            if value and value != "" and str(value).lower() not in ["null", "none"]:
                cleaned_data[field] = (
                    value.strip() if isinstance(value, str) else value
                )

        try:
            tz_offset_min = int(data.get("tz_offset_minutes") or 0)
        except Exception:
            tz_offset_min = 0

        now_utc = datetime.utcnow()
        now_local = now_utc + timedelta(minutes=tz_offset_min)
        start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_day_utc = start_local - timedelta(minutes=tz_offset_min)

        existing = (
            db.session.query(SelfAssessmentEntry)
            .filter(SelfAssessmentEntry.session_id == session_id)
            .filter(SelfAssessmentEntry.timestamp >= start_of_day_utc)
            .first()
        )

        if existing:
            current_app.logger.info(
                f"Self-assessment already completed today | session_id={session_id} completed_at={existing.timestamp.isoformat()} tz_offset_min={tz_offset_min}"
            )
            return (
                jsonify(
                    {
                        "success": True,
                        "already_completed_today": True,
                        "xp_awarded": 0,
                        "completed_at": existing.timestamp.isoformat(),
                    }
                ),
                200,
            )

        entry = SelfAssessmentEntry(
            session_id=session_id,
            timestamp=now_utc,
            assessment_data=cleaned_data,
        )
        db.session.add(entry)
        db.session.commit()

        xp_awarded = 10
        current_app.logger.info(
            f"Self-assessment recorded | session_id={session_id} xp_awarded={xp_awarded} tz_offset_min={tz_offset_min} data_keys={list(cleaned_data.keys())}"
        )

        return (
            jsonify(
                {
                    "message": "Assessment recorded",
                    "success": True,
                    "already_completed_today": False,
                    "xp_awarded": xp_awarded,
                    "completed_at": now_utc.isoformat(),
                }
            ),
            201,
        )

    except Exception as e:
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            raise
        current_app.logger.error(f"Self-assessment error: {e}")
        return jsonify({"error": "Failed to process assessment"}), 500


@session_bp.route("/api/mood_pulse", methods=["GET"])
@limiter.limit("30 per minute")
def mood_pulse():
    """Get anonymous aggregate mood stats for today - 'You Are Not Alone' feature"""
    try:
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        from sqlalchemy import func
        result = db.session.query(
            MoodEntry.mood_level,
            func.count(MoodEntry.id).label('count')
        ).filter(MoodEntry.timestamp >= today_start)\
         .group_by(MoodEntry.mood_level).all()

        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total = 0
        for row in result:
            level = row.mood_level
            count = row.count
            if 1 <= level <= 5:
                distribution[level] = count
                total += count

        percentages = {}
        for level in range(1, 6):
            if total > 0:
                percentages[level] = round((distribution[level] / total) * 100)
            else:
                percentages[level] = 0

        solidarity_messages = {
            1: "You're not alone. Others are having a tough day too.",
            2: "Many people feel this way sometimes. You're not alone.",
            3: "Lots of us are feeling okay today. You're in good company.",
            4: "Others are feeling good too! The positive energy is spreading.",
            5: "You're part of the happiness today! Keep shining.",
        }

        return jsonify(
            {
                "total_checkins_today": total,
                "distribution": distribution,
                "percentages": percentages,
                "solidarity_messages": solidarity_messages,
            }
        )

    except Exception as e:
        current_app.logger.error(f"Mood pulse error: {e}")
        return jsonify({"error": "Failed to get mood pulse"}), 500


@session_bp.route("/api/crisis_detection", methods=["POST"])
@limiter.limit("10 per minute")
def crisis_detection():
    """Enhanced crisis detection with immediate response"""
    try:
        from helpers.crisis_helpers import (
            _enhanced_crisis_detection,
            _get_crisis_resources,
            _get_crisis_response,
            _log_crisis_detection,
        )

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        message = data.get("message", "")
        session_id = request.headers.get("X-Session-ID")

        if not message:
            return jsonify({"error": "Message required"}), 400

        risk_level, risk_score, keywords = _enhanced_crisis_detection(message)
        response = _get_crisis_response(risk_level, risk_score)
        _log_crisis_detection(session_id, message, risk_level, risk_score, keywords)

        return jsonify(
            {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "keywords": keywords,
                "response": response,
                "immediate_action_required": risk_level in ["high", "crisis"],
                "resources": _get_crisis_resources(risk_level),
            }
        )

    except Exception as e:
        current_app.logger.error(f"Crisis detection error: {e}")
        return jsonify({"error": "Failed to process crisis detection"}), 500


@session_bp.route("/api/mood_analytics", methods=["GET"])
@limiter.limit("30 per minute")
def mood_analytics():
    """Get mood analytics and trends"""
    try:
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            return jsonify({"error": "Session ID required"}), 400

        entries = MoodEntry.query.filter_by(session_id=session_id)\
            .order_by(MoodEntry.timestamp.desc())\
            .limit(100).all()

        if not entries:
            return jsonify(
                {
                    "message": "No mood data available",
                    "analytics": {
                        "average_mood": 0,
                        "mood_trend": "stable",
                        "total_entries": 0,
                        "weekly_average": 0,
                        "mood_distribution": {},
                    },
                }
            )

        mood_levels = [entry.mood_level for entry in entries]

        recent_moods = mood_levels[:7] if len(mood_levels) >= 7 else mood_levels
        older_moods = mood_levels[7:14] if len(mood_levels) >= 14 else []

        if older_moods:
            recent_avg = sum(recent_moods) / len(recent_moods)
            older_avg = sum(older_moods) / len(older_moods)
            if recent_avg > older_avg + 0.5:
                trend = "improving"
            elif recent_avg < older_avg - 0.5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        mood_distribution = {}
        for level in range(1, 6):
            count = mood_levels.count(level)
            mood_distribution[f"level_{level}"] = count

        week_ago = datetime.utcnow() - timedelta(days=7)

        def _get_ts(entry):
            ts = entry.timestamp
            if isinstance(ts, str):
                try:
                    return datetime.fromisoformat(ts.replace(' ', 'T'))
                except Exception:
                    return datetime.min
            return ts

        weekly_entries = [entry for entry in entries if _get_ts(entry) >= week_ago]
        weekly_average = (
            sum(entry.mood_level for entry in weekly_entries) / len(weekly_entries)
            if weekly_entries
            else 0
        )

        return jsonify(
            {
                "analytics": {
                    "average_mood": round(sum(mood_levels) / len(mood_levels), 2),
                    "mood_trend": trend,
                    "total_entries": len(entries),
                    "weekly_average": round(weekly_average, 2),
                    "mood_distribution": mood_distribution,
                    "recent_entries": len(recent_moods),
                }
            }
        )

    except Exception as e:
        current_app.logger.error(f"Mood analytics error: {e}")
        return jsonify({"error": "Failed to get mood analytics"}), 500
