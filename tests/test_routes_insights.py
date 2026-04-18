"""Integration tests for routes/insights.py endpoints."""

import os
import sys
import uuid
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["PYTEST_CURRENT_TEST"] = "true"

from app import create_app
from models import InterventionOutcome, Message, MoodEntry, UserSession, db


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "RATE_LIMIT_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def session_id(app):
    sid = str(uuid.uuid4())
    with app.app_context():
        db.session.add(UserSession(id=sid))
        db.session.commit()
    return sid


def _seed_moods(app, sid, levels_and_days):
    with app.app_context():
        now = datetime.utcnow()
        for level, days_ago in levels_and_days:
            db.session.add(MoodEntry(
                session_id=sid, mood_level=level,
                timestamp=now - timedelta(days=days_ago),
            ))
        db.session.commit()


def _seed_messages(app, sid, texts_and_days):
    with app.app_context():
        now = datetime.utcnow()
        for text, days_ago in texts_and_days:
            db.session.add(Message(
                session_id=sid, content=text, is_user=True,
                timestamp=now - timedelta(days=days_ago),
            ))
        db.session.commit()


def _seed_outcomes(app, sid, rows):
    with app.app_context():
        for etype, before, after in rows:
            db.session.add(InterventionOutcome(
                session_id=sid, intervention_id=f"i-{etype}",
                exercise_type=etype, mood_before=before, mood_after=after,
            ))
        db.session.commit()


# ---------------------------------------------------------------------------
# /api/insights/weekly
# ---------------------------------------------------------------------------

class TestWeeklyEndpoint:
    def test_missing_session_id_400(self, client):
        r = client.get("/api/insights/weekly")
        assert r.status_code == 400
        assert "X-Session-ID" in r.json.get("error", "")

    def test_empty_session_returns_nulls(self, client, session_id):
        r = client.get(
            "/api/insights/weekly",
            headers={"X-Session-ID": session_id},
        )
        assert r.status_code == 200
        assert r.json["count"] == 0
        assert r.json["mean"] is None

    def test_with_entries(self, client, app, session_id):
        _seed_moods(app, session_id, [(5, 1), (3, 2), (1, 3)])
        r = client.get(
            "/api/insights/weekly",
            headers={"X-Session-ID": session_id},
        )
        assert r.status_code == 200
        assert r.json["count"] == 3
        assert r.json["mean"] == 3.0
        assert r.json["min"] == 1 and r.json["max"] == 5

    def test_window_30(self, client, app, session_id):
        _seed_moods(app, session_id, [(4, 20), (2, 5)])
        r = client.get(
            "/api/insights/weekly?window=30",
            headers={"X-Session-ID": session_id},
        )
        assert r.status_code == 200
        assert r.json["count"] == 2
        assert r.json["window_days"] == 30

    def test_invalid_window_falls_back_to_default(self, client, session_id):
        r = client.get(
            "/api/insights/weekly?window=999",
            headers={"X-Session-ID": session_id},
        )
        assert r.status_code == 200
        assert r.json["window_days"] == 7

    def test_session_scoping(self, client, app, session_id):
        other_sid = str(uuid.uuid4())
        with app.app_context():
            db.session.add(UserSession(id=other_sid))
            db.session.commit()
        _seed_moods(app, other_sid, [(5, 1)])
        r = client.get(
            "/api/insights/weekly",
            headers={"X-Session-ID": session_id},
        )
        # Our session has no entries
        assert r.json["count"] == 0


# ---------------------------------------------------------------------------
# /api/insights/keywords
# ---------------------------------------------------------------------------

class TestKeywordsEndpoint:
    def test_missing_session_id_400(self, client):
        r = client.get("/api/insights/keywords")
        assert r.status_code == 400

    def test_empty_session(self, client, session_id):
        r = client.get(
            "/api/insights/keywords",
            headers={"X-Session-ID": session_id},
        )
        assert r.status_code == 200
        assert r.json["heatmap"] == []
        assert r.json["totals_per_bucket"] == {}
        assert "buckets" in r.json

    def test_crisis_keyword_detected(self, client, app, session_id):
        _seed_messages(app, session_id, [
            ("I feel hopeless today", 1),
            ("Another normal message", 2),
        ])
        r = client.get(
            "/api/insights/keywords",
            headers={"X-Session-ID": session_id},
        )
        assert r.status_code == 200
        assert r.json["totals_per_bucket"].get("hopelessness") == 1

    def test_no_raw_text_leaked(self, client, app, session_id):
        secret = "my secret account password is xyz123"
        _seed_messages(app, session_id, [(f"hopeless {secret}", 1)])
        r = client.get(
            "/api/insights/keywords",
            headers={"X-Session-ID": session_id},
        )
        body = r.data.decode()
        assert "xyz123" not in body
        assert secret not in body


# ---------------------------------------------------------------------------
# /api/insights/quest-correlation
# ---------------------------------------------------------------------------

class TestQuestCorrelationEndpoint:
    def test_missing_session_400(self, client):
        r = client.get("/api/insights/quest-correlation")
        assert r.status_code == 400

    def test_empty(self, client, session_id):
        r = client.get(
            "/api/insights/quest-correlation",
            headers={"X-Session-ID": session_id},
        )
        assert r.status_code == 200
        assert r.json["overall_delta"] is None
        assert r.json["per_type"] == []

    def test_with_outcomes(self, client, app, session_id):
        _seed_outcomes(app, session_id, [
            ("breathing", 2, 4),
            ("breathing", 3, 4),
            ("grounding", 3, 3),
        ])
        r = client.get(
            "/api/insights/quest-correlation",
            headers={"X-Session-ID": session_id},
        )
        assert r.status_code == 200
        types = [t["type"] for t in r.json["per_type"]]
        # Breathing should rank above grounding
        assert types.index("breathing") < types.index("grounding")


# ---------------------------------------------------------------------------
# /api/insights/next-steps
# ---------------------------------------------------------------------------

class TestNextStepsEndpoint:
    def test_missing_session_400(self, client):
        r = client.get("/api/insights/next-steps")
        assert r.status_code == 400

    def test_empty_session_returns_fallback(self, client, session_id):
        r = client.get(
            "/api/insights/next-steps",
            headers={"X-Session-ID": session_id},
        )
        assert r.status_code == 200
        assert "next_steps" in r.json
        assert len(r.json["next_steps"]) >= 1

    def test_crisis_keyword_elevates_cta(self, client, app, session_id):
        _seed_messages(app, session_id, [
            ("I want to end it all", 1),
        ])
        r = client.get(
            "/api/insights/next-steps",
            headers={"X-Session-ID": session_id},
        )
        types = [c["type"] for c in r.json["next_steps"]]
        assert "crisis_resource" in types

    def test_low_mood_triggers_reach_out(self, client, app, session_id):
        _seed_moods(app, session_id, [(1, 1), (2, 2), (2, 3)])
        r = client.get(
            "/api/insights/next-steps",
            headers={"X-Session-ID": session_id},
        )
        types = [c["type"] for c in r.json["next_steps"]]
        assert "reach_out" in types

    def test_response_schema(self, client, session_id):
        r = client.get(
            "/api/insights/next-steps",
            headers={"X-Session-ID": session_id},
        )
        assert r.status_code == 200
        for cta in r.json["next_steps"]:
            assert set(cta.keys()) == {"type", "title", "description", "action"}


# ---------------------------------------------------------------------------
# Smoke: all 4 endpoints registered
# ---------------------------------------------------------------------------

class TestEndpointsRegistered:
    def test_all_four_routes_present(self, app):
        rules = {r.rule for r in app.url_map.iter_rules()}
        for expected in [
            "/api/insights/weekly",
            "/api/insights/keywords",
            "/api/insights/quest-correlation",
            "/api/insights/next-steps",
        ]:
            assert expected in rules, f"Missing: {expected}"
