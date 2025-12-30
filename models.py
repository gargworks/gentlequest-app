from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import os
from sqlalchemy.dialects.postgresql import JSONB

db = SQLAlchemy()


class UserSession(db.Model):
    __tablename__ = "user_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    conversation_count = db.Column(db.Integer, default=0)
    risk_level = db.Column(db.String(20), default="low")


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"))
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=False)  # True for user, False for AI
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    risk_level = db.Column(db.String(20), default="none")
    resources = db.Column(db.Text)  # JSON string for crisis resources


class ConversationLog(db.Model):
    __tablename__ = "conversation_logs"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"))
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    risk_level = db.Column(db.String(20), default="low")
    risk_score = db.Column(db.Float, default=0.0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class CrisisEvent(db.Model):
    __tablename__ = "crisis_events"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    risk_level = db.Column(db.String(20))
    intervention_taken = db.Column(db.String(100))
    escalated = db.Column(db.Boolean, default=False)


class SelfAssessmentEntry(db.Model):
    __tablename__ = "self_assessment_entries"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.String(36), db.ForeignKey("user_sessions.id"), nullable=False
    )
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    assessment_data = db.Column(JSONB, nullable=False)

    def __repr__(self):
        return f"<SelfAssessmentEntry id={self.id} session_id={self.session_id}>"


class MoodEntry(db.Model):
    __tablename__ = "mood_entries"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"))
    mood_level = db.Column(db.Integer, nullable=False)  # 1-5 scale
    note = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MoodEntry id={self.id} level={self.mood_level}>"


class AnalyticsEvent(db.Model):
    __tablename__ = "analytics_events"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"))
    event_type = db.Column(db.String(50), nullable=False)
    event_data = db.Column(JSONB)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AnalyticsEvent id={self.id} type={self.event_type}>"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"))

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


class CommunityPost(db.Model):
    __tablename__ = "community_posts"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"))
    content = db.Column(db.Text, nullable=False)
    is_anonymous = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<CommunityPost id={self.id}>"


class CommunityComment(db.Model):
    __tablename__ = "community_comments"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("community_posts.id"))
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"))
    content = db.Column(db.Text, nullable=False)
    is_anonymous = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CommunityComment id={self.id}>"


class ClinicalAssessment(db.Model):
    """Store PHQ-9 and GAD-7 clinical assessment results."""
    __tablename__ = "clinical_assessments"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"), nullable=False)
    assessment_type = db.Column(db.String(20), nullable=False)  # 'phq9' or 'gad7'
    responses = db.Column(JSONB, nullable=False)  # List of integer responses
    total_score = db.Column(db.Integer, nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # minimal, mild, moderate, severe
    requires_follow_up = db.Column(db.Boolean, default=False)  # For PHQ-9 Q9
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ClinicalAssessment id={self.id} type={self.assessment_type} score={self.total_score}>"

