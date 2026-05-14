import os
import sys
import time
import uuid
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import JournalEntry, db


@pytest.fixture
def app():
    os.environ["PYTEST_CURRENT_TEST"] = "true"
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
        "RATE_LIMIT_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _sid():
    return str(uuid.uuid4())


def _headers(session_id):
    return {"X-Session-ID": session_id}


def test_post_get_round_trip_with_body_only(client):
    sid = _sid()
    created = client.post("/api/journal", json={"body": "first entry"}, headers=_headers(sid))
    listed = client.get("/api/journal", headers=_headers(sid))
    assert created.status_code == 201
    created_data = created.get_json()
    assert created_data["id"]
    assert created_data["body"] == "first entry"
    assert created_data["title"] is None
    assert created_data["moodTag"] is None
    assert listed.status_code == 200
    assert listed.get_json()[0]["id"] == created_data["id"]


def test_post_get_round_trip_with_title_and_mood_tag(client):
    sid = _sid()
    response = client.post(
        "/api/journal",
        json={"title": "Morning", "body": "I feel steady", "moodTag": "good"},
        headers=_headers(sid),
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["title"] == "Morning"
    assert data["body"] == "I feel steady"
    assert data["moodTag"] == "good"


def test_patch_updates_body_and_updated_at_advances(client):
    sid = _sid()
    created = client.post("/api/journal", json={"body": "draft"}, headers=_headers(sid)).get_json()
    time.sleep(0.01)
    response = client.patch(
        f"/api/journal/{created['id']}",
        json={"body": "revised"},
        headers=_headers(sid),
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["body"] == "revised"
    assert datetime.fromisoformat(data["updatedAt"]) > datetime.fromisoformat(created["updatedAt"])


def test_delete_soft_removes_entry(client):
    sid = _sid()
    entry_id = client.post("/api/journal", json={"body": "delete me"}, headers=_headers(sid)).get_json()["id"]
    deleted = client.delete(f"/api/journal/{entry_id}", headers=_headers(sid))
    listed = client.get("/api/journal", headers=_headers(sid))
    assert deleted.status_code == 200
    assert deleted.get_json() == {"deleted": True}
    assert listed.status_code == 200
    assert listed.get_json() == []
    with client.application.app_context():
        entry = db.session.get(JournalEntry, entry_id)
        assert entry.deleted_at is not None


def test_validation_empty_and_oversized_body_return_400(client):
    sid = _sid()
    empty = client.post("/api/journal", json={"body": "   "}, headers=_headers(sid))
    oversized = client.post("/api/journal", json={"body": "x" * (50 * 1024 + 1)}, headers=_headers(sid))
    assert empty.status_code == 400
    assert empty.get_json()["error"] == "body is required"
    assert oversized.status_code == 400
    assert oversized.get_json()["error"] == "body must be at most 50 KB"


def test_pagination_limit_timestamp_slices_entries(client):
    sid = _sid()
    base = datetime.utcnow() - timedelta(minutes=5)
    with client.application.app_context():
        entries = []
        for i in range(5):
            entry = JournalEntry(
                session_id=sid,
                body=f"entry {i}",
                created_at=base + timedelta(minutes=i),
                updated_at=base + timedelta(minutes=i),
            )
            db.session.add(entry)
            entries.append(entry)
        db.session.commit()
        before = entries[4].created_at.isoformat()
    response = client.get(f"/api/journal?limit=2&before={before}", headers=_headers(sid))
    assert response.status_code == 200
    assert [item["body"] for item in response.get_json()] == ["entry 3", "entry 2"]
