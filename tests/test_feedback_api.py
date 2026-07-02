import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import FeedbackSubmission, db


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


def test_submit_feedback_with_rating_only(client):
    sid = _sid()
    response = client.post("/api/feedback", json={"rating": 5}, headers=_headers(sid))
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["id"]
    with client.application.app_context():
        row = db.session.get(FeedbackSubmission, data["id"])
        assert row.rating == 5
        assert row.session_id == sid
        assert row.feedback_text is None


def test_submit_feedback_with_all_fields(client):
    sid = _sid()
    response = client.post(
        "/api/feedback",
        json={
            "rating": 3,
            "feedback_text": "Would love a dark mode",
            "app_version": "1.4.0",
            "platform": "ios",
        },
        headers=_headers(sid),
    )
    assert response.status_code == 201
    data = response.get_json()
    with client.application.app_context():
        row = db.session.get(FeedbackSubmission, data["id"])
        assert row.feedback_text == "Would love a dark mode"
        assert row.app_version == "1.4.0"
        assert row.platform == "ios"


def test_missing_rating_returns_400(client):
    sid = _sid()
    response = client.post("/api/feedback", json={}, headers=_headers(sid))
    assert response.status_code == 400
    assert "rating" in response.get_json()["error"]


def test_out_of_range_rating_returns_400(client):
    sid = _sid()
    response = client.post("/api/feedback", json={"rating": 6}, headers=_headers(sid))
    assert response.status_code == 400


def test_non_integer_rating_returns_400(client):
    sid = _sid()
    response = client.post("/api/feedback", json={"rating": "great"}, headers=_headers(sid))
    assert response.status_code == 400


def test_feedback_text_is_truncated_to_max_chars(client):
    sid = _sid()
    long_text = "x" * 5000
    response = client.post(
        "/api/feedback",
        json={"rating": 4, "feedback_text": long_text},
        headers=_headers(sid),
    )
    assert response.status_code == 201
    data = response.get_json()
    with client.application.app_context():
        row = db.session.get(FeedbackSubmission, data["id"])
        assert len(row.feedback_text) == 2000


def test_blank_feedback_text_stored_as_none(client):
    sid = _sid()
    response = client.post(
        "/api/feedback",
        json={"rating": 4, "feedback_text": "   "},
        headers=_headers(sid),
    )
    assert response.status_code == 201
    data = response.get_json()
    with client.application.app_context():
        row = db.session.get(FeedbackSubmission, data["id"])
        assert row.feedback_text is None
