
import os
# Force SQLite for testing BEFORE importing app/models which might read env
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["AI_PROVIDER"] = "gemini" # Prevent startup warnings

import pytest
import uuid
from app import create_app, db
from models import MoodEntry, UserSession

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    
    with app.app_context():
        # SQLite doesn't support JSONB/ARRAY types natively in the way our models define them for Postgres
        # But allow it to try.
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_feedback_prompt_trigger(client):
    """
    Test that the feedback prompt flag appears ONLY on the 3rd check-in.
    """
    # 1. Create a fresh session
    session_id = str(uuid.uuid4())
    headers = {"X-Session-ID": session_id}
    
    # 2. Add 5 mood entries and check the flag
    for i in range(1, 6):
        response = client.post(
            "/api/mood_entry",
            json={"mood_level": 3, "note": f"Check-in #{i}"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.get_json()
        
        # KEY ASSERTION: Flag should be true ONLY when i == 3
        if i == 3:
            assert data["show_feedback_prompt"] is True, f"Failed on entry #{i}"
        else:
            assert data["show_feedback_prompt"] is False, f"Failed on entry #{i}"
            
    print("\n✅ verified: Feedback prompt showed exactly on 3rd entry.")
