"""
Comprehensive test suite for Counselor Alert System (Crisis Management)
Run with: pytest tests/test_alert_system.py -v
"""

import pytest
from datetime import datetime, timedelta
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
        
        # Create tables using raw SQL for those not in models.py
        
        # University Counselors
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS university_counselors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                university_id INTEGER NOT NULL,
                name VARCHAR(200) NOT NULL,
                email VARCHAR(255) NOT NULL,
                phone VARCHAR(50),
                role VARCHAR(100),
                is_active BOOLEAN DEFAULT 1,
                receives_alerts BOOLEAN DEFAULT 1,
                alert_methods VARCHAR(100) DEFAULT 'email',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Counselor Alerts
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS counselor_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(255) NOT NULL,
                university_id INTEGER,
                severity VARCHAR(20) NOT NULL, -- Enum in Postgres
                trigger_message TEXT NOT NULL,
                conversation_excerpt TEXT,
                risk_keywords VARCHAR(500),
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged_at TIMESTAMP,
                acknowledged_by VARCHAR(255),
                email_sent BOOLEAN DEFAULT 0,
                sms_sent BOOLEAN DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES user_sessions(id)
            )
        """))
        
        # Alert Acknowledgments
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS alert_acknowledgments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER NOT NULL,
                counselor_id VARCHAR(255) NOT NULL,
                response_notes TEXT,
                action_taken VARCHAR(500),
                responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alert_id) REFERENCES counselor_alerts(id)
            )
        """))
        
        # Insert a dummy session
        db.session.execute(text("INSERT INTO user_sessions (id) VALUES ('test_session_alert_1')"))
        
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

class TestAlertSystem:
    
    def test_get_alert_history_empty(self, client):
        """Test fetching alerts when empty"""
        response = client.get('/api/alerts/history?university_id=1')
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 0
        assert data['alerts'] == []

    def test_get_alert_history_populated(self, client, app):
        """Test fetching alerts with data"""
        with app.app_context():
            db.session.execute(text("""
                INSERT INTO counselor_alerts (session_id, university_id, severity, trigger_message)
                VALUES ('test_session_alert_1', 1, 'high', 'Suicidal ideation detected')
            """))
            db.session.commit()
            
        response = client.get('/api/alerts/history?university_id=1')
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 1
        assert data['alerts'][0]['severity'] == 'high'
        assert data['alerts'][0]['trigger_message'] == 'Suicidal ideation detected'

    def test_filter_alerts(self, client, app):
        """Test filtering alerts"""
        with app.app_context():
            # Pending High
            db.session.execute(text("""
                INSERT INTO counselor_alerts (session_id, university_id, severity, trigger_message)
                VALUES ('test_session_alert_1', 1, 'high', 'msg1')
            """))
            # Acknowledged Medium
            db.session.execute(text("""
                INSERT INTO counselor_alerts (session_id, university_id, severity, trigger_message, acknowledged_at)
                VALUES ('test_session_alert_1', 1, 'medium', 'msg2', CURRENT_TIMESTAMP)
            """))
            db.session.commit()
            
        # Filter Pending
        response = client.get('/api/alerts/history?university_id=1&status=pending')
        data = response.get_json()
        assert data['count'] == 1
        assert data['alerts'][0]['severity'] == 'high'
        
        # Filter Acknowledged
        response = client.get('/api/alerts/history?university_id=1&status=acknowledged')
        data = response.get_json()
        assert data['count'] == 1
        assert data['alerts'][0]['severity'] == 'medium'
        
        # Filter by Severity
        response = client.get('/api/alerts/history?university_id=1&severity=high')
        data = response.get_json()
        assert data['count'] == 1

    def test_get_alert_detail(self, client, app):
        """Test fetching full alert details"""
        with app.app_context():
            # Create Alert
            result = db.session.execute(text("""
                INSERT INTO counselor_alerts (session_id, university_id, severity, trigger_message, risk_keywords)
                VALUES ('test_session_alert_1', 1, 'critical', 'Help me', 'help,suicide')
                RETURNING id
            """))
            alert_id = result.scalar()
            
            # Create Messages
            db.session.execute(text("""
                INSERT INTO messages (session_id, content, is_user, timestamp)
                VALUES 
                ('test_session_alert_1', 'I feel sad', 1, '2026-01-01 10:00:00'),
                ('test_session_alert_1', 'I am here for you', 0, '2026-01-01 10:00:05')
            """))
            db.session.commit()
            
        response = client.get(f'/api/alerts/{alert_id}')
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['alert']['severity'] == 'critical'
        assert data['alert']['risk_keywords'] == 'help,suicide'
        assert len(data['conversation']) == 2
        assert data['conversation'][0]['content'] == 'I feel sad'
        assert data['conversation'][0]['role'] == 'student'

    def test_acknowledge_alert(self, client, app):
        """Test acknowledging an alert"""
        with app.app_context():
            result = db.session.execute(text("""
                INSERT INTO counselor_alerts (session_id, university_id, severity, trigger_message)
                VALUES ('test_session_alert_1', 1, 'medium', 'Anxiety')
                RETURNING id
            """))
            alert_id = result.scalar()
            db.session.commit()
            
        payload = {
            "counselor_id": "counselor_123",
            "response_notes": "Called student, detailed plan made.",
            "action_taken": "phone_call"
        }
        
        response = client.post(f'/api/alerts/{alert_id}/acknowledge', json=payload)
        assert response.status_code == 200
        assert response.get_json()['success'] == True
        
        # Verify DB updates
        with app.app_context():
            # Check Alert Table
            alert = db.session.execute(text("SELECT acknowledged_at, acknowledged_by FROM counselor_alerts WHERE id = :id"), {"id": alert_id}).fetchone()
            assert alert[0] is not None
            assert alert[1] == "counselor_123"
            
            # Check Acknowledgment Log
            log = db.session.execute(text("SELECT response_notes FROM alert_acknowledgments WHERE alert_id = :id"), {"id": alert_id}).fetchone()
            assert log[0] == "Called student, detailed plan made."

    def test_acknowledge_invalid_id(self, client):
        """Test acknowledging missing alert"""
        response = client.post('/api/alerts/999/acknowledge', json={"counselor_id": "1"})
        assert response.status_code == 404

    def test_acknowledge_missing_counselor(self, client, app):
        """Test acknowledging without counselor ID"""
        with app.app_context():
            result = db.session.execute(text("INSERT INTO counselor_alerts (session_id, trigger_message, severity) VALUES ('s1', 't', 'low') RETURNING id"))
            alert_id = result.scalar()
            db.session.commit()
            
        response = client.post(f'/api/alerts/{alert_id}/acknowledge', json={})
        assert response.status_code == 400
