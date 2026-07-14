from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy import text

db = SQLAlchemy()


class UserSession(db.Model):
    __tablename__ = "user_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    conversation_count = db.Column(db.Integer, default=0)
    risk_level = db.Column(db.String(20), default="low")


class University(db.Model):
    """University profile and customization settings."""
    __tablename__ = "universities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    domain = db.Column(db.String(100))
    caps_email = db.Column(db.String(255))
    caps_phone = db.Column(db.String(50))
    caps_hours = db.Column(db.String(200))
    waitlist_weeks = db.Column(db.Integer)
    enrollment = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Branding
    logo_url = db.Column(db.String(500))
    primary_color = db.Column(db.String(7))
    secondary_color = db.Column(db.String(7))
    welcome_message = db.Column(db.Text)

    # Integration
    sso_enabled = db.Column(db.Boolean, server_default=text('false'), default=False)
    sso_provider = db.Column(db.String(50))
    sso_config = db.Column(JSON().with_variant(JSONB, "postgresql"))
    lms_integration = db.Column(db.String(50))
    custom_domain = db.Column(db.String(100))
    
    # Outreach
    outreach_status = db.Column(db.String(50), default="pending")  # pending, drafted, sent, replied
    contact_email = db.Column(db.String(255))  # Specific contact derived from script

    def __repr__(self):
        return f"<University id={self.id} name={self.name}>"


class UniversityCounselor(db.Model):
    """Counselor contact points for university-specific alerts."""
    __tablename__ = "university_counselors"

    id = db.Column(db.Integer, primary_key=True)
    university_id = db.Column(db.Integer, db.ForeignKey("universities.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    role = db.Column(db.String(100))
    alert_methods = db.Column(db.String(200), default="email")  # comma-separated: email,sms
    is_active = db.Column(db.Boolean, server_default=text('false'), default=False)
    receives_alerts = db.Column(db.Boolean, server_default=text('true'), default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    university = db.relationship("University", backref="counselors")

    def __repr__(self):
        return f"<UniversityCounselor id={self.id} name={self.name} uni={self.university_id}>"


class Message(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"), index=True)
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=False)  # True for user, False for AI
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    risk_level = db.Column(db.String(20), default="none")
    resources = db.Column(db.Text)  # JSON string for crisis resources
    message_type = db.Column(db.String(50), default="text")


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
    __tablename__ = "crisis_detections"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"))
    message = db.Column(db.Text)
    risk_level = db.Column(db.String(50))
    risk_score = db.Column(db.Float, default=0.0)
    keywords = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
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
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"), index=True)
    mood_level = db.Column(db.Integer, nullable=False)  # 1-5 scale
    note = db.Column(db.Text)
    context_chips = db.Column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        server_default='[]',
    )
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MoodEntry id={self.id} level={self.mood_level}>"


class JournalEntry(db.Model):
    __tablename__ = "journal_entries"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"), nullable=False, index=True)
    title = db.Column(db.Text)
    body = db.Column(db.Text, nullable=False)
    mood_tag = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = db.Column(db.DateTime)

    def __repr__(self):
        return f"<JournalEntry id={self.id} session_id={self.session_id}>"

class AnalyticsEvent(db.Model):
    __tablename__ = "analytics_events"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"))
    event_type = db.Column(db.String(50), nullable=False)
    event_metadata = db.Column('metadata', JSON().with_variant(JSONB, "postgresql"))
    request_id = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AnalyticsEvent id={self.id} type={self.event_type}>"


class InterventionOutcome(db.Model):
    __tablename__ = "intervention_outcomes"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), db.ForeignKey("user_sessions.id"), nullable=False, index=True)
    intervention_id = db.Column(db.String(100), nullable=False)
    issue = db.Column(db.String(50), index=True)
    offer_stage = db.Column(db.Integer, default=1)
    outcome = db.Column(db.String(20), default='offered')
    completed = db.Column(db.Boolean, default=False, nullable=False)
    effectiveness_rating = db.Column(db.Float)
    feedback = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    exercise_type = db.Column(db.String(50), index=True)
    time_spent_seconds = db.Column(db.Integer)
    mood_before = db.Column(db.Integer)
    mood_after = db.Column(db.Integer)

    def __repr__(self):
        return f"<InterventionOutcome id={self.id} session={self.session_id}>"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"))
    anonymity_mode = db.Column(db.Boolean, nullable=False, server_default=text('false'), default=False)
    notification_prefs = db.Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, server_default='{}', default=dict)
    deleted_at = db.Column(db.DateTime)

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


class AuthToken(db.Model):
    """One-time passwordless magic-link token.

    Flow:
      1. POST /api/auth/magic-link {email} → creates a row with
         token_hash + expires_at + email, emails (or logs in dev) the
         raw token via gentlequest://auth/verify?token=<raw>.
      2. POST /api/auth/verify {token} → looks up by token_hash, marks
         used_at, returns the user_id + session_id. Future requests
         carry X-Session-ID to identify the user across devices.

    Token expires in 15 minutes. Single-use (used_at sentinel).
    Stored as SHA-256 hash; raw token never persisted on the server.
    """

    __tablename__ = "auth_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    email = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)

    def __repr__(self):
        return f"<AuthToken id={self.id} user_id={self.user_id} used={self.used_at is not None}>"


class CommunityPost(db.Model):
    __tablename__ = "community_posts"

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(64))
    body_redacted = db.Column(db.Text, nullable=False)
    is_curated = db.Column(db.Boolean, default=True)
    is_hidden = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reactions_relate = db.Column(db.Integer, default=0)
    reactions_helped = db.Column(db.Integer, default=0)
    reactions_strength = db.Column(db.Integer, default=0)
    author_hash = db.Column(db.String(64))

    def __repr__(self):
        return f"<CommunityPost id={self.id}>"
#
#
# class CommunityComment(db.Model):
#     __tablename__ = "community_comments"
#
#     id = db.Column(db.Integer, primary_key=True)
#     post_id = db.Column(db.Integer, db.ForeignKey("community_posts.id"))
#     session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"))
#     content = db.Column(db.Text, nullable=False)
#     is_anonymous = db.Column(db.Boolean, default=True)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#
#     def __repr__(self):
#         return f"<CommunityComment id={self.id}>"


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
    target = db.Column(db.Integer, default=1)  # Target value for progress (e.g. 10 minutes)
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
    university_id = db.Column(db.Integer, db.ForeignKey("universities.id"), nullable=True)
    tags = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, server_default=text('false'), default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    university = db.relationship("University", backref="resources")

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


class CounselorAlert(db.Model):
    """Alerts sent to university counselors regarding student crisis messages."""
    __tablename__ = "counselor_alerts"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"))
    university_id = db.Column(db.Integer, db.ForeignKey("universities.id"))
    severity = db.Column(db.String(20), nullable=False)
    trigger_message = db.Column(db.Text, nullable=False)
    conversation_excerpt = db.Column(db.Text)
    risk_keywords = db.Column(db.String(500))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledged_at = db.Column(db.DateTime)
    acknowledged_by = db.Column(db.String(255))
    email_sent = db.Column(db.Boolean, server_default=text('false'), default=False)
    sms_sent = db.Column(db.Boolean, server_default=text('false'), default=False)
    # Phase H: triage state machine (new -> acknowledged -> resolved | escalated)
    triage_state = db.Column(db.String(20), default="new", server_default=text("'new'"))

    def __repr__(self):
        return f"<CounselorAlert id={self.id} severity={self.severity} session={self.session_id}>"


class AlertAcknowledgment(db.Model):
    """History of counselor actions taken on a specific alert."""
    __tablename__ = "alert_acknowledgments"

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey("counselor_alerts.id"))
    counselor_id = db.Column(db.String(255), nullable=False)
    response_notes = db.Column(db.Text)
    action_taken = db.Column(db.String(500))
    responded_at = db.Column(db.DateTime, default=datetime.utcnow)

    alert = db.relationship("CounselorAlert", backref="acknowledgments")

    def __repr__(self):
        return f"<AlertAcknowledgment alert_id={self.alert_id} by={self.counselor_id}>"


class CrisisEscalation(db.Model):
    """Phase I: escalation events triggered by the 'I need help now' button."""
    __tablename__ = "crisis_escalations"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False, index=True)
    country_code = db.Column(db.String(5))
    channel = db.Column(db.String(20), nullable=False)   # sms, call, banner_only
    status = db.Column(db.String(20), default="initiated")  # initiated, sent, failed, checked_in
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    check_in_at = db.Column(db.DateTime)
    check_in_sent = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<CrisisEscalation id={self.id} session={self.session_id} channel={self.channel}>"


class UserResourcePref(db.Model):
    __tablename__ = "user_resource_prefs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"), nullable=False, index=True)
    resource_id = db.Column(db.Text, nullable=False)
    is_favorite = db.Column(db.Boolean, default=False, server_default=text('false'), nullable=False)
    last_opened_at = db.Column(db.DateTime)

    __table_args__ = (db.UniqueConstraint("session_id", "resource_id", name="uq_user_resource_prefs_session_resource"),)

    def __repr__(self):
        return f"<UserResourcePref session_id={self.session_id} resource_id={self.resource_id}>"


class PushToken(db.Model):
    __tablename__ = "push_tokens"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey("user_sessions.id"), nullable=False, index=True)
    token = db.Column(db.Text, nullable=False)
    platform = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = db.Column(db.DateTime)

    __table_args__ = (db.UniqueConstraint("session_id", "token", name="uq_push_tokens_session_token"),)

    def __repr__(self):
        return f"<PushToken session_id={self.session_id} platform={self.platform}>"

class BrainState(db.Model):
    """Singleton model for database-backed brain state."""
    __tablename__ = "brain_state"

    id = db.Column(db.Integer, primary_key=True, default=1)
    state_data = db.Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BrainState last_updated={self.last_updated}>"


class UserFeedback(db.Model):
    """In-app feedback from the feedback widget (ADR-005 criterion iii — human voice)."""
    __tablename__ = "user_feedback"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), nullable=True, index=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    feedback_text = db.Column(db.Text)
    feedback_trigger = db.Column("trigger", db.String(50), default="after_3rd_checkin")  # 'trigger' is reserved in PG
    country = db.Column(db.String(10))
    app_version = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<UserFeedback id={self.id} rating={self.rating}>"


class BrainEvent(db.Model):
    """Event log for brain activities."""
    __tablename__ = "brain_events"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(36), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    emitter = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), default="NOTABLE")
    payload = db.Column(JSON().with_variant(JSONB, "postgresql"))
    event_metadata = db.Column('metadata', JSON().with_variant(JSONB, "postgresql"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<BrainEvent type={self.event_type} emitter={self.emitter}>"
