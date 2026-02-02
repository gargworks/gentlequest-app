"""
Complete Integration Test Suite
Tests all API endpoints end-to-end
"""

import os
import pytest
from datetime import datetime
from app import create_app
from models import db, UserSession

@pytest.fixture
def app():
    os.environ["PYTEST_CURRENT_TEST"] = "true"
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['RATE_LIMIT_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def session_id(app):
    with app.app_context():
        # Ensure session exists (compatible with Postgres)
        session = UserSession.query.get("test_session")
        if not session:
            session = UserSession(id="test_session", last_active=datetime.utcnow())
            db.session.add(session)
            db.session.commit()
        return "test_session"

class TestChatEndpoints:
    def test_chat_message_success(self, client, session_id):
        response = client.post('/api/chat', json={'message': 'Hello'}, 
                              headers={'X-Session-ID': session_id})
        assert response.status_code == 200
        data = response.get_json()
        assert 'response' in data
        assert 'risk_level' in data
    
    def test_chat_history(self, client, session_id):
        # Send message first
        client.post('/api/chat', json={'message': 'Hello'}, 
                   headers={'X-Session-ID': session_id})
        
        # Get history
        response = client.get('/api/chat_history', headers={'X-Session-ID': session_id})
        assert response.status_code == 200

class TestMoodEndpoints:
    def test_mood_entry_creation(self, client, session_id):
        response = client.post('/api/mood_entry', json={
            'mood_level': 3,
            'note': 'Feeling okay'
        }, headers={'X-Session-ID': session_id})
        assert response.status_code in [200, 201]
    
    def test_mood_history(self, client, session_id):
        # Create entry first
        client.post('/api/mood_entry', json={'mood_level': 3}, 
                   headers={'X-Session-ID': session_id})
        
        # Get history
        response = client.get('/api/mood_history', headers={'X-Session-ID': session_id})
        assert response.status_code == 200

class TestAssessmentEndpoints:
    def test_phq9_submission(self, client, session_id):
        response = client.post('/api/assessment/phq9', json={
            'responses': [1,1,1,1,1,1,1,1,1]
        }, headers={'X-Session-ID': session_id})
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_score'] == 9
    
    def test_gad7_submission(self, client, session_id):
        response = client.post('/api/assessment/gad7', json={
            'responses': [1,1,1,1,1,1,1]
        }, headers={'X-Session-ID': session_id})
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_score'] == 7

class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert data['status'] in ['healthy', 'degraded']
