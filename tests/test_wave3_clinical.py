import pytest
from app import app
from models import db, UserProfile, MoodEntry, ClinicalAssessment, QuestProgress, UserSession, Quest
from datetime import datetime

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


def test_clinical_summary(client):
    # Seed data
    with app.app_context():
        # User session
        sid = "test-session-summary"
        session = UserSession(id=sid, last_active=datetime.utcnow())
        db.session.add(session)
        db.session.flush()
        
        # Profile
        profile = UserProfile(session_id=sid, xp=100, level=2)
        db.session.add(profile)
        
        # Mood
        mood = MoodEntry(session_id=sid, mood_level=4, timestamp=datetime.utcnow())
        db.session.add(mood)
        
        db.session.commit()

    response = client.get('/api/clinical/summary')
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_enrollments'] == 1
    assert data['active_users_24h'] == 1
    assert data['average_mood_7d'] == 4.0

def test_clinical_triage(client):
    # Seed data
    with app.app_context():
        sid = "test-session-triage"
        # Ensure session exists for FK
        session = UserSession(id=sid, last_active=datetime.utcnow())
        db.session.add(session)
        db.session.flush()
        # High priority assessment
        assessment = ClinicalAssessment(
            session_id=sid,
            assessment_type="phq9",
            responses=[3, 3, 3, 3, 3, 3, 3, 3, 3], # Score 27
            total_score=27,
            severity="Severe",
            requires_follow_up=True,
            timestamp=datetime.utcnow()
        )
        db.session.add(assessment)
        db.session.commit()

    response = client.get('/api/clinical/triage')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['triage_cases']) == 1
    assert data['triage_cases'][0]['total_score'] == 27
    assert data['triage_cases'][0]['requires_follow_up'] is True

def test_clinical_engagement(client):
    # Seed data
    with app.app_context():
        sid = "test-session-engagement"
        # Ensure session exists for FK
        session = UserSession(id=sid, last_active=datetime.utcnow())
        db.session.add(session)
        db.session.flush()
        profile = UserProfile(session_id=sid, updated_at=datetime.utcnow())
        db.session.add(profile)
        
        # Seed quest to satisfy FK
        quest = Quest(title="Engagement Quest", description="D", quest_type="task", xp_reward=10, difficulty=1, week_number=1, year=2026)
        db.session.add(quest)
        db.session.flush()
        
        progress = QuestProgress(
            session_id=sid,
            quest_id=quest.id,
            status="completed",
            completed_at=datetime.utcnow()
        )
        db.session.add(progress)
        db.session.commit()

    response = client.get('/api/clinical/engagement')
    assert response.status_code == 200
    data = response.get_json()
    assert data['completed_quests_7d'] == 1
    assert data['active_users_7d'] == 1
    assert data['avg_quests_per_user'] == 1.0

def test_clinical_dashboard_route(client):
    response = client.get('/clinical')
    # If 404, the route might be misconfigured or requires template rendering which fails
    if response.status_code != 200:
        print(f"Failed Route data: {response.data}")
    assert response.status_code == 200
    assert b"GentleQuest | Clinical Dashboard" in response.data

