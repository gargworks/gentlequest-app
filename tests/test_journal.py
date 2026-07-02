"""
JournalEntry — model-level tests + a route-removal regression guard.

v1.5.0 (docs/V1_5_0_ADHD_UPDATE_SCOPE.md, Workstream 3c) deleted
routes/journal.py and its blueprint registration so the app's on-screen
promise ("Stays on your device. Never synced. Never shared.") is true in
code — there is no longer a live /api/journal HTTP route. The old HTTP
round-trip tests that lived in this file were removed along with the route
they exercised.

The JournalEntry *model* is kept (see the comment on the class in
models.py) because routes/user_settings.py's GDPR export/delete-account
flows still read/delete rows here for any entries synced server-side
before the route was removed. The tests below exercise the model directly
(the only way journal rows can be written now) so that dependency stays
covered, and assert the HTTP route is actually gone so it can't silently
come back.
"""
import os
import sys
import uuid
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import JournalEntry, db


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


def _sid():
    return str(uuid.uuid4())


# ── Route removal (privacy-promise regression guard) ────────────────────


@pytest.mark.parametrize(
    "method,path,expected_status",
    [
        # GET falls through to Flask's static-file catch-all (this app
        # serves the Flutter web build from static_url_path=""), which
        # 404s because no such file exists — NOT a 200 with journal data.
        ("get", "/api/journal", 404),
        # Non-GET methods never reach the static catch-all either (it only
        # registers GET/HEAD), so routing itself rejects them with 405
        # before any view function runs.
        ("post", "/api/journal", 405),
        ("patch", "/api/journal/some-id", 405),
        ("delete", "/api/journal/some-id", 405),
    ],
)
def test_journal_http_routes_are_gone(client, method, path, expected_status):
    """No /api/journal route should exist — this is the actual mechanism
    that makes the "never synced" promise true. If this test starts
    failing (e.g. any of these starts returning 200/201 with journal-shaped
    JSON), someone re-registered the journal blueprint."""
    resp = getattr(client, method)(path, headers={"X-Session-ID": _sid()})
    assert resp.status_code == expected_status
    assert resp.status_code not in (200, 201)


# ── Model-level coverage (still used by user_settings GDPR export/delete) ──


def test_journal_entry_model_create_and_query(app):
    sid = _sid()
    with app.app_context():
        entry = JournalEntry(session_id=sid, body="first entry", title="Morning", mood_tag="good")
        db.session.add(entry)
        db.session.commit()

        fetched = JournalEntry.query.filter_by(session_id=sid, deleted_at=None).all()
        assert len(fetched) == 1
        assert fetched[0].body == "first entry"
        assert fetched[0].title == "Morning"
        assert fetched[0].mood_tag == "good"
        assert fetched[0].id  # server-assigned uuid default


def test_journal_entry_soft_delete_excludes_from_default_query(app):
    sid = _sid()
    with app.app_context():
        entry = JournalEntry(session_id=sid, body="delete me")
        db.session.add(entry)
        db.session.commit()
        entry.deleted_at = datetime.utcnow()
        db.session.commit()

        assert JournalEntry.query.filter_by(session_id=sid, deleted_at=None).count() == 0
        assert JournalEntry.query.filter_by(session_id=sid).count() == 1


def test_journal_entry_cascade_delete_by_session_id(app):
    """Mirrors routes/user_settings.py's account-deletion cascade
    (`JournalEntry.query.filter_by(session_id=session_id).delete(...)`) —
    the reason the model is kept post-route-removal."""
    sid = _sid()
    other_sid = _sid()
    with app.app_context():
        base = datetime.utcnow() - timedelta(minutes=5)
        for i in range(3):
            db.session.add(JournalEntry(session_id=sid, body=f"entry {i}", created_at=base + timedelta(minutes=i)))
        db.session.add(JournalEntry(session_id=other_sid, body="not mine"))
        db.session.commit()

        JournalEntry.query.filter_by(session_id=sid).delete(synchronize_session=False)
        db.session.commit()

        assert JournalEntry.query.filter_by(session_id=sid).count() == 0
        assert JournalEntry.query.filter_by(session_id=other_sid).count() == 1
