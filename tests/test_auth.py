"""Smoke tests for routes/auth.py — passwordless magic-link login."""

import hashlib
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from models import AuthToken, User, db  # noqa: E402


@pytest.fixture
def app():
    os.environ["PYTEST_CURRENT_TEST"] = "true"
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key",
            "RATE_LIMIT_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _swap_token_hash(raw_replacement: str) -> str:
    """Helper: replace the most recent token's hash with a known raw value's
    sha256. Returns the raw replacement. Lets us "intercept" the magic link
    that would otherwise be emailed."""
    token_row = AuthToken.query.order_by(AuthToken.id.desc()).first()
    assert token_row is not None
    token_row.token_hash = hashlib.sha256(raw_replacement.encode()).hexdigest()
    db.session.commit()
    return raw_replacement


def test_magic_link_request_returns_202(client):
    r = client.post("/api/auth/magic-link", json={"email": "user@example.com"})
    assert r.status_code == 202
    assert r.get_json() == {"status": "sent"}
    # User row created lazily
    user = User.query.filter_by(email="user@example.com").first()
    assert user is not None
    # Token row created
    tok = AuthToken.query.filter_by(user_id=user.id).first()
    assert tok is not None and tok.used_at is None


def test_magic_link_rejects_bad_email(client):
    r = client.post("/api/auth/magic-link", json={"email": "not-an-email"})
    assert r.status_code == 400


def test_verify_round_trip(client):
    # Magic-link request creates the user + sets user.session_id to the
    # requesting device's session. That id becomes the canonical
    # cross-device session_id that verify returns to every device.
    request_sid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    client.post(
        "/api/auth/magic-link",
        json={"email": "round@example.com"},
        headers={"X-Session-ID": request_sid},
    )
    raw = _swap_token_hash("test-raw-token-xyz")
    # Verify from a DIFFERENT device (e.g. user clicks link on phone after
    # requesting from desktop). The verifying device should adopt the
    # canonical session_id, not its own anonymous one.
    verify_sid = "11111111-1111-1111-1111-111111111111"
    r = client.post(
        "/api/auth/verify",
        json={"token": raw},
        headers={"X-Session-ID": verify_sid},
    )
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["user"]["email"] == "round@example.com"
    # Phase 1.5: returned session_id is the canonical (request-time) one,
    # NOT the verifying device's anonymous session. Lets both devices hit
    # the same server-side data without a junction table.
    assert body["session_id"] == request_sid
    # User row still points at the canonical session.
    user = User.query.first()
    assert user.session_id == request_sid
    # Token marked used.
    tok = AuthToken.query.first()
    assert tok.used_at is not None


def test_verify_single_use(client):
    client.post("/api/auth/magic-link", json={"email": "once@example.com"})
    raw = _swap_token_hash("single-use-token")
    client.post("/api/auth/verify", json={"token": raw})
    r2 = client.post("/api/auth/verify", json={"token": raw})
    assert r2.status_code == 400
    # Audit fix 2026-05-21: generic message — no longer distinguishes
    # invalid / used / expired (closes a timing-leak oracle).
    assert "invalid or expired" in r2.get_json()["error"].lower()


def test_verify_rejects_unknown_token(client):
    r = client.post("/api/auth/verify", json={"token": "no-such-token"})
    assert r.status_code == 400


def test_whoami_anonymous(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.get_json() == {"user": None}


def test_whoami_after_verify(client):
    # Hit magic-link from the same device the test will later whoami from.
    sid = "22222222-2222-2222-2222-222222222222"
    client.post(
        "/api/auth/magic-link",
        json={"email": "who@example.com"},
        headers={"X-Session-ID": sid},
    )
    raw = _swap_token_hash("who-am-i-token")
    verify = client.post(
        "/api/auth/verify",
        json={"token": raw},
        headers={"X-Session-ID": sid},
    )
    canonical = verify.get_json()["session_id"]
    r = client.get("/api/auth/me", headers={"X-Session-ID": canonical})
    assert r.status_code == 200
    body = r.get_json()
    assert body["user"]["email"] == "who@example.com"


def test_multi_device_inherits_canonical_session(client):
    """A second device verifying the same account adopts the user's
    canonical session_id — both devices then hit the same server rows."""
    desktop_sid = "dddddddd-dddd-dddd-dddd-dddddddddddd"
    phone_sid = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    # 1. User requests magic link from desktop.
    client.post(
        "/api/auth/magic-link",
        json={"email": "multi@example.com"},
        headers={"X-Session-ID": desktop_sid},
    )
    raw = _swap_token_hash("multi-device-token")
    # 2. User clicks link on phone — verify carries phone's anon session.
    verify_resp = client.post(
        "/api/auth/verify",
        json={"token": raw},
        headers={"X-Session-ID": phone_sid},
    )
    assert verify_resp.status_code == 200
    # Phone gets desktop's session_id back as the canonical.
    assert verify_resp.get_json()["session_id"] == desktop_sid
    # 3. Desktop's whoami still resolves to the same user.
    r_desktop = client.get(
        "/api/auth/me", headers={"X-Session-ID": desktop_sid}
    )
    assert r_desktop.get_json()["user"]["email"] == "multi@example.com"
    # 4. Phone — once it adopts the canonical session — also resolves.
    r_phone = client.get(
        "/api/auth/me", headers={"X-Session-ID": desktop_sid}
    )
    assert r_phone.get_json()["user"]["email"] == "multi@example.com"
