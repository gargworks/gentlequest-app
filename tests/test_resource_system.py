import pytest
from app import create_app
from models import db, Resource, UserResourceInteraction, UserSession

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    
    with app.app_context():
        db.create_all()
        # Seed session for FK-backed interactions
        if not UserSession.query.get("test_sess"):
            db.session.add(UserSession(id="test_sess"))
        if not UserSession.query.get("test_interaction_sess"):
            db.session.add(UserSession(id="test_interaction_sess"))
        # Seed test data (active resources)
        r1 = Resource(title="Test Crisis", description="D1", category="crisis", tags="tag1", is_active=True)
        r2 = Resource(title="Test SelfHelp", description="D2", category="self_help", tags="tag2", is_active=True)
        db.session.add_all([r1, r2])
        db.session.commit()
        
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_resources(client):
    """Test fetching resources with filters."""
    headers = {"X-Session-ID": "test_sess"}
    
    # 1. Get All
    resp = client.get('/api/resources', headers=headers)
    assert resp.status_code == 200
    data = resp.json
    assert len(data['resources']) == 2
    
    # 2. Filter by Category
    resp = client.get('/api/resources?category=crisis', headers=headers)
    data = resp.json
    assert len(data['resources']) == 1
    assert data['resources'][0]['title'] == "Test Crisis"
    
    # 3. Search
    resp = client.get('/api/resources?search=SelfHelp', headers=headers)
    data = resp.json
    assert len(data['resources']) == 1
    assert data['resources'][0]['title'] == "Test SelfHelp"

def test_track_interaction(client):
    """Test tracking resource views."""
    session_id = "test_interaction_sess"
    headers = {"X-Session-ID": session_id}
    
    # Get ID of first resource
    resp = client.get('/api/resources', headers=headers)
    resource_id = resp.json['resources'][0]['id']
    
    # Track View
    resp = client.post(f'/api/resources/{resource_id}/view', headers=headers)
    assert resp.status_code == 200
    assert resp.json['success'] is True
    
    # Verify DB
    with client.application.app_context():
        interaction = UserResourceInteraction.query.filter_by(session_id=session_id).first()
        assert interaction is not None
        assert interaction.resource_id == resource_id
