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
from models import AnalyticsEvent, db


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
                    event_metadata={"landing_path": "/"},
                )
            )
            db.session.add(
                AnalyticsEvent(
                    session_id="s1",
                    event_type="cta_click",
                    timestamp=now + timedelta(seconds=5),
                    event_metadata={"cta_id": "hero"},
                )
            )
            db.session.add(
                AnalyticsEvent(
                    session_id="s1",
                    event_type="web_app_open_from_cta",
                    timestamp=now + timedelta(seconds=10),
                    event_metadata={"source_cta": "hero"},
                )
            )
            db.session.add(
                AnalyticsEvent(
                    session_id="s1",
                    event_type="compliance_passed",
                    timestamp=now + timedelta(seconds=15),
                    event_metadata={},
                )
            )
            db.session.add(
                AnalyticsEvent(
                    session_id="s1",
                    event_type="first_chat_message",
                    timestamp=now + timedelta(seconds=20),
                    event_metadata={},
                )
            )

            # Bot session s2 (Googlebot): landing + click (should be excluded by bot filter)
            db.session.add(
                AnalyticsEvent(
                    session_id="s2",
                    event_type="cta_impression",
                    timestamp=now,
                    event_metadata={"user_agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"},
                )
            )
            db.session.add(
                AnalyticsEvent(
                    session_id="s2",
                    event_type="cta_click",
                    timestamp=now + timedelta(seconds=1),
                    event_metadata={"user_agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"},
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
                    event_metadata={},
                )
            )
            db.session.add(
                AnalyticsEvent(
                    session_id="s_ret",
                    event_type="first_chat_message",
                    timestamp=now + timedelta(hours=25),
                    event_metadata={},
                )
            )
            db.session.commit()

        resp = client.get("/api/metrics/funnel")
        assert resp.status_code == 200
        data = resp.get_json()

        assert data["counts"]["landing_sessions"] == 1
        assert data["counts"]["first_value_actions"] == 1
        assert data["counts"]["returning_users"] == 1
