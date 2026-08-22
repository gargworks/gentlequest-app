"""Tests for the daily funnel scheduler and retention-gate attachment."""

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import FunnelSnapshot, db


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


class TestFunnelScheduler:
    def test_snapshot_persists_funnel_and_retention_gate(self, app):
        from scheduler import funnel_scheduler

        fake_gate = {
            "schema_version": 1,
            "status": "insufficient",
            "reason": "not_mature",
            "native": {"total_n": 12, "d14": {"eligible_n": 0, "returned": 0, "rate": 0.0}},
        }

        with patch.object(
            funnel_scheduler, "_schedule_next"
        ), patch.object(
            funnel_scheduler, "collect_native_retention_gate", return_value=fake_gate
        ):
            funnel_scheduler._run_snapshot(app)

        with app.app_context():
            snapshots = FunnelSnapshot.query.all()
            assert len(snapshots) == 1
            snapshot_data = snapshots[0].snapshot_data
            assert "counts" in snapshot_data
            assert snapshot_data.get("retention_gate") == fake_gate

    def test_snapshot_persists_despite_retention_error(self, app):
        from scheduler import funnel_scheduler

        with patch.object(
            funnel_scheduler, "_schedule_next"
        ), patch.object(
            funnel_scheduler, "collect_native_retention_gate", side_effect=RuntimeError("boom")
        ):
            funnel_scheduler._run_snapshot(app)

        with app.app_context():
            snapshots = FunnelSnapshot.query.all()
            assert len(snapshots) == 1
            snapshot_data = snapshots[0].snapshot_data
            assert "counts" in snapshot_data
            rg = snapshot_data.get("retention_gate", {})
            assert rg.get("status") == "error"
            assert rg.get("reason") == "unexpected_error"

    def test_no_snapshot_when_funnel_endpoint_fails(self, app):
        from scheduler import funnel_scheduler
        from flask.testing import FlaskClient

        with patch.object(
            funnel_scheduler, "_schedule_next"
        ), patch.object(
            FlaskClient,
            "get",
            return_value=Mock(status_code=500, get_json=Mock(return_value=None)),
        ):
            funnel_scheduler._run_snapshot(app)

        with app.app_context():
            assert FunnelSnapshot.query.count() == 0
