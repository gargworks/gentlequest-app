import os
import sys
import uuid
from datetime import date, datetime, timedelta
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import AnalyticsEvent, PushToken, UserSession, db
from services import retention_nudge


@pytest.fixture
def app(monkeypatch):
    os.environ["PYTEST_CURRENT_TEST"] = "true"
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
        "RATE_LIMIT_ENABLED": False,
        "SQLALCHEMY_EXPIRE_ON_COMMIT": False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _sid():
    return str(uuid.uuid4())


def _make_session(session_id, first_open_days_ago, last_event_days_ago=None, with_token=True):
    """A session whose earliest analytics_events row is first_open_days_ago
    in the past, with an optional more-recent event (default: same as
    first_open, i.e. never returned)."""
    db.session.add(UserSession(id=session_id))
    first_open_ts = datetime.utcnow() - timedelta(days=first_open_days_ago)
    db.session.add(AnalyticsEvent(session_id=session_id, event_type="chat_session_started", timestamp=first_open_ts))
    if last_event_days_ago is not None:
        last_ts = datetime.utcnow() - timedelta(days=last_event_days_ago)
        db.session.add(AnalyticsEvent(session_id=session_id, event_type="chat_message_sent", timestamp=last_ts))
    if with_token:
        db.session.add(PushToken(session_id=session_id, token=f"tok-{session_id}", platform="ios"))
    db.session.commit()


def test_cohort_matches_exactly_day_10_sessions(app):
    with app.app_context():
        day10 = _sid()
        day9 = _sid()
        day11 = _sid()
        _make_session(day10, first_open_days_ago=10)
        _make_session(day9, first_open_days_ago=9)
        _make_session(day11, first_open_days_ago=11)

        cohort = retention_nudge._d10_cohort_session_ids(datetime.utcnow().date() - timedelta(days=10))

        assert day10 in cohort
        assert day9 not in cohort
        assert day11 not in cohort


def test_recently_active_sessions_are_excluded_from_the_nudge(app):
    """A session that first-opened 10 days ago but has ALSO been active in
    the last 3 days is still engaged -- nudging them is pointless and the
    query must exclude them."""
    with app.app_context():
        still_active = _sid()
        gone_quiet = _sid()
        _make_session(still_active, first_open_days_ago=10, last_event_days_ago=1)
        _make_session(gone_quiet, first_open_days_ago=10, last_event_days_ago=10)

        cohort = retention_nudge._d10_cohort_session_ids(datetime.utcnow().date() - timedelta(days=10))

        assert gone_quiet in cohort
        assert still_active not in cohort


def test_send_d10_nudges_sends_only_to_sessions_with_a_valid_token(app):
    with app.app_context():
        has_token = _sid()
        no_token = _sid()
        _make_session(has_token, first_open_days_ago=10, with_token=True)
        _make_session(no_token, first_open_days_ago=10, with_token=False)

        with patch("services.retention_nudge.send_push", return_value={"sent": 1, "failed": [], "skipped": []}) as mock_send:
            result = retention_nudge.send_d10_nudges(target_date=datetime.utcnow().date() - timedelta(days=10))

        assert result["cohort_size"] == 2
        assert result["sent"] == 1
        assert result["skipped"] == 1
        mock_send.assert_called_once()
        called_sid = mock_send.call_args.args[0]
        assert called_sid == has_token


def test_send_d10_nudges_uses_the_gentle_return_category_and_no_guilt_copy(app):
    with app.app_context():
        sid = _sid()
        _make_session(sid, first_open_days_ago=10, with_token=True)

        with patch("services.retention_nudge.send_push", return_value={"sent": 1, "failed": [], "skipped": []}) as mock_send:
            retention_nudge.send_d10_nudges(target_date=datetime.utcnow().date() - timedelta(days=10))

        args, kwargs = mock_send.call_args
        assert args[0] == sid
        assert args[1] == retention_nudge.NUDGE_TITLE
        assert args[2] == retention_nudge.NUDGE_BODY
        assert kwargs["category"] == "gentle_return"
        # No streak/guilt language anywhere in the copy -- brand invariant.
        assert "streak" not in args[2].lower() or "no streak" in args[2].lower()
        assert "miss" not in args[1].lower() and "miss" not in args[2].lower()


def test_send_d10_nudges_with_empty_cohort_is_a_clean_noop(app):
    with app.app_context():
        result = retention_nudge.send_d10_nudges(target_date=datetime.utcnow().date() - timedelta(days=10))
        assert result == {"cohort_size": 0, "sent": 0, "skipped": 0, "failed": 0}
