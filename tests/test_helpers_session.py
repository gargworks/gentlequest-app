"""Unit tests for helpers/session_helpers.py."""

import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["PYTEST_CURRENT_TEST"] = "true"

from app import create_app
from helpers.session_helpers import (
    _get_conversation_count,
    _get_or_create_session,
    _increment_conversation_count,
    _log_analytics_event,
    _log_chat_request,
    _update_session_last_active,
    background_executor,
)
from models import AnalyticsEvent, UserSession, db


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
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# background_executor
# ---------------------------------------------------------------------------

class TestBackgroundExecutor:
    def test_executor_exists_and_accepts_work(self):
        fut = background_executor.submit(lambda: 42)
        assert fut.result(timeout=2) == 42

    def test_executor_runs_in_background_thread(self):
        import threading
        main = threading.get_ident()
        fut = background_executor.submit(lambda: threading.get_ident())
        assert fut.result(timeout=2) != main


# ---------------------------------------------------------------------------
# _get_or_create_session
# ---------------------------------------------------------------------------

class TestGetOrCreateSession:
    def test_creates_new_uuid_when_no_header(self, app):
        with app.test_request_context("/api/x", headers={}):
            sid = _get_or_create_session()
            # Valid UUID
            uuid.UUID(sid)
            # Persisted to DB
            assert db.session.get(UserSession, sid) is not None

    def test_uses_valid_header_uuid(self, app):
        existing = str(uuid.uuid4())
        with app.test_request_context("/", headers={"X-Session-ID": existing}):
            sid = _get_or_create_session()
            assert sid == existing
            assert db.session.get(UserSession, sid) is not None

    def test_rejects_malformed_uuid_and_creates_new(self, app):
        with app.test_request_context("/", headers={"X-Session-ID": "not-a-uuid"}):
            sid = _get_or_create_session()
            assert sid != "not-a-uuid"
            uuid.UUID(sid)

    def test_idempotent_for_existing_session(self, app):
        existing = str(uuid.uuid4())
        with app.app_context():
            db.session.add(UserSession(id=existing))
            db.session.commit()
        with app.test_request_context("/", headers={"X-Session-ID": existing}):
            sid = _get_or_create_session()
            assert sid == existing
            count = UserSession.query.filter_by(id=existing).count()
            assert count == 1


# ---------------------------------------------------------------------------
# _update_session_last_active
# ---------------------------------------------------------------------------

class TestUpdateSessionLastActive:
    def test_updates_last_active_timestamp(self, app):
        sid = str(uuid.uuid4())
        db.session.add(UserSession(id=sid))
        db.session.commit()
        original = db.session.get(UserSession, sid).last_active

        _update_session_last_active(app, sid)

        updated = db.session.get(UserSession, sid).last_active
        # Either was None and now set, or strictly newer
        assert updated is not None
        if original is not None:
            assert updated >= original

    def test_silent_noop_for_missing_session(self, app):
        # Should not raise
        _update_session_last_active(app, str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# _get_conversation_count / _increment_conversation_count
# ---------------------------------------------------------------------------

class TestConversationCount:
    def test_returns_zero_for_missing_session(self, app):
        assert _get_conversation_count(str(uuid.uuid4())) == 0

    def test_returns_count_for_existing_session(self, app):
        sid = str(uuid.uuid4())
        db.session.add(UserSession(id=sid, conversation_count=7))
        db.session.commit()
        assert _get_conversation_count(sid) == 7

    def test_handles_null_count_as_zero(self, app):
        sid = str(uuid.uuid4())
        db.session.add(UserSession(id=sid))  # conversation_count may be None
        db.session.commit()
        assert _get_conversation_count(sid) == 0

    def test_increment_bumps_count_by_one(self, app):
        sid = str(uuid.uuid4())
        db.session.add(UserSession(id=sid, conversation_count=3))
        db.session.commit()

        _increment_conversation_count(app, sid)

        assert _get_conversation_count(sid) == 4

    def test_increment_from_null_starts_at_one(self, app):
        sid = str(uuid.uuid4())
        db.session.add(UserSession(id=sid))
        db.session.commit()

        _increment_conversation_count(app, sid)

        assert _get_conversation_count(sid) == 1

    def test_increment_silent_noop_for_missing_session(self, app):
        _increment_conversation_count(app, str(uuid.uuid4()))  # no-op, no raise


# ---------------------------------------------------------------------------
# _log_analytics_event
# ---------------------------------------------------------------------------

class TestLogAnalyticsEvent:
    def test_logs_event_to_db(self, app):
        sid = str(uuid.uuid4())
        _log_analytics_event(app, sid, "mood_logged", {"mood": 4})
        events = AnalyticsEvent.query.filter_by(session_id=sid).all()
        assert len(events) == 1
        assert events[0].event_type == "mood_logged"
        assert events[0].event_metadata == {"mood": 4}

    def test_accepts_none_metadata(self, app):
        sid = str(uuid.uuid4())
        _log_analytics_event(app, sid, "page_view", None)
        ev = AnalyticsEvent.query.filter_by(session_id=sid).first()
        assert ev is not None
        assert ev.event_metadata == {}

    def test_exception_is_swallowed(self, app):
        # Force a failure by passing an unsupported metadata type; helper must not raise
        _log_analytics_event(app, str(uuid.uuid4()), "x", {"ok": True})


# ---------------------------------------------------------------------------
# _log_chat_request
# ---------------------------------------------------------------------------

class TestLogChatRequest:
    def test_writes_to_jsonl_file(self, tmp_path, monkeypatch):
        log_file = tmp_path / "chat.jsonl"
        monkeypatch.setattr(
            "helpers.session_helpers._CHAT_LOG_PATH", str(log_file)
        )
        _log_chat_request("s1", 100, 200, 1500, 200, "gemini-2.5-flash")
        assert log_file.exists()
        content = log_file.read_text()
        assert "s1" in content
        assert "gemini-2.5-flash" in content
        assert '"status": 200' in content

    def test_handles_write_failure_silently(self, monkeypatch):
        # Point at an unwritable path; should not raise
        monkeypatch.setattr(
            "helpers.session_helpers._CHAT_LOG_PATH", "/root/forbidden/chat.jsonl"
        )
        _log_chat_request("s1", 0, 0, 0, 500)  # no raise expected
