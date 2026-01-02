"""
IIP Module 6 - Database Models (SQLAlchemy)
Target: FastAPI + PostgreSQL Backend
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class Team(Base):
    """Team entity for Mod 6 project teams."""
    __tablename__ = "teams"
    
    team_id = Column(Integer, primary_key=True, index=True)
    team_name = Column(String(255), unique=True, index=True)
    project_focus = Column(String(255))  # e.g., "Mental Health Support for Students"
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = relationship("TeamMember", back_populates="team")
    pov_statements = relationship("POVStatement", back_populates="team")
    interviews = relationship("ResearchInterview", back_populates="team")
    personas = relationship("Persona", back_populates="team")
    cvp_canvas = relationship("CVPCanvas", back_populates="team")
    experiments = relationship("Experiment", back_populates="team")


class TeamMember(Base):
    """Team member entity."""
    __tablename__ = "team_members"
    
    member_id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(String(100))  # e.g., "Project Lead", "Research Lead"
    timezone = Column(String(100))
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    team = relationship("Team", back_populates="members")


class POVStatement(Base):
    """Point of View Statement for problem definition."""
    __tablename__ = "pov_statements"
    
    pov_id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    
    # POV Components
    users_description = Column(Text)  # "Who has the problem?"
    need_description = Column(Text)   # "What do they need?"
    why_matters_description = Column(Text)  # "Why does it matter?"
    full_statement = Column(Text)     # Complete: "[Users] need a way to [Need] because [Why]"
    
    # Metadata
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    feedback_from_instructors = Column(Text)
    iteration_count = Column(Integer, default=1)
    
    # Relationship
    team = relationship("Team", back_populates="pov_statements")


class ResearchInterview(Base):
    """Research interview record."""
    __tablename__ = "research_interviews"
    
    interview_id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    
    # Interview Details
    interview_date = Column(DateTime, nullable=False)
    participant_role = Column(String(100))  # e.g., "Student", "Counselor", "Parent"
    participant_anonymized_id = Column(String(100), index=True)  # For privacy
    location = Column(String(255))
    duration_minutes = Column(Integer)  # Interview duration
    
    # Content
    interview_notes = Column(Text, nullable=False)  # Raw transcript/notes
    recording_url = Column(String(500))  # Cloud storage link (optional)
    key_quotes = Column(JSON)  # Array of quoted strings from participant
    
    # Insights
    insights_extracted = Column(JSON)  # Array of ANRUM objects
    researcher_bias_notes = Column(Text)  # Reflection on researcher assumptions
    
    # Metadata
    created_date = Column(DateTime, default=datetime.utcnow)
    researcher_name = Column(String(255))
    
    # Relationship
    team = relationship("Team", back_populates="interviews")


class ANRUMInsight(Base):
    """
    ANRUM Insight object (Attitude, Need, Response, Use case, Mental model)
    Can be stored as JSON within ResearchInterview or as separate entity.
    """
    __tablename__ = "anrum_insights"
    
    insight_id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("research_interviews.interview_id"))
    
    attitude = Column(Text)  # What emotion/belief surfaced?
    need = Column(Text)      # What unmet need does this reveal?
    response = Column(Text)  # How did user currently respond?
    use_case = Column(Text)  # What specific scenario triggered this?
    mental_model = Column(Text)  # What assumption does user hold?
    
    created_date = Column(DateTime, default=datetime.utcnow)


class Persona(Base):
    """User persona developed from research."""
    __tablename__ = "personas"
    
    persona_id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    
    # Persona Identity
    name = Column(String(255), nullable=False)
    age = Column(Integer)
    context = Column(Text)  # Demographic, academic level, living situation
    avatar_url = Column(String(500))  # Profile image URL
    
    # Persona Attributes (stored as JSON for flexibility)
    goals = Column(JSON)  # Array of goal strings
    frustrations = Column(JSON)  # Array of frustration strings
    behaviors = Column(JSON)  # Array of behavior descriptions
    motivations = Column(JSON)  # Array of motivation strings
    barriers = Column(JSON)  # Array of barrier strings
    
    environment = Column(Text)  # School, dorm, home, support network
    
    # Supporting Research
    supporting_interview_ids = Column(JSON)  # Array of interview_ids that informed this persona
    supporting_quotes = Column(JSON)  # Key quotes from interviews
    
    # Metadata
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)
    
    # Relationship
    team = relationship("Team", back_populates="personas")


class CVPCanvas(Base):
    """Customer Value Proposition Canvas."""
    __tablename__ = "cvp_canvas"
    
    cvp_id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False, unique=True)
    
    # Customer Segment
    customer_segment = Column(Text)
    
    # Jobs to be Done (JTBD)
    jobs_to_be_done = Column(JSON)  # Array of job descriptions (functional, emotional, social)
    
    # Value Proposition
    value_proposition = Column(Text)
    
    # Customer Pain Points
    pains = Column(JSON)  # Array of pain descriptions
    pain_relievers = Column(JSON)  # Array of how solution eases pains
    
    # Customer Gains
    gains = Column(JSON)  # Array of desired benefits
    gain_creators = Column(JSON)  # Array of how solution enables gains
    
    # Competitive Analysis
    competitive_positioning = Column(Text)
    direct_competitors = Column(JSON)  # Array of competitor names
    indirect_competitors = Column(JSON)  # Array of alternative solutions
    differentiation = Column(Text)  # How you stand out
    
    # Trade-offs
    trade_offs = Column(JSON)  # Array of design trade-off decisions
    
    # Metadata
    created_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)
    
    # Relationship
    team = relationship("Team", back_populates="cvp_canvas")


class ExperimentStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Experiment(Base):
    """Hypothesis-driven experiment for validation."""
    __tablename__ = "experiments"
    
    exp_id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    
    # Hypothesis Definition
    hypothesis = Column(Text, nullable=False)  # e.g., "Students will use AI check-ins if anonymous"
    assumption = Column(Text)  # Core assumption being tested
    
    # Test Design
    test_method = Column(String(255))  # e.g., "A/B Test", "User Interview", "Prototype Test"
    test_description = Column(Text)
    
    # Success Criteria
    success_metric = Column(Text)  # e.g., ": 