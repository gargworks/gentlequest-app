"""Opposed-pair regression test: push must DEGRADE, not crash, when its
optional dependencies are absent.

Why this file exists
--------------------
`apns2` and `firebase-admin` are in no requirements file and never have been
(verified 2026-08-20), while `services/push_delivery.py` imported them at the
top of `_apns_client` / `_send_android` -- i.e. ABOVE the config checks that
were supposed to return "apns_not_configured" / "fcm_not_configured". Those
graceful branches were unreachable dead code: in the deployed image the first
real push token would have raised ModuleNotFoundError and killed the whole
nightly job instead of degrading.

The existing suite could not catch this: tests/test_push_delivery.py patches
`_send_ios`/`_send_android` wholesale and monkeypatches a fake `apns2.payload`
into sys.modules, so it proves payload shape and token bookkeeping but never
exercises the real import path.

These tests force the failure condition -- dependency genuinely unimportable --
and assert the graceful result. `sys.modules[name] = None` is the standard way
to make `import name` raise ImportError.

Extra trap this guards: `firebase_admin` IS installed on the dev machine while
absent from every requirements file, so the Android path passes locally and
would die in Docker. These tests fail the same way in both places.
"""

import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import PushToken, UserSession, db
from services import push_delivery


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
        "SQLALCHEMY_EXPIRE_ON_COMMIT": False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def blocked_apns(monkeypatch):
    """Make `import apns2...` raise ImportError, as it does in production."""
    for name in ("apns2", "apns2.client", "apns2.credentials", "apns2.payload"):
        monkeypatch.setitem(sys.modules, name, None)


@pytest.fixture
def blocked_firebase(monkeypatch):
    for name in ("firebase_admin", "firebase_admin.credentials", "firebase_admin.messaging"):
        monkeypatch.setitem(sys.modules, name, None)


def _token(app, platform):
    sid = str(uuid.uuid4())
    db.session.add(UserSession(id=sid))
    tok = PushToken(session_id=sid, token=f"tok-{sid}", platform=platform)
    db.session.add(tok)
    db.session.commit()
    return sid, tok


# ── iOS ────────────────────────────────────────────────────────────────────

def test_apns_client_returns_none_when_dependency_missing(app, blocked_apns, monkeypatch):
    """Fully configured but dependency absent -> None, not ModuleNotFoundError."""
    for k, v in {
        "APNS_AUTH_KEY_PATH": "/tmp/fake.p8",
        "APNS_KEY_ID": "K", "APNS_TEAM_ID": "T", "APNS_BUNDLE_ID": "B",
    }.items():
        monkeypatch.setenv(k, v)
    with app.app_context():
        assert push_delivery._apns_client() is None


def test_send_ios_degrades_when_dependency_missing(app, blocked_apns, monkeypatch):
    for k, v in {
        "APNS_AUTH_KEY_PATH": "/tmp/fake.p8",
        "APNS_KEY_ID": "K", "APNS_TEAM_ID": "T", "APNS_BUNDLE_ID": "B",
    }.items():
        monkeypatch.setenv(k, v)
    with app.app_context():
        _, tok = _token(app, "ios")
        assert push_delivery._send_ios(tok, "t", "b", "generic", None) == {
            "sent": False, "reason": "apns_not_configured"
        }


def test_send_ios_degrades_when_unconfigured_and_dependency_missing(app, blocked_apns, monkeypatch):
    """The real production state: no config AND no dependency."""
    for k in ("APNS_AUTH_KEY_PATH", "APNS_AUTH_KEY_BASE64", "APNS_KEY_ID",
              "APNS_TEAM_ID", "APNS_BUNDLE_ID"):
        monkeypatch.delenv(k, raising=False)
    with app.app_context():
        _, tok = _token(app, "ios")
        assert push_delivery._send_ios(tok, "t", "b", "generic", None) == {
            "sent": False, "reason": "apns_not_configured"
        }


# ── Android ────────────────────────────────────────────────────────────────

def test_send_android_degrades_when_dependency_missing(app, blocked_firebase, monkeypatch):
    monkeypatch.setenv("FCM_SERVICE_ACCOUNT_JSON", '{"type":"service_account"}')
    with app.app_context():
        _, tok = _token(app, "android")
        assert push_delivery._send_android(tok, "t", "b", "generic", None) == {
            "sent": False, "reason": "fcm_not_configured"
        }


def test_send_android_degrades_when_unconfigured_and_dependency_missing(app, blocked_firebase, monkeypatch):
    monkeypatch.delenv("FCM_SERVICE_ACCOUNT_JSON", raising=False)
    with app.app_context():
        _, tok = _token(app, "android")
        assert push_delivery._send_android(tok, "t", "b", "generic", None) == {
            "sent": False, "reason": "fcm_not_configured"
        }


# ── The whole job must survive ─────────────────────────────────────────────

def test_send_push_survives_missing_deps_on_both_platforms(app, blocked_apns, blocked_firebase):
    """The load-bearing case: a real token exists and neither dep is installed.
    Before the fix this raised ModuleNotFoundError and took down the nightly
    retention job. It must now return a clean failure report instead."""
    with app.app_context():
        sid_i, _ = _token(app, "ios")
        result_i = push_delivery.send_push(sid_i, "t", "b", category="gentle_return")
        sid_a, _ = _token(app, "android")
        result_a = push_delivery.send_push(sid_a, "t", "b", category="gentle_return")

    assert result_i["sent"] == 0
    assert result_i["failed"][0]["reason"] == "apns_not_configured"
    assert result_a["sent"] == 0
    assert result_a["failed"][0]["reason"] == "fcm_not_configured"
