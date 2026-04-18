"""Integration tests for routes/crisis.py (Phase I)."""

import os
import sys
import uuid
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["PYTEST_CURRENT_TEST"] = "true"

from app import create_app
from models import CrisisEscalation, UserSession, db
from providers.twilio_client import reset_circuit


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "RATE_LIMIT_ENABLED": False,
        "ADMIN_API_TOKEN": "admin-test-token",
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


@pytest.fixture(autouse=True)
def _reset_twilio():
    reset_circuit()
    yield
    reset_circuit()


# ---------------------------------------------------------------------------
# /api/crisis/resources
# ---------------------------------------------------------------------------

class TestCrisisResources:
    def test_default_returns_resources(self, client):
        r = client.get("/api/crisis/resources")
        assert r.status_code == 200
        assert "country" in r.json
        assert "resources" in r.json
        assert "available_countries" in r.json
        assert len(r.json["resources"]) >= 1

    def test_country_override_query(self, client):
        r = client.get("/api/crisis/resources?country=US")
        assert r.json["country"] == "us"

    def test_country_override_header(self, client):
        r = client.get(
            "/api/crisis/resources",
            headers={"X-Country-Override": "IN"},
        )
        assert r.json["country"] == "in"

    def test_invalid_country_falls_back_to_ip(self, client):
        r = client.get("/api/crisis/resources?country=ZZ")
        # ZZ not in map, falls back
        assert r.json["country"] != "ZZ"


# ---------------------------------------------------------------------------
# /api/crisis/escalate
# ---------------------------------------------------------------------------

class TestCrisisEscalate:
    def test_missing_session_400(self, client):
        r = client.post("/api/crisis/escalate", json={})
        assert r.status_code == 400

    def test_invalid_channel_400(self, client, session_id):
        r = client.post(
            "/api/crisis/escalate",
            headers={"X-Session-ID": session_id},
            json={"channel": "carrier_pigeon"},
        )
        assert r.status_code == 400

    def test_banner_only_creates_record(self, client, app, session_id):
        r = client.post(
            "/api/crisis/escalate?country=us",
            headers={"X-Session-ID": session_id},
            json={"channel": "banner_only"},
        )
        assert r.status_code == 200
        assert r.json["ok"] is True
        assert "escalation_id" in r.json
        # US has a primary phone (988), so tel_link should be set
        assert r.json["fallback"]["tel_link"]
        assert "988" in r.json["fallback"]["tel_link"]

        with app.app_context():
            e = CrisisEscalation.query.get(r.json["escalation_id"])
            assert e is not None
            assert e.channel == "banner_only"
            assert e.status == "initiated"

    def test_sms_without_phone_returns_fallback(self, client, session_id):
        r = client.post(
            "/api/crisis/escalate",
            headers={"X-Session-ID": session_id},
            json={"channel": "sms"},
        )
        assert r.status_code == 200
        assert r.json["sms"]["ok"] is False
        assert "user_phone required" in r.json["sms"]["error"]

    def test_sms_with_phone_sends_mock(self, client, app, session_id):
        # Twilio is auto-disabled under pytest; should return mock success
        r = client.post(
            "/api/crisis/escalate",
            headers={"X-Session-ID": session_id},
            json={"channel": "sms", "user_phone": "+15551234567"},
        )
        assert r.status_code == 200
        assert r.json["sms"]["ok"] is True
        assert r.json["sms"].get("mock") is True

        with app.app_context():
            e = CrisisEscalation.query.get(r.json["escalation_id"])
            assert e.status == "sent"

    def test_privacy_no_raw_message_sent(self, client, session_id, monkeypatch):
        """Verify SMS body never contains raw user content."""
        import sys
        import types
        from unittest.mock import MagicMock

        monkeypatch.setenv("TWILIO_FORCE_ENABLE", "true")
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "tok")
        monkeypatch.setenv("TWILIO_FROM_NUMBER", "+111")
        monkeypatch.delenv("TWILIO_DISABLED", raising=False)

        mock_client = MagicMock()
        mock_msg = MagicMock(sid="SM1")
        mock_client.messages.create.return_value = mock_msg

        fake_twilio = types.ModuleType("twilio")
        fake_rest = types.ModuleType("twilio.rest")
        fake_rest.Client = MagicMock(return_value=mock_client)
        sys.modules["twilio"] = fake_twilio
        sys.modules["twilio.rest"] = fake_rest
        try:
            r = client.post(
                "/api/crisis/escalate",
                headers={"X-Session-ID": session_id},
                json={"channel": "sms", "user_phone": "+15551234567"},
            )
        finally:
            sys.modules.pop("twilio", None)
            sys.modules.pop("twilio.rest", None)

        assert r.status_code == 200
        call_kwargs = mock_client.messages.create.call_args.kwargs
        sms_body = call_kwargs.get("body", "")
        # Must contain product name but no session id or user content
        assert session_id not in sms_body
        assert "GentleQuest" in sms_body


# ---------------------------------------------------------------------------
# /api/crisis/check-in/run
# ---------------------------------------------------------------------------

class TestCheckIn:
    def test_requires_admin_token(self, client):
        r = client.post("/api/crisis/check-in/run")
        assert r.status_code == 401

    def test_wrong_token_unauthorized(self, client):
        r = client.post(
            "/api/crisis/check-in/run",
            headers={"X-Admin-Token": "wrong"},
        )
        assert r.status_code == 401

    def test_empty_db_zero_processed(self, client):
        r = client.post(
            "/api/crisis/check-in/run",
            headers={"X-Admin-Token": "admin-test-token"},
        )
        assert r.status_code == 200
        assert r.json["ok"] is True
        assert r.json["processed"] == 0

    def test_old_escalation_checked_in(self, client, app, session_id):
        with app.app_context():
            old = CrisisEscalation(
                session_id=session_id,
                country_code="US",
                channel="sms",
                status="sent",
                created_at=datetime.utcnow() - timedelta(hours=25),
                check_in_sent=False,
            )
            db.session.add(old)
            db.session.commit()
            old_id = old.id

        r = client.post(
            "/api/crisis/check-in/run",
            headers={"X-Admin-Token": "admin-test-token"},
        )
        assert r.status_code == 200
        assert r.json["processed"] == 1

        with app.app_context():
            e = CrisisEscalation.query.get(old_id)
            assert e.check_in_sent is True
            assert e.check_in_at is not None
            assert e.status == "checked_in"

    def test_recent_escalation_skipped(self, client, app, session_id):
        with app.app_context():
            recent = CrisisEscalation(
                session_id=session_id,
                country_code="US",
                channel="banner_only",
                status="initiated",
                created_at=datetime.utcnow() - timedelta(hours=2),
            )
            db.session.add(recent)
            db.session.commit()

        r = client.post(
            "/api/crisis/check-in/run",
            headers={"X-Admin-Token": "admin-test-token"},
        )
        assert r.json["processed"] == 0

    def test_idempotent_no_double_check_in(self, client, app, session_id):
        with app.app_context():
            old = CrisisEscalation(
                session_id=session_id,
                country_code="US",
                channel="sms",
                status="sent",
                created_at=datetime.utcnow() - timedelta(hours=30),
            )
            db.session.add(old)
            db.session.commit()

        # First run processes it
        r1 = client.post(
            "/api/crisis/check-in/run",
            headers={"X-Admin-Token": "admin-test-token"},
        )
        assert r1.json["processed"] == 1

        # Second run finds nothing new
        r2 = client.post(
            "/api/crisis/check-in/run",
            headers={"X-Admin-Token": "admin-test-token"},
        )
        assert r2.json["processed"] == 0


# ---------------------------------------------------------------------------
# Registration smoke
# ---------------------------------------------------------------------------

class TestEndpointsRegistered:
    def test_all_three_registered(self, app):
        rules = {r.rule for r in app.url_map.iter_rules()}
        for expected in [
            "/api/crisis/resources",
            "/api/crisis/escalate",
            "/api/crisis/check-in/run",
        ]:
            assert expected in rules, f"Missing: {expected}"
