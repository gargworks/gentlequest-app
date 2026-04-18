"""Integration tests for routes/alerts.py (Phase H)."""

import os
import sys
import uuid
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["PYTEST_CURRENT_TEST"] = "true"

from app import create_app
from models import AlertAcknowledgment, CounselorAlert, UserSession, db


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "RATE_LIMIT_ENABLED": False,
        "ALERTS_STREAM_POLL_SEC": 0.01,
    })
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def counselor_headers():
    return {"X-Counselor-Id": "counselor-001"}


def _seed_alert(app, severity="high", minutes_ago=0, state="new"):
    sid = str(uuid.uuid4())
    with app.app_context():
        db.session.add(UserSession(id=sid))
        alert = CounselorAlert(
            session_id=sid,
            severity=severity,
            trigger_message="test crisis message",
            risk_keywords="hopeless,alone",
            sent_at=datetime.utcnow() - timedelta(minutes=minutes_ago),
            triage_state=state,
        )
        db.session.add(alert)
        db.session.commit()
        return alert.id


# ---------------------------------------------------------------------------
# POST /api/alerts/<id>/triage
# ---------------------------------------------------------------------------

class TestTriage:
    def test_requires_counselor_id(self, client):
        r = client.post("/api/alerts/1/triage", json={"target_state": "acknowledged"})
        assert r.status_code == 401

    def test_404_on_missing_alert(self, client, counselor_headers):
        r = client.post(
            "/api/alerts/99999/triage",
            headers=counselor_headers,
            json={"target_state": "acknowledged"},
        )
        assert r.status_code == 404

    def test_new_to_acknowledged(self, client, app, counselor_headers):
        aid = _seed_alert(app)
        r = client.post(
            f"/api/alerts/{aid}/triage",
            headers=counselor_headers,
            json={"target_state": "acknowledged", "notes": "got it"},
        )
        assert r.status_code == 200
        assert r.json["alert"]["triage_state"] == "acknowledged"

        with app.app_context():
            a = CounselorAlert.query.get(aid)
            assert a.triage_state == "acknowledged"
            assert a.acknowledged_by == "counselor-001"
            assert a.acknowledged_at is not None

    def test_illegal_transition_400(self, client, app, counselor_headers):
        aid = _seed_alert(app, state="resolved")
        r = client.post(
            f"/api/alerts/{aid}/triage",
            headers=counselor_headers,
            json={"target_state": "new"},
        )
        assert r.status_code == 400
        assert r.json["current"] == "resolved"
        assert r.json["target"] == "new"
        assert r.json["allowed_next"] == []

    def test_audit_row_created(self, client, app, counselor_headers):
        aid = _seed_alert(app)
        client.post(
            f"/api/alerts/{aid}/triage",
            headers=counselor_headers,
            json={"target_state": "escalated", "notes": "sent to psych"},
        )
        with app.app_context():
            rows = AlertAcknowledgment.query.filter_by(alert_id=aid).all()
            assert len(rows) == 1
            assert rows[0].action_taken == "new->escalated"
            assert rows[0].counselor_id == "counselor-001"
            assert rows[0].response_notes == "sent to psych"

    def test_escalated_can_resolve(self, client, app, counselor_headers):
        aid = _seed_alert(app, state="escalated")
        r = client.post(
            f"/api/alerts/{aid}/triage",
            headers=counselor_headers,
            json={"target_state": "resolved"},
        )
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/alerts/<id>/audit
# ---------------------------------------------------------------------------

class TestAudit:
    def test_requires_counselor_id(self, client):
        r = client.get("/api/alerts/1/audit")
        assert r.status_code == 401

    def test_404_on_missing(self, client, counselor_headers):
        r = client.get("/api/alerts/99999/audit", headers=counselor_headers)
        assert r.status_code == 404

    def test_empty_audit(self, client, app, counselor_headers):
        aid = _seed_alert(app)
        r = client.get(f"/api/alerts/{aid}/audit", headers=counselor_headers)
        assert r.status_code == 200
        assert r.json["audit"] == []

    def test_audit_ordered_asc(self, client, app, counselor_headers):
        aid = _seed_alert(app)
        # Transition through multiple states
        client.post(f"/api/alerts/{aid}/triage",
                    headers=counselor_headers,
                    json={"target_state": "acknowledged"})
        client.post(f"/api/alerts/{aid}/triage",
                    headers=counselor_headers,
                    json={"target_state": "resolved"})

        r = client.get(f"/api/alerts/{aid}/audit", headers=counselor_headers)
        actions = [row["action_taken"] for row in r.json["audit"]]
        assert actions == ["new->acknowledged", "acknowledged->resolved"]


# ---------------------------------------------------------------------------
# GET /api/alerts/history
# ---------------------------------------------------------------------------

class TestHistory:
    PATH = "/api/alerts/triage/history"

    def test_requires_counselor_id(self, client):
        r = client.get(self.PATH)
        assert r.status_code == 401

    def test_empty_history(self, client, counselor_headers):
        r = client.get(self.PATH, headers=counselor_headers)
        assert r.status_code == 200
        assert r.json["alerts"] == []

    def test_state_filter(self, client, app, counselor_headers):
        _seed_alert(app, state="new")
        _seed_alert(app, state="resolved")
        r = client.get(
            f"{self.PATH}?state=resolved",
            headers=counselor_headers,
        )
        assert len(r.json["alerts"]) == 1
        assert r.json["alerts"][0]["triage_state"] == "resolved"

    def test_severity_filter(self, client, app, counselor_headers):
        _seed_alert(app, severity="high")
        _seed_alert(app, severity="low")
        r = client.get(
            f"{self.PATH}?severity=low",
            headers=counselor_headers,
        )
        assert len(r.json["alerts"]) == 1
        assert r.json["alerts"][0]["severity"] == "low"

    def test_limit_capped_at_500(self, client, counselor_headers):
        r = client.get(
            f"{self.PATH}?limit=9999",
            headers=counselor_headers,
        )
        assert r.json["filters"]["limit"] == 500

    def test_since_invalid_400(self, client, counselor_headers):
        r = client.get(
            f"{self.PATH}?since=not-a-date",
            headers=counselor_headers,
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/alerts/stream (SSE)
# ---------------------------------------------------------------------------

class TestStream:
    def test_requires_counselor_id(self, client):
        r = client.get("/api/alerts/stream")
        assert r.status_code == 401

    def test_sse_content_type(self, client, counselor_headers):
        r = client.get("/api/alerts/stream", headers=counselor_headers)
        assert r.status_code == 200
        assert r.mimetype == "text/event-stream"

    def test_stream_emits_new_alerts(self, client, app, counselor_headers):
        _seed_alert(app)  # A new alert exists
        r = client.get("/api/alerts/stream", headers=counselor_headers)
        body = r.data.decode()
        # TESTING mode exits after one poll; should include the alert event
        assert "event: alert" in body
        assert "event: heartbeat" in body

    def test_no_new_alerts_still_heartbeats(self, client, counselor_headers):
        r = client.get("/api/alerts/stream", headers=counselor_headers)
        body = r.data.decode()
        assert "event: heartbeat" in body


# ---------------------------------------------------------------------------
# Registration smoke
# ---------------------------------------------------------------------------

class TestEndpointsRegistered:
    def test_all_four_registered(self, app):
        rules = {r.rule for r in app.url_map.iter_rules()}
        for expected in [
            "/api/alerts/<int:alert_id>/triage",
            "/api/alerts/<int:alert_id>/audit",
            "/api/alerts/triage/history",
            "/api/alerts/stream",
        ]:
            assert expected in rules, f"Missing: {expected}"
