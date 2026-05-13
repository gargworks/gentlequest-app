"""Tests for contextChips field on POST /api/mood_entry + GET /api/mood_history."""

import json
import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import db


# ---------------------------------------------------------------------------
# Fixtures — same pattern as test_mood_provider.py
# ---------------------------------------------------------------------------

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


def _session_id():
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# 1. POST + GET round-trip with chips
# ---------------------------------------------------------------------------

class TestContextChipsRoundTrip:
    def test_post_and_get_with_chips(self, client):
        sid = _session_id()
        resp = client.post(
            "/api/mood_entry",
            data=json.dumps({"mood_level": 3, "contextChips": ["Work", "Sleep"]}),
            content_type="application/json",
            headers={"X-Session-ID": sid},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["contextChips"] == ["Work", "Sleep"]

        hist = client.get(
            "/api/mood_history",
            headers={"X-Session-ID": sid},
        )
        assert hist.status_code == 200
        entries = hist.get_json()
        assert len(entries) == 1
        assert entries[0]["contextChips"] == ["Work", "Sleep"]


# ---------------------------------------------------------------------------
# 2. POST with empty list — must round-trip as []
# ---------------------------------------------------------------------------

class TestContextChipsEmpty:
    def test_empty_list_round_trips(self, client):
        sid = _session_id()
        resp = client.post(
            "/api/mood_entry",
            data=json.dumps({"mood_level": 4, "contextChips": []}),
            content_type="application/json",
            headers={"X-Session-ID": sid},
        )
        assert resp.status_code == 200
        assert resp.get_json()["contextChips"] == []

        hist = client.get(
            "/api/mood_history",
            headers={"X-Session-ID": sid},
        )
        entries = hist.get_json()
        assert entries[0]["contextChips"] == []

    def test_omitted_chips_defaults_to_empty(self, client):
        sid = _session_id()
        resp = client.post(
            "/api/mood_entry",
            data=json.dumps({"mood_level": 2}),
            content_type="application/json",
            headers={"X-Session-ID": sid},
        )
        assert resp.status_code == 200
        assert resp.get_json()["contextChips"] == []


# ---------------------------------------------------------------------------
# 3. POST with malformed chips — all should return 400
# ---------------------------------------------------------------------------

class TestContextChipsMalformed:
    def _post(self, client, payload):
        return client.post(
            "/api/mood_entry",
            data=json.dumps(payload),
            content_type="application/json",
            headers={"X-Session-ID": _session_id()},
        )

    def test_non_list_rejected(self, client):
        resp = self._post(client, {"mood_level": 3, "contextChips": "Work"})
        assert resp.status_code == 400
        assert "list" in resp.get_json()["error"].lower()

    def test_list_of_numbers_rejected(self, client):
        resp = self._post(client, {"mood_level": 3, "contextChips": [1, 2, 3]})
        assert resp.status_code == 400
        assert "string" in resp.get_json()["error"].lower()

    def test_too_many_items_rejected(self, client):
        chips = [f"chip{i}" for i in range(11)]
        resp = self._post(client, {"mood_level": 3, "contextChips": chips})
        assert resp.status_code == 400
        assert "10" in resp.get_json()["error"]

    def test_oversized_string_rejected(self, client):
        resp = self._post(client, {"mood_level": 3, "contextChips": ["x" * 41]})
        assert resp.status_code == 400
        assert "40" in resp.get_json()["error"]
