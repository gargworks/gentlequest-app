import pytest
from app import create_app
from models import db, Quest, UserProfile, UserSession
from providers.quest_generator import QuestGenerator

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_quest_generation(app):
    """Test that quests are generated correctly."""
    with app.app_context():
        # Generate quests for Week 1, Year 2026
        quests = QuestGenerator.generate_weekly_quests(week=1, year=2026)
        
        assert len(quests) == 5
        assert len([q for q in quests if q['type'] == 'task']) == 2
        assert len([q for q in quests if q['type'] == 'tip']) == 1
        assert len([q for q in quests if q['type'] == 'check_in']) == 1
        assert len([q for q in quests if q['type'] == 'progress']) == 1

def test_quest_api_flow(client, app):
    """Test the full API flow: Get Quests -> Complete Quest -> Verify Profile."""
    session_id = "test_session_gamer"

    # Ensure session exists for FK-backed profile
    with app.app_context():
        if not UserSession.query.get(session_id):
            db.session.add(UserSession(id=session_id))
            db.session.commit()

    # 1. Get Quests (should auto-generate)
    resp = client.get(f'/api/quests?session_id={session_id}')
    assert resp.status_code == 200
    data = resp.json
    
    assert len(data['quests']) == 5
    assert data['profile']['level'] == 1
    assert data['profile']['xp'] == 0
    
    # Pick the first quest
    quest_id = data['quests'][0]['id']
    quest_xp = data['quests'][0]['xp_reward']
    
    # 2. Complete Quest
    resp = client.post(f'/api/quests/{quest_id}/complete', json={
        "session_id": session_id
    })
    assert resp.status_code == 200
    result = resp.json
    
    assert result['success'] is True
    assert result['xp_earned'] == quest_xp
    assert result['new_total_xp'] == quest_xp
    
    # 3. Verify Persistence
    resp = client.get(f'/api/quests?session_id={session_id}')
    data = resp.json
    
    completed_quest = next(q for q in data['quests'] if q['id'] == quest_id)
    assert completed_quest['status'] == 'completed'
    assert data['profile']['xp'] == quest_xp

def test_level_up_logic(client, app):
    """Test that leveling up works correctly."""
    session_id = "test_session_leveler"

    # Generate Quests manually to control XP
    with app.app_context():
        if not UserSession.query.get(session_id):
            db.session.add(UserSession(id=session_id))
            db.session.flush()
        q1 = Quest(title="Big Quest", description="D", quest_type="task", xp_reward=150, difficulty=1, week_number=1, year=2026)
        db.session.add(q1)
        db.session.commit()
        quest_id = q1.id
        
        # User starts at 0 XP
        profile = UserProfile(session_id=session_id)
        db.session.add(profile)
        db.session.commit()

    # Complete Big Quest (150 XP should be Level 2 since Level = 1 + XP // 100)
    resp = client.post(f'/api/quests/{quest_id}/complete', json={
        "session_id": session_id
    })
    
    result = resp.json
    assert result['leveled_up'] is True
    assert result['new_level'] == 2
    assert result['new_total_xp'] == 150
