"""Funnel endpoint tests — GentleQuest Qualified Activation Proof (Slice A, Task 6).

Covers GET /api/metrics/funnel endpoint, checking schema, counts, rates,
bot filtering, and divide-by-zero behavior.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import AnalyticsEvent, FunnelSnapshot, db


def _sync_submit(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except Exception:
        pass
    from concurrent.futures import Future

    fut = Future()
    fut.set_result(None)
    return fut


@pytest.fixture
def app():
    """Create an in-memory test application with synchronous background execution."""
    os.environ["PYTEST_CURRENT_TEST"] = "true"
    application = create_app()
    application.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key",
            "RATE_LIMIT_ENABLED": False,
        }
    )

    with application.app_context():
        db.create_all()
        with patch(
            "helpers.session_helpers.background_executor.submit",
            new=_sync_submit,
        ):
            yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


class TestFunnelEndpoint:
    """Test GET /api/metrics/funnel."""

    def test_empty_funnel_returns_200_and_zero_rates(self, client):
        resp = client.get("/api/metrics/funnel")
        assert resp.status_code == 200
        data = resp.get_json()

        assert "window" in data
        assert "start" in data["window"]
        assert "end" in data["window"]

        assert "counts" in data
        counts = data["counts"]
        required_keys = [
            "landing_sessions",
            "cta_clicks",
            "web_app_opens",
            "compliance_passed",
            "first_value_actions",
            "returning_users",
        ]
        for key in required_keys:
            assert key in counts, f"Missing count key {key!r}"
            assert counts[key] == 0

        assert "cta_ctr" in data
        assert data["cta_ctr"] == 0.0
        assert "first_value_conversion" in data
        assert data["first_value_conversion"] == 0.0

    def test_funnel_counts_and_bot_filtering(self, app, client):
        now = datetime.utcnow()
        with app.app_context():
            # Qualified human session s1: landing -> click -> open -> compliance -> first value
            db.session.add(
                AnalyticsEvent(
                    session_id="s1",
                    event_type="cta_impression",
                    timestamp=now,
                    event_metadata={"landing_path": "/", "_ua_class": "human"},
                )
            )
            db.session.add(
                AnalyticsEvent(
                    session_id="s1",
                    event_type="cta_click",
                    timestamp=now + timedelta(seconds=5),
                    event_metadata={"cta_id": "hero", "_ua_class": "human"},
                )
            )
            db.session.add(
                AnalyticsEvent(
                    session_id="s1",
                    event_type="web_app_open_from_cta",
                    timestamp=now + timedelta(seconds=10),
                    event_metadata={"source_cta": "hero", "_ua_class": "human"},
                )
            )
            db.session.add(
                AnalyticsEvent(
                    session_id="s1",
                    event_type="compliance_passed",
                    timestamp=now + timedelta(seconds=15),
                    event_metadata={"_ua_class": "human"},
                )
            )
            db.session.add(
                AnalyticsEvent(
                    session_id="s1",
                    event_type="first_chat_message",
                    timestamp=now + timedelta(seconds=20),
                    event_metadata={"_ua_class": "human"},
                )
            )

            # Bot session s2 (Googlebot): landing + click (should be excluded by bot filter)
            db.session.add(
                AnalyticsEvent(
                    session_id="s2",
                    event_type="cta_impression",
                    timestamp=now,
                    event_metadata={"_ua_class": "bot"},
                )
            )
            db.session.add(
                AnalyticsEvent(
                    session_id="s2",
                    event_type="cta_click",
                    timestamp=now + timedelta(seconds=1),
                    event_metadata={"_ua_class": "bot"},
                )
            )

            db.session.commit()

        resp = client.get("/api/metrics/funnel")
        assert resp.status_code == 200
        data = resp.get_json()

        counts = data["counts"]
        assert counts["landing_sessions"] == 1  # s1 included, s2 excluded
        assert counts["cta_clicks"] == 1
        assert counts["web_app_opens"] == 1
        assert counts["compliance_passed"] == 1
        assert counts["first_value_actions"] == 1
        assert counts["returning_users"] == 0

        assert data["cta_ctr"] == 1.0
        assert data["first_value_conversion"] == 1.0

    def test_returning_user_count(self, app, client):
        now = datetime.utcnow()
        with app.app_context():
            # Qualified human session s_ret: first visit now, second visit 25 hours later
            db.session.add(
                AnalyticsEvent(
                    session_id="s_ret",
                    event_type="cta_impression",
                    timestamp=now,
                    event_metadata={"_ua_class": "human"},
                )
            )
            db.session.add(
                AnalyticsEvent(
                    session_id="s_ret",
                    event_type="first_chat_message",
                    timestamp=now + timedelta(hours=25),
                    event_metadata={"_ua_class": "human"},
                )
            )
            db.session.commit()

        resp = client.get("/api/metrics/funnel")
        assert resp.status_code == 200
        data = resp.get_json()

        assert data["counts"]["landing_sessions"] == 1
        assert data["counts"]["first_value_actions"] == 1
        assert data["counts"]["returning_users"] == 1


class TestFunnelHistoryEndpoint:
    """Tests for GET /api/metrics/funnel/history freshness metadata."""

    def test_empty_history_freshness_empty(self, client):
        resp = client.get("/api/metrics/funnel/history?limit=1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 0
        assert data["freshness"]["status"] == "empty"
        assert data["freshness"]["latest_created_at"] is None
        assert data["freshness"]["retention_gate_status"] is None

    def test_recent_history_freshness_ok(self, app, client):
        with app.app_context():
            snapshot = FunnelSnapshot(
                snapshot_data={
                    "counts": {"landing_sessions": 1},
                    "retention_gate": {"status": "insufficient", "reason": "not_mature"},
                },
                created_at=datetime.utcnow(),
            )
            db.session.add(snapshot)
            db.session.commit()

        resp = client.get("/api/metrics/funnel/history?limit=1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 1
        assert data["freshness"]["status"] == "ok"
        assert data["freshness"]["retention_gate_status"] == "insufficient"

    def test_old_history_freshness_stale(self, app, client):
        with app.app_context():
            snapshot = FunnelSnapshot(
                snapshot_data={"counts": {"landing_sessions": 1}},
                created_at=datetime.utcnow() - timedelta(hours=48),
            )
            db.session.add(snapshot)
            db.session.commit()

        resp = client.get("/api/metrics/funnel/history?limit=1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 1
        assert data["freshness"]["status"] == "stale"
        assert data["freshness"]["retention_gate_status"] == "missing"

    def test_retention_gate_error_status(self, app, client):
        with app.app_context():
            snapshot = FunnelSnapshot(
                snapshot_data={
                    "counts": {"landing_sessions": 1},
                    "retention_gate": {"status": "error", "reason": "authentication_failed"},
                },
                created_at=datetime.utcnow(),
            )
            db.session.add(snapshot)
            db.session.commit()

        resp = client.get("/api/metrics/funnel/history?limit=1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["freshness"]["status"] == "ok"
        assert data["freshness"]["retention_gate_status"] == "error"


class TestUaClassification:
    """The 2026-09-03 fix: the funnel's bot filter was dead by construction.

    The reader took the UA from event metadata, but /api/analytics/log strips
    user_agent from metadata via its allowlist — so the UA was ALWAYS absent
    and the reader substituted DEFAULT_UA, a hardcoded desktop-Chrome string.
    A working filter, handed the same synthetic human for every session.

    Note the old test above passed only because it wrote user_agent straight
    into the model, a door production does not have. It proved the filter
    worked on inputs production could never produce.
    """

    def test_real_ua_is_classified_server_side(self, client, app):
        """A browser UA on the request is recorded as human — the writer's job."""
        resp = client.post(
            "/api/analytics/log",
            json={"event_type": "cta_impression", "metadata": {"cta_id": "hero"}},
            headers={
                "X-Analytics-Consent": "true",
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
            },
        )
        assert resp.status_code == 201
        with app.app_context():
            from models import AnalyticsEvent

            ev = AnalyticsEvent.query.filter_by(event_type="cta_impression").first()
            assert ev is not None
            assert ev.event_metadata.get("_ua_class") == "human"

    def test_bot_ua_is_classified_as_bot(self, client, app):
        """The opposed half. Without this, "human" could be a constant."""
        resp = client.post(
            "/api/analytics/log",
            json={"event_type": "cta_impression", "metadata": {"cta_id": "hero"}},
            headers={
                "X-Analytics-Consent": "true",
                "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; "
                              "+http://www.google.com/bot.html)",
            },
        )
        assert resp.status_code == 201
        with app.app_context():
            from models import AnalyticsEvent

            ev = AnalyticsEvent.query.filter_by(event_type="cta_impression").first()
            assert ev.event_metadata.get("_ua_class") == "bot"

    def test_client_cannot_forge_the_classification(self, client, app):
        """A crawler declaring itself human must not be believed.

        _ua_class is set AFTER the metadata allowlist, so a client-supplied
        value is discarded. If this ever fails, the filter is worthless: any
        bot bypasses it by sending one extra JSON key.
        """
        resp = client.post(
            "/api/analytics/log",
            json={
                "event_type": "cta_impression",
                "metadata": {"cta_id": "hero", "_ua_class": "human"},
            },
            headers={
                "X-Analytics-Consent": "true",
                "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)",
            },
        )
        assert resp.status_code == 201
        with app.app_context():
            from models import AnalyticsEvent

            ev = AnalyticsEvent.query.filter_by(event_type="cta_impression").first()
            assert ev.event_metadata.get("_ua_class") == "bot"

    def test_legacy_sessions_are_unclassified_not_counted(self, client, app):
        """Pre-fix events are reported as UNKNOWN, never as a quiet zero.

        We genuinely do not know whether those sessions were human. Folding
        them into either bucket would repeat the mistake being corrected, so
        they surface as unclassified_sessions + insufficient_data.
        """
        with app.app_context():
            from models import UserSession

            sid = "legacy-session-no-ua-class"
            db.session.add(UserSession(id=sid))
            db.session.add(
                AnalyticsEvent(
                    session_id=sid,
                    event_type="cta_impression",
                    event_metadata={"landing_path": "/"},  # no _ua_class
                )
            )
            db.session.commit()

        data = client.get("/api/metrics/funnel").get_json()
        assert data["counts"]["landing_sessions"] == 0
        assert data["counts"]["unclassified_sessions"] == 1
        assert data["insufficient_data"] is True
