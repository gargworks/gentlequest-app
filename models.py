from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import os
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

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
    assessment_data = db.Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)

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
    event_data = db.Column(JSON().with_variant(JSONB, "postgresql"))
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
    responses = db.Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)  # List of integer responses
    total_score = db.Column(db.Integer, nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # minimal, mild, moderate, severe
    requires_follow_up = db.Column(db.Boolean, default=False)  # For PHQ-9 Q9
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    assessment_metadata = db.Column(JSON().with_variant(JSONB, "postgresql"), default={})

    def __repr__(self):
        return f"<ClinicalAssessment id={self.id} type={self.assessment_type} score={self.total_score}>"


class Quest(db.Model):
    """Gamification mechanics: Quests for users to complete."""
    __tablename__ = "quests"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    quest_type = db.Column(db.String(20), nullable=False)  # task, tip, check_in, progress
    xp_reward = db.Column(db.Integer, default=10)
    difficulty = db.Column(db.Integer, default=1)
    week_number = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Quest id={self.id} title={self.title}>"


class QuestProgress(db.Model):
    """Tracking user progress on quests."""
    __tablename__ = "quest_progress"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"), nullable=False)
    quest_id = db.Column(db.Integer, db.ForeignKey("quests.id"), nullable=False)
    status = db.Column(db.String(20), default="available")  # available, in_progress, completed, expired
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    quest = db.relationship("Quest", backref="user_attempts")

    def __repr__(self):
        return f"<QuestProgress session={self.session_id} quest={self.quest_id} status={self.status}>"


class UserProfile(db.Model):
    """User gamification profile."""
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"), unique=True, nullable=False)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    streak_days = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.DateTime)
    badges = db.Column(db.String(500), default="")  # Comma-separated list
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserProfile session={self.session_id} xp={self.xp} level={self.level}>"


class Resource(db.Model):
    """Educational and crisis resources for users."""
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    url = db.Column(db.String(500))
    category = db.Column(db.String(50), nullable=False)  # crisis, self_help, university, external
    country = db.Column(db.String(10))
    university_id = db.Column(db.Integer)
    tags = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Resource id={self.id} title={self.title}>"


class UserResourceInteraction(db.Model):
    """Tracking user interactions with resources."""
    __tablename__ = "user_resource_interactions"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserResourceInteraction session={self.session_id} resource={self.resource_id}>"
