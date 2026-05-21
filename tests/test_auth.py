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
    client.post("/api/auth/magic-link", json={"email": "round@example.com"})
    raw = _swap_token_hash("test-raw-token-xyz")
    r = client.post(
        "/api/auth/verify",
        json={"token": raw},
        headers={"X-Session-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["user"]["email"] == "round@example.com"
    assert body["session_id"] == "11111111-1111-1111-1111-111111111111"
    # Token marked used
    tok = AuthToken.query.first()
    assert tok.used_at is not None


def test_verify_single_use(client):
    client.post("/api/auth/magic-link", json={"email": "once@example.com"})
    raw = _swap_token_hash("single-use-token")
    client.post("/api/auth/verify", json={"token": raw})
    r2 = client.post("/api/auth/verify", json={"token": raw})
    assert r2.status_code == 400
    assert "used" in r2.get_json()["error"].lower()


def test_verify_rejects_unknown_token(client):
    r = client.post("/api/auth/verify", json={"token": "no-such-token"})
    assert r.status_code == 400


def test_whoami_anonymous(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.get_json() == {"user": None}


def test_whoami_after_verify(client):
    client.post("/api/auth/magic-link", json={"email": "who@example.com"})
    raw = _swap_token_hash("who-am-i-token")
    sid = "22222222-2222-2222-2222-222222222222"
    client.post(
        "/api/auth/verify",
        json={"token": raw},
        headers={"X-Session-ID": sid},
    )
    r = client.get("/api/auth/me", headers={"X-Session-ID": sid})
    assert r.status_code == 200
    body = r.get_json()
    assert body["user"]["email"] == "who@example.com"
