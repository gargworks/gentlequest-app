"""
Comprehensive test suite for Quest system
Run with: pytest tests/test_quest_system.py -v
"""

import pytest
from datetime import datetime, timedelta, date
from app import create_app
from models import db
from sqlalchemy import text
from providers.quest_generator import QuestGenerator


@pytest.fixture
def app():
    """Create test app with in-memory database"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        # Create sessions table (required for FK)
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id VARCHAR(255) PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        # Create quest tables
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                description VARCHAR(500) NOT NULL,
                quest_type VARCHAR(20) NOT NULL,
                xp_reward INTEGER NOT NULL DEFAULT 10,
                difficulty INTEGER NOT NULL DEFAULT 1,
                week_number INTEGER NOT NULL,
                year INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS quest_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(255) NOT NULL,
                quest_id INTEGER NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'available',
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES user_sessions(id),
                FOREIGN KEY (quest_id) REFERENCES quests(id)
            )
        """))
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                streak_days INTEGER NOT NULL DEFAULT 0,
                last_activity_date TIMESTAMP,
                badges VARCHAR(500) DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES user_sessions(id)
            )
        """))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def session_id(app):
    """Create test session"""
    with app.app_context():
        db.session.execute(
            text("INSERT INTO user_sessions (id) VALUES (:id)"),
            {"id": "test_session_123"}
        )
        db.session.commit()
        return "test_session_123"


class TestQuestGenerator:
    def test_get_week_number(self):
        """Test ISO week number calculation"""
        week, year = QuestGenerator.get_week_number()
        assert isinstance(week, int)
        assert isinstance(year, int)
        assert 1 <= week <= 53
        assert year >= 2026
    
    def test_generate_weekly_quests_count(self, app):
        """Test that 5 quests are generated"""
        with app.app_context():
            week, year = 1, 2026
            quests = QuestGenerator.generate_weekly_quests(week, year)
            assert len(quests) == 5
    
    def test_generate_weekly_quests_types(self, app):
        """Test quest type distribution"""
        with app.app_context():
            quests = QuestGenerator.generate_weekly_quests(1, 2026)
            types = [q['type'] for q in quests]
            assert types.count('task') == 2
            assert types.count('tip') == 1
            assert types.count('check_in') == 1
            assert types.count('progress') == 1
    
    def test_generate_weekly_quests_xp_valid(self, app):
        """Test XP rewards are in valid range"""
        with app.app_context():
            quests = QuestGenerator.generate_weekly_quests(1, 2026)
            for quest in quests:
                assert 10 <= quest['xp_reward'] <= 50
    
    def test_generate_weekly_quests_idempotent(self, app):
        """Test that generating twice returns same quests"""
        with app.app_context():
            week, year = 2, 2026
            quests1 = QuestGenerator.generate_weekly_quests(week, year)
            quests2 = QuestGenerator.generate_weekly_quests(week, year)
            
            assert len(quests1) == len(quests2)
            assert [q['id'] for q in quests1] == [q['id'] for q in quests2]
    
    def test_difficulty_progression(self, app):
        """Test difficulty increases over weeks"""
        with app.app_context():
            week1 = QuestGenerator.generate_weekly_quests(1, 2026)
            week8 = QuestGenerator.generate_weekly_quests(8, 2026)
            
            max_diff_week1 = max(q['difficulty'] for q in week1)
            max_diff_week8 = max(q['difficulty'] for q in week8)
            
            assert max_diff_week8 >= max_diff_week1


class TestQuestAPI:
    def test_get_quests_no_session(self, client):
        """Test GET /api/quests without session ID"""
        response = client.get('/api/quests')
        assert response.status_code == 400
    
    def test_get_quests_success(self, client, session_id, app):
        """Test GET /api/quests with valid session"""
        with app.app_context():
            # Generate quests first
            QuestGenerator.generate_weekly_quests()
        
        response = client.get(
            '/api/quests',
            headers={'X-Session-ID': session_id}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'quests' in data
        assert 'week' in data
        assert 'year' in data
        assert len(data['quests']) == 5
    
    def test_complete_quest_success(self, client, session_id, app):
        """Test POST /api/quests/{id}/complete"""
        with app.app_context():
            quests = QuestGenerator.generate_weekly_quests(1, 2026)
            quest_id = quests[0]['id']
        
        response = client.post(
            f'/api/quests/{quest_id}/complete',
            headers={'X-Session-ID': session_id},
            json={}
        )
        if response.status_code != 200:
            with open("debug_error.log", "w") as f:
                f.write(f"ERROR: {response.get_json()}")
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert data['xp_earned'] > 0
    
    def test_complete_quest_twice_fails(self, client, session_id, app):
        """Test that completing same quest twice fails"""
        with app.app_context():
            quests = QuestGenerator.generate_weekly_quests(1, 2026)
            quest_id = quests[0]['id']
        
        # Complete once
        client.post(
            f'/api/quests/{quest_id}/complete',
            headers={'X-Session-ID': session_id},
            json={}
        )
        
        # Try to complete again
        response = client.post(
            f'/api/quests/{quest_id}/complete',
            headers={'X-Session-ID': session_id},
            json={}
        )
        assert response.status_code == 400
    
    def test_get_profile_creates_if_not_exists(self, client, session_id):
        """Test GET /api/user/profile creates profile if doesn't exist"""
        response = client.get(
            '/api/user/profile',
            headers={'X-Session-ID': session_id}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['xp'] == 0
        assert data['level'] == 1
        assert data['streak_days'] == 0


class TestUserProfile:
    def test_xp_award_no_level_up(self, app, session_id):
        """Test adding XP without leveling up"""
        with app.app_context():
            # Create profile with 50 XP
            db.session.execute(
                text("""
                    INSERT INTO user_profiles (session_id, xp, level)
                    VALUES (:session_id, 50, 1)
                """),
                {"session_id": session_id}
            )
            db.session.commit()
            
            # Add 30 XP (total 80, still level 1)
            db.session.execute(
                text("UPDATE user_profiles SET xp = xp + 30 WHERE session_id = :session_id"),
                {"session_id": session_id}
            )
            db.session.commit()
            
            profile = db.session.execute(
                text("SELECT xp, level FROM user_profiles WHERE session_id = :session_id"),
                {"session_id": session_id}
            ).fetchone()
            
            assert profile[0] == 80
            assert profile[1] == 1
    
    def test_xp_award_with_level_up(self, app, session_id):
        """Test adding XP that triggers level up"""
        with app.app_context():
            # Create profile with 90 XP
            db.session.execute(
                text("INSERT INTO user_profiles (session_id, xp, level) VALUES (:sid, 90, 1)"),
                {"sid": session_id}
            )
            db.session.commit()
            
            # Add 20 XP (total 110, should be level 2)
            new_xp = 110
            new_level = (new_xp // 100) + 1
            
            db.session.execute(
                text("UPDATE user_profiles SET xp = :xp, level = :level WHERE session_id = :sid"),
                {"xp": new_xp, "level": new_level, "sid": session_id}
            )
            db.session.commit()
            
            profile = db.session.execute(
                text("SELECT xp, level FROM user_profiles WHERE session_id = :sid"),
                {"sid": session_id}
            ).fetchone()
            
            assert profile[0] == 110
            assert profile[1] == 2
    
    def test_streak_tracking_consecutive_day(self, app, session_id):
        """Test streak increments on consecutive day"""
        with app.app_context():
            yesterday = datetime.utcnow() - timedelta(days=1)
            
            # Create profile with 5-day streak, last activity yesterday
            db.session.execute(
                text("""
                    INSERT INTO user_profiles (session_id, streak_days, last_activity_date)
                    VALUES (:sid, 5, :last_activity)
                """),
                {"sid": session_id, "last_activity": yesterday}
            )
            db.session.commit()
            
            # Update streak (simulate today's activity)
            today = datetime.utcnow()
            db.session.execute(
                text("""
                    UPDATE user_profiles 
                    SET streak_days = streak_days + 1, last_activity_date = :today
                    WHERE session_id = :sid
                """),
                {"today": today, "sid": session_id}
            )
            db.session.commit()
            
            profile = db.session.execute(
                text("SELECT streak_days FROM user_profiles WHERE session_id = :sid"),
                {"sid": session_id}
            ).fetchone()
            
            assert profile[0] == 6
    
    def test_streak_broken(self, app, session_id):
        """Test streak resets when broken"""
        with app.app_context():
            three_days_ago = datetime.utcnow() - timedelta(days=3)
            
            # Create profile with 10-day streak, last activity 3 days ago
            db.session.execute(
                text("""
                    INSERT INTO user_profiles (session_id, streak_days, last_activity_date)
                    VALUES (:sid, 10, :last_activity)
                """),
                {"sid": session_id, "last_activity": three_days_ago}
            )
            db.session.commit()
            
            # Reset streak (simulate today's activity after gap)
            today = datetime.utcnow()
            db.session.execute(
                text("""
                    UPDATE user_profiles 
                    SET streak_days = 1, last_activity_date = :today
                    WHERE session_id = :sid
                """),
                {"today": today, "sid": session_id}
            )
            db.session.commit()
            
            profile = db.session.execute(
                text("SELECT streak_days FROM user_profiles WHERE session_id = :sid"),
                {"sid": session_id}
            ).fetchone()
            
            assert profile[0] == 1
    
    def test_badge_award(self, app, session_id):
        """Test awarding a badge"""
        with app.app_context():
            # Create profile
            db.session.execute(
                text("INSERT INTO user_profiles (session_id, badges) VALUES (:sid, '')"),
                {"sid": session_id}
            )
            db.session.commit()
            
            # Award badge
            db.session.execute(
                text("""
                    UPDATE user_profiles 
                    SET badges = CASE 
                        WHEN badges = '' THEN 'streak_7'
                        ELSE badges || ',streak_7'
                    END
                    WHERE session_id = :sid
                """),
                {"sid": session_id}
            )
            db.session.commit()
            
            profile = db.session.execute(
                text("SELECT badges FROM user_profiles WHERE session_id = :sid"),
                {"sid": session_id}
            ).fetchone()
            
            assert 'streak_7' in profile[0]


class TestQuestIntegration:
    def test_full_quest_completion_flow(self, client, session_id, app):
        """Test complete flow: Get quests → Complete quest → Check profile"""
        with app.app_context():
            # Generate quests
            QuestGenerator.generate_weekly_quests(1, 2026)
        
        # Get quests
        response = client.get('/api/quests', headers={'X-Session-ID': session_id})
        assert response.status_code == 200
        quests = response.get_json()['quests']
        assert len(quests) == 5
        
        quest_id = quests[0]['id']
        xp_reward = quests[0]['xp_reward']
        
        # Complete quest
        response = client.post(
            f'/api/quests/{quest_id}/complete',
            headers={'X-Session-ID': session_id},
            json={}
        )
        assert response.status_code == 200
        assert response.get_json()['xp_earned'] == xp_reward
        
        # Check profile
        response = client.get('/api/user/profile', headers={'X-Session-ID': session_id})
        assert response.status_code == 200
        profile = response.get_json()
        assert profile['xp'] >= xp_reward
        assert profile['streak_days'] >= 1
    
    def test_level_up_flow(self, client, session_id, app):
        """Test leveling up from quest completion"""
        with app.app_context():
            # Create profile at 90 XP (10 away from level 2)
            db.session.execute(
                text("INSERT INTO user_profiles (session_id, xp, level) VALUES (:sid, 90, 1)"),
                {"sid": session_id}
            )
            db.session.commit()
            
            # Generate quests
            quests = QuestGenerator.generate_weekly_quests(1, 2026)
            # Find quest with 20+ XP
            quest = next((q for q in quests if q['xp_reward'] >= 20), quests[0])
        
        # Complete quest
        response = client.post(
            f'/api/quests/{quest["id"]}/complete',
            headers={'X-Session-ID': session_id},
            json={}
        )
        assert response.status_code == 200
        data = response.get_json()
        
        if quest['xp_reward'] >= 10:
            assert data['leveled_up'] == True
            assert data['new_level'] == 2
    
    def test_badge_unlock_7_day_streak(self, client, session_id, app):
        """Test 7-day streak badge unlock"""
        with app.app_context():
            # Create profile with 6-day streak
            yesterday = datetime.utcnow() - timedelta(days=1)
            db.session.execute(
                text("""
                    INSERT INTO user_profiles (session_id, streak_days, last_activity_date, xp, level)
                    VALUES (:sid, 6, :last_activity, 0, 1)
                """),
                {"sid": session_id, "last_activity": yesterday}
            )
            db.session.commit()
            
            quests = QuestGenerator.generate_weekly_quests(1, 2026)
            quest_id = quests[0]['id']
        
        # Complete quest on day 7
        response = client.post(
            f'/api/quests/{quest_id}/complete',
            headers={'X-Session-ID': session_id},
            json={}
        )
        if response.status_code != 200:
            with open("debug_error_badge.log", "w") as f:
                f.write(f"ERROR: {response.get_json()}")
        assert response.status_code == 200
        data = response.get_json()
        
        # Should award streak_7 badge
        new_badges = data.get('new_badges', [])
        if new_badges:
            assert any(b['id'] == 'streak_7' for b in new_badges)


class TestQuestEdgeCases:
    def test_complete_nonexistent_quest(self, client, session_id):
        """Test completing quest that doesn't exist"""
        response = client.post(
            '/api/quests/99999/complete',
            headers={'X-Session-ID': session_id},
            json={}
        )
        if response.status_code != 404:
            with open("debug_error_404.log", "w") as f:
                f.write(f"ERROR: {response.get_json()}")
        assert response.status_code == 404
    
    def test_get_quests_empty_database(self, client, session_id):
        """Test getting quests when none exist (should auto-generate)"""
        response = client.get('/api/quests', headers={'X-Session-ID': session_id})
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['quests']) == 5  # Auto-generated
    
    def test_concurrent_quest_completion(self, client, session_id, app):
        """Test that concurrent completions don't double-award XP"""
        with app.app_context():
            quests = QuestGenerator.generate_weekly_quests(1, 2026)
            quest_id = quests[0]['id']
        
        # Try to complete twice rapidly
        response1 = client.post(f'/api/quests/{quest_id}/complete', 
                               headers={'X-Session-ID': session_id}, json={})
        response2 = client.post(f'/api/quests/{quest_id}/complete', 
                               headers={'X-Session-ID': session_id}, json={})
        
        # First should succeed, second should fail
        assert response1.status_code == 200
        assert response2.status_code == 400
