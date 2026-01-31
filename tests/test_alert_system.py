import pytest
from app import create_app
from models import db, CounselorAlert, Message, AlertAcknowledgment
from providers.alert_manager import AlertManager, AlertSeverity

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

def test_alert_manager_severity_logic():
    """Test mapping of risk scores to severity levels."""
    assert AlertManager.determine_severity('crisis', 0.95) == AlertSeverity.CRITICAL
    assert AlertManager.determine_severity('high', 0.8) == AlertSeverity.HIGH
    assert AlertManager.determine_severity('medium', 0.6) == AlertSeverity.MEDIUM
    assert AlertManager.determine_severity('low', 0.2) == AlertSeverity.LOW

def test_create_alert_and_deduplication(app):
    """Test alert creation and rate limiting logic."""
    with app.app_context():
        session_id = "test_alert_sess"
        
        # 1. Create Initial High Severity Alert
        alert_id_1 = AlertManager.create_alert(
            session_id=session_id,
            trigger_message="I want to hurt myself",
            risk_level="crisis",
            risk_score=0.95,
            keywords=["hurt", "die"],
            university_id=1
        )
        assert alert_id_1 is not None
        
        # 2. Try to create duplicate alert immediately (Should be blocked)
        alert_id_2 = AlertManager.create_alert(
            session_id=session_id,
            trigger_message="I really want to hurt myself", 
            risk_level="high", # Lower/Equal severity
            risk_score=0.8,
            keywords=["hurt"],
            university_id=1
        )
        assert alert_id_2 is None # Should be rate limited
        
        # 3. Verify DB state
        alerts = CounselorAlert.query.filter_by(session_id=session_id).all()
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.CRITICAL

def test_alert_api_flow(client, app):
    """Test fetching and acknowledging alerts via API."""
    with app.app_context():
        # Seed an alert
        alert = CounselorAlert(
            session_id="api_test_sess",
            university_id=1,
            severity="high",
            trigger_message="Test Trigger",
            conversation_excerpt="User: Help\nLuna: Here for you",
            risk_keywords="help"
        )
        db.session.add(alert)
        db.session.commit()
        alert_id = alert.id

    # 1. Get History
    resp = client.get('/api/alerts/history?university_id=1')
    assert resp.status_code == 200
    data = resp.json
    assert len(data['alerts']) == 1
    assert data['alerts'][0]['id'] == alert_id
    assert data['alerts'][0]['acknowledged_at'] is None
    
    # 2. Acknowledge Alert
    resp = client.post(f'/api/alerts/{alert_id}/acknowledge', json={
        "counselor_id": "counselor_01",
        "response_notes": "Called student.",
        "action_taken": "escorted_to_clinic"
    })
    assert resp.status_code == 200
    assert resp.json['success'] is True
    
    # 3. Verify History Update
    resp = client.get('/api/alerts/history?university_id=1&status=acknowledged')
    data = resp.json
    assert len(data['alerts']) == 1
    assert data['alerts'][0]['acknowledged_by'] == "counselor_01"
