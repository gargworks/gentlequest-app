import json
import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import AnalyticsEvent, Message, MoodEntry, User, UserSession, db


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


def test_export_round_trip_returns_inline_bundle_with_counts(client):
    sid = _sid()
    client.post(
        "/api/mood_entry",
        data=json.dumps({"mood_level": 4, "note": "steady", "contextChips": ["Sleep"]}),
        content_type="application/json",
        headers=_headers(sid),
    )
    with client.application.app_context():
        db.session.add(Message(session_id=sid, content="hello", is_user=True))
        db.session.commit()

    response = client.post("/api/user/export", headers={**_headers(sid), "X-User-Email": "user@example.com"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["delivery"] == "inline_json"
    assert data["counts"]["mood_entries"] == 1
    assert data["counts"]["chat_messages"] == 1
    assert data["counts"]["journal_entries"] == 0
    assert data["mood_entries"][0]["contextChips"] == ["Sleep"]


def test_delete_cascade_removes_session_data_and_soft_deletes_user(client):
    sid = _sid()
    client.post(
        "/api/mood_entry",
        data=json.dumps({"mood_level": 2, "note": "hard"}),
        content_type="application/json",
        headers=_headers(sid),
    )
    client.post("/api/user/notification_prefs", json={"daily_checkin_enabled": True}, headers=_headers(sid))
    with client.application.app_context():
        db.session.add(Message(session_id=sid, content="chat", is_user=True))
        db.session.add(AnalyticsEvent(session_id=sid, event_type="test", event_metadata={"ip_masked": "1.2.3***"}))
        db.session.commit()

    response = client.delete("/api/user", headers=_headers(sid))

    assert response.status_code == 200
    assert response.get_json() == {"deleted": True}
    with client.application.app_context():
        assert MoodEntry.query.filter_by(session_id=sid).count() == 0
        assert Message.query.filter_by(session_id=sid).count() == 0
        assert AnalyticsEvent.query.filter_by(session_id=sid).count() == 0
        assert db.session.get(UserSession, sid) is None
        user = User.query.filter_by(session_id=None).one()
        assert user.deleted_at is not None
        assert user.email is None


def test_anonymity_toggle_round_trip(client):
    sid = _sid()

    enable = client.post("/api/user/anonymity", json={"enabled": True}, headers=_headers(sid))
    user = client.get("/api/user", headers=_headers(sid))
    disable = client.post("/api/user/anonymity", json={"enabled": False}, headers=_headers(sid))

    assert enable.status_code == 200
    assert enable.get_json() == {"anonymity_mode": True}
    assert user.get_json()["anonymity_mode"] is True
    assert disable.status_code == 200
    assert disable.get_json() == {"anonymity_mode": False}


def test_notification_prefs_round_trip(client):
    sid = _sid()
    prefs = {
        "daily_checkin_enabled": True,
        "daily_checkin_time": "09:00",
        "weekly_review_day": "Sunday",
        "weekly_review_time": "18:00",
        "streak_nudges_enabled": False,
    }

    post_response = client.post("/api/user/notification_prefs", json=prefs, headers=_headers(sid))
    get_response = client.get("/api/user/notification_prefs", headers=_headers(sid))

    assert post_response.status_code == 200
    assert post_response.get_json() == prefs
    assert get_response.status_code == 200
    assert get_response.get_json() == prefs


def test_anonymity_gates_analytics_write_path(client):
    sid = _sid()
    client.post("/api/user/anonymity", json={"enabled": True}, headers=_headers(sid))

    from helpers.session_helpers import _log_analytics_event

    _log_analytics_event(
        client.application,
        sid,
        "button_click",
        {"device_id": "device-1", "ip_masked": "1.2.3***"},
    )
    with client.application.app_context():
        assert AnalyticsEvent.query.filter_by(session_id=sid).count() == 0
