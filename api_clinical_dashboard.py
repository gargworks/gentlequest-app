from flask import Blueprint, jsonify, request
import os
from models import db, UserProfile, MoodEntry, ClinicalAssessment, QuestProgress, UserSession
from sqlalchemy import func
from datetime import datetime, timedelta
from extensions import limiter

clinical_dashboard = Blueprint('clinical_dashboard', __name__)

# Helper to check for admin (Mock for now, replace with real auth later)
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for simple API key header or session
        # This is a basic implementation for the MVP
        import secrets as _secrets
        auth_header = request.headers.get("X-Admin-Token") or ""
        admin_token = os.environ.get("ADMIN_TOKEN", "")
        if not admin_token or not _secrets.compare_digest(auth_header, admin_token):
             # Allow local debug bypass
             if request.remote_addr != "127.0.0.1":
                 return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

@clinical_dashboard.route('/api/clinical/summary', methods=['GET'])
@limiter.limit("10 per minute")
@admin_required
def get_summary():
    """Returns high-level stats for the university mental health dashboard."""
    try:
        # Total enrollments (UserProfiles)
        total_enrollments = UserProfile.query.count()
        
        # Active users in last 24h
        last_24h = datetime.utcnow() - timedelta(hours=24)
        active_users = UserSession.query.filter(UserSession.last_active >= last_24h).count()
        
        # Average mood in last 7 days
        last_7d = datetime.utcnow() - timedelta(days=7)
        avg_mood = db.session.query(func.avg(MoodEntry.mood_level)).filter(MoodEntry.timestamp >= last_7d).scalar()
        
        return jsonify({
            "total_enrollments": total_enrollments,
            "active_users_24h": active_users,
            "average_mood_7d": round(float(avg_mood or 0), 2),
            "status": "stable",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@clinical_dashboard.route('/api/clinical/triage', methods=['GET'])
@limiter.limit("10 per minute")
@admin_required
def get_triage():
    """Returns high-priority triage cases (PHQ-9 Q9 > 0 or Total Score >= 10)."""
    try:
        # High-priority cases: PHQ-9 Q9 > 0 or Score 10+
        high_priority = ClinicalAssessment.query.filter(
            (ClinicalAssessment.requires_follow_up == True) | 
            (ClinicalAssessment.total_score >= 10)
        ).order_by(ClinicalAssessment.timestamp.desc()).limit(50).all()
        
        triage_list = []
        for case in high_priority:
            triage_list.append({
                "id": case.id,
                "session_id": case.session_id,
                "assessment_type": case.assessment_type.upper(),
                "total_score": case.total_score,
                "severity": case.severity,
                "requires_follow_up": case.requires_follow_up,
                "timestamp": case.timestamp.isoformat()
            })
        
        return jsonify({"triage_cases": triage_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@clinical_dashboard.route('/api/clinical/engagement', methods=['GET'])
@limiter.limit("10 per minute")
@admin_required
def get_engagement():
    """Returns quest completion rates for the last 7 days."""
    try:
        # Quest completion rate over last 7 days
        last_7d = datetime.utcnow() - timedelta(days=7)
        
        # We look at all QuestProgress entries updated/created in the last 7 days
        # completed_at is the most reliable timestamp for engagement
        completed_quests = QuestProgress.query.filter(
            QuestProgress.completed_at >= last_7d, 
            QuestProgress.status == 'completed'
        ).count()
        
        total_active_profiles = UserProfile.query.filter(UserProfile.updated_at >= last_7d).count()
        
        # Metric: Average quests completed per active user
        quests_per_user = (completed_quests / total_active_profiles) if total_active_profiles > 0 else 0
        
        return jsonify({
            "completed_quests_7d": completed_quests,
            "active_users_7d": total_active_profiles,
            "avg_quests_per_user": round(quests_per_user, 2),
            "status": "healthy"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
