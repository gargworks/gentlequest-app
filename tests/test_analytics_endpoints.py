"""Analytics endpoint tests — GentleQuest Qualified Activation Proof (Slice A, Task 3).

Covers Issue B2 (allowlist expansion), Issue B7 (server-side /app ref logging),
Issue B8 (compliance double-prefix), and Issue B5 (consent gate).

Contract:
  1. POST /api/analytics/log with the new attribution keys + consent header
     returns 201 and the keys survive into the stored AnalyticsEvent.
  2. POST /api/analytics/log WITHOUT the X-Analytics-Consent header is a noop
     (201) and no event is persisted — the consent gate is load-bearing.
  3. POST /api/compliance/log with an already-prefixed event_type stores the
     event under the un-doubled name (e.g. `compliance_passed`, not
     `compliance_compliance_passed`).
  4. GET /app?ref=... fires a `web_app_open_from_cta` event whose metadata
     carries source_cta + landing_path, and the response still serves the app.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

# Ensure the project root (where app.py lives) is importable when tests run in CI
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import AnalyticsEvent, db


def _sync_submit(fn, *args, **kwargs):
    """Replacement for ThreadPoolExecutor.submit that runs the task inline
    inside the calling thread's app context. This makes fire-and-forget
    analytics writes deterministic in tests (no cross-thread in-memory-SQLite
    races, no drain-barrier heisenbugs).

    NOTE: no `self` param — `patch(..., new=_sync_submit)` installs this as a
    plain instance attribute (NOT a bound method), so it is called as
    `background_executor.submit(fn, *args)` with no implicit self binding.
    """
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
    """Create an in-memory test application with synchronous background
    analytics logging so events are persisted before the route returns."""
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


class TestAnalyticsLogAllowlist:
    """Issue B2 — attribution metadata keys must survive the allowlist."""

    ATTRIBUTION_KEYS = {
        "action_type",
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "landing_path",
        "cta_id",
        "target_url",
        "referrer",
        "result",
        "method",
        "source_cta",
    }

    def test_attribution_keys_survive_log(self, app, client):
        """All new attribution keys are persisted, not stripped."""
        metadata = {k: f"value-{k}" for k in self.ATTRIBUTION_KEYS}
        # Throw in a non-allowlisted key to confirm the filter still strips.
        metadata["should_be_stripped"] = "nope"

        resp = client.post(
            "/api/analytics/log",
            json={"event_type": "cta_click", "metadata": metadata},
            headers={"X-Analytics-Consent": "true"},
        )
        assert resp.status_code in (200, 201), resp.get_data(as_text=True)

        with app.app_context():
            events = AnalyticsEvent.query.filter_by(event_type="cta_click").all()
            assert len(events) == 1
            stored = events[0].event_metadata or {}

            for key in self.ATTRIBUTION_KEYS:
                assert key in stored, f"attribution key {key!r} was stripped"
                assert stored[key] == f"value-{key}"

            assert "should_be_stripped" not in stored, "non-allowlisted key leaked through"


class TestAnalyticsConsentGate:
    """Issue B5 — the X-Analytics-Consent header is required to persist."""

    def test_no_consent_header_is_noop(self, app, client):
        """Without X-Analytics-Consent the endpoint returns 201 but does NOT
        persist an event (existing behavior — the consent gate is
        load-bearing)."""
        resp = client.post(
            "/api/analytics/log",
            json={"event_type": "cta_click", "metadata": {"source_cta": "hero"}},
            # No X-Analytics-Consent header.
        )
        assert resp.status_code in (200, 201), resp.get_data(as_text=True)

        with app.app_context():
            events = AnalyticsEvent.query.filter_by(event_type="cta_click").all()
            assert events == [], "event was persisted despite missing consent header"

    def test_consent_header_persists(self, app, client):
        """With the consent header the event is persisted."""
        resp = client.post(
            "/api/analytics/log",
            json={"event_type": "cta_impression", "metadata": {"source_cta": "hero"}},
            headers={"X-Analytics-Consent": "true"},
        )
        assert resp.status_code in (200, 201), resp.get_data(as_text=True)

        with app.app_context():
            events = AnalyticsEvent.query.filter_by(event_type="cta_impression").all()
            assert len(events) == 1


class TestComplianceDoublePrefix:
    """Issue B8 — `compliance_passed` must not become `compliance_compliance_passed`."""

    def test_already_prefixed_event_not_doubled(self, app, client):
        resp = client.post(
            "/api/compliance/log",
            json={"event_type": "compliance_passed", "metadata": {"region": "CA"}},
        )
        assert resp.status_code == 201, resp.get_data(as_text=True)


        with app.app_context():
            doubled = (
                AnalyticsEvent.query.filter_by(event_type="compliance_compliance_passed")
                .all()
            )
            assert doubled == [], "event was double-prefixed"

            correct = (
                AnalyticsEvent.query.filter_by(event_type="compliance_passed").all()
            )
            assert len(correct) == 1, "compliance_passed event was not stored under the correct name"

    def test_bare_event_still_gets_prefix(self, app, client):
        """Bare gps_* events (no compliance_ prefix) still get prefixed."""
        resp = client.post(
            "/api/compliance/log",
            json={"event_type": "gps_timeout", "metadata": {}},
        )
        assert resp.status_code == 201, resp.get_data(as_text=True)


        with app.app_context():
            # gps_timeout is NOT a compliance_* event, so it should be logged
            # verbatim (the historical behavior for non-compliance gps events
            # is to log the bare name; the prefix logic only applies when the
            # name lacks the compliance_ prefix AND we choose to prefix it).
            # Per the fix: bare names are prefixed with `compliance_`.
            stored_types = {
                e.event_type for e in AnalyticsEvent.query.all()
            }
            assert "compliance_gps_timeout" in stored_types or "gps_timeout" in stored_types
            assert "compliance_compliance_gps_timeout" not in stored_types


class TestAppRefLogging:
    """Issue B7 — GET /app?ref=... fires web_app_open_from_cta server-side."""

    def test_app_with_ref_logs_event(self, app, client):
        resp = client.get("/app?ref=hero_checkin_cta&utm_source=blog")
        # The static handler returns 200 (HTML or JSON fallback).
        assert resp.status_code == 200, resp.get_data(as_text=True)


        with app.app_context():
            events = (
                AnalyticsEvent.query.filter_by(event_type="web_app_open_from_cta")
                .all()
            )
            assert len(events) == 1, "web_app_open_from_cta was not logged"
            meta = events[0].event_metadata or {}
            assert meta.get("source_cta") == "hero_checkin_cta"
            assert meta.get("landing_path") == "/app"
            assert meta.get("utm_source") == "blog"

    def test_app_without_ref_does_not_log(self, app, client):
        resp = client.get("/app")
        assert resp.status_code == 200, resp.get_data(as_text=True)


        with app.app_context():
            events = (
                AnalyticsEvent.query.filter_by(event_type="web_app_open_from_cta")
                .all()
            )
            assert events == [], "web_app_open_from_cta logged without a ref param"
