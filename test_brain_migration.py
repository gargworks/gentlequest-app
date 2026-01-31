import pytest
from app import create_app
from models import db, BrainState, BrainEvent
from providers.brain_state import get_brain_state, set_brain_state, emit_brain_event, get_recent_brain_events

@pytest.fixture
def app():
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_brain_state_initialization(app):
    """Test that brain state initializes with defaults."""
    with app.app_context():
        state = get_brain_state()
        assert state['current_sprint']['id'] == 'none'
        assert BrainState.query.count() == 1

def test_set_brain_state(app):
    """Test updating brain state."""
    with app.app_context():
        success = set_brain_state({"current_sprint": {"id": "sprint-001", "name": "Test Sprint"}})
        assert success is True
        
        state = get_brain_state()
        assert state['current_sprint']['id'] == 'sprint-001'
        assert state['current_sprint']['name'] == 'Test Sprint'

def test_emit_brain_event(app):
    """Test emitting brain events."""
    with app.app_context():
        event_id = emit_brain_event(
            emitter="test_agent",
            event_type="test_event",
            payload={"foo": "bar"},
            severity="NOTABLE"
        )
        assert event_id is not None
        assert len(event_id) == 8
        
        events = get_recent_brain_events(1)
        assert len(events) == 1
        assert events[0]['event_id'] == event_id
        assert events[0]['event_type'] == "test_event"
        assert events[0]['emitter'] == "test_agent"
        assert events[0]['payload'] == {"foo": "bar"}
        
        # Verify event counter
        state = get_brain_state()
        assert state['counters']['total_events'] == 1

def test_get_recent_events_order(app):
    """Test that events are returned in descending order (newest first)."""
    with app.app_context():
        emit_brain_event("agent", "type1", {})
        emit_brain_event("agent", "type2", {})
        
        events = get_recent_brain_events(2)
        assert len(events) == 2
        assert events[0]['event_type'] == "type2"
        assert events[1]['event_type'] == "type1"
