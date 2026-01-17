"""
Comprehensive test suite for Resource System (Content Library)
Run with: pytest tests/test_resource_system.py -v
"""

import pytest
from datetime import datetime
from app import create_app
from models import db
from sqlalchemy import text

@pytest.fixture
def app():
    """Create test app with in-memory database"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Create user_sessions if not exists (db.create_all might create it if in models.py)
        # It IS in models.py, so db.create_all() handles it.
        # But we need raw SQL tables for resources since they aren't in models.py
        
        # Resources Table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                description VARCHAR(1000) NOT NULL,
                url VARCHAR(500),
                category VARCHAR(50) NOT NULL, -- Enum in Postgres, Varchar here
                country VARCHAR(10),
                university_id INTEGER,
                tags VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """))
        
        # Interactions Table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS user_resource_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(255) NOT NULL,
                resource_id INTEGER NOT NULL,
                viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES user_sessions(id),
                FOREIGN KEY (resource_id) REFERENCES resources(id)
            )
        """))
        
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def session_id(app):
    """Create test session"""
    with app.app_context():
        sid = "test_session_res_123"
        # Check if exists first to be safe, though fixture yields fresh db
        db.session.execute(
            text("INSERT INTO user_sessions (id) VALUES (:id)"),
            {"id": sid}
        )
        db.session.commit()
        return sid

class TestResourceSystem:
    
    def test_get_resources_empty(self, client, session_id):
        """Test fetching resources when empty"""
        response = client.get('/api/resources', headers={'X-Session-ID': session_id})
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 0
        assert data['resources'] == []

    def test_get_resources_populated(self, client, session_id, app):
        """Test fetching resources with data"""
        with app.app_context():
            db.session.execute(text("""
                INSERT INTO resources (title, description, category, tags)
                VALUES ('Test Resource', 'Desc', 'self_help', 'anxiety,stress')
            """))
            db.session.commit()
            
        response = client.get('/api/resources', headers={'X-Session-ID': session_id})
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 1
        assert data['resources'][0]['title'] == 'Test Resource'
        assert 'anxiety' in data['resources'][0]['tags']

    def test_filter_by_category(self, client, session_id, app):
        """Test filtering resources by category"""
        with app.app_context():
            db.session.execute(text("""
                INSERT INTO resources (title, description, category) VALUES 
                ('Crisis Help', 'Help', 'crisis'),
                ('Self Care', 'Care', 'self_help')
            """))
            db.session.commit()
            
        # Filter for crisis
        response = client.get('/api/resources?category=crisis', headers={'X-Session-ID': session_id})
        data = response.get_json()
        assert data['count'] == 1
        assert data['resources'][0]['title'] == 'Crisis Help'
        
        # Filter for self_help
        response = client.get('/api/resources?category=self_help', headers={'X-Session-ID': session_id})
        data = response.get_json()
        assert data['count'] == 1
        assert data['resources'][0]['title'] == 'Self Care'

    def test_search_resources(self, client, session_id, app):
        """Test searching resources"""
        with app.app_context():
            db.session.execute(text("""
                INSERT INTO resources (title, description, category) VALUES 
                ('Meditation Guide', 'Breathing exercises', 'self_help'),
                ('Academic Support', 'Study tips', 'university')
            """))
            db.session.commit()
            
        response = client.get('/api/resources?search=breathing', headers={'X-Session-ID': session_id})
        data = response.get_json()
        assert data['count'] == 1
        assert data['resources'][0]['title'] == 'Meditation Guide'

    def test_track_resource_view(self, client, session_id, app):
        """Test tracking a resource view"""
        with app.app_context():
            # Create resource
            result = db.session.execute(text("INSERT INTO resources (title, description, category) VALUES ('A', 'B', 'C') RETURNING id"))
            res_id = result.scalar()
            db.session.commit()
            
        # View it
        response = client.post(f'/api/resources/{res_id}/view', 
                             headers={'X-Session-ID': session_id},
                             json={})
        
        assert response.status_code == 200
        assert response.get_json()['success'] == True
        
        # Verify DB
        with app.app_context():
            count = db.session.execute(text("SELECT count(*) FROM user_resource_interactions")).scalar()
            assert count == 1

    def test_track_view_invalid_id(self, client, session_id):
        """Test viewing non-existent resource"""
        response = client.post('/api/resources/999/view', 
                             headers={'X-Session-ID': session_id},
                             json={})
        assert response.status_code == 404

    def test_unauthorized_access(self, client):
        """Test access without session ID"""
        response = client.get('/api/resources')
        assert response.status_code == 401
