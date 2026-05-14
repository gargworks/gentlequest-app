import os
import sys
import types
import uuid
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import PushToken, UserSession, db
from services import push_delivery


@pytest.fixture
def app(monkeypatch):
    os.environ["PYTEST_CURRENT_TEST"] = "true"
    monkeypatch.delenv("DEBUG_PUSH_ENABLED", raising=False)
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
def client(app):
    return app.test_client()


def _sid():
    return str(uuid.uuid4())


def _add_token(session_id, token, platform):
    db.session.add(UserSession(id=session_id))
    db.session.add(PushToken(session_id=session_id, token=token, platform=platform))
    db.session.commit()


def test_send_push_ios_uses_critical_payload_for_crisis_category(app):
    sid = _sid()
    with app.app_context():
        _add_token(sid, "ios-token", "ios")
        with patch("services.push_delivery._send_ios", return_value={"sent": True}) as send_ios:
            result = push_delivery.send_push(sid, "Help", "Checking in", category="crisis_followup")
            token, title, body, category, collapse_key = send_ios.call_args.args
            assert token.token == "ios-token"
            assert title == "Help"
            assert body == "Checking in"
            assert category == "crisis_followup"
            assert collapse_key is None

    assert result["sent"] == 1
    payload = push_delivery._apns_payload("Help", "Checking in", "crisis_followup", None)
    assert payload["aps"]["interruption-level"] == "critical"
    assert payload["aps"]["sound"]["critical"] == 1


def test_send_push_android_calls_fcm_path(app):
    sid = _sid()
    with app.app_context():
        _add_token(sid, "android-token", "android")
        with patch("services.push_delivery._send_android", return_value={"sent": True}) as send_android:
            result = push_delivery.send_push(sid, "Daily", "How are you?", category="daily_checkin", collapse_key="daily")
            token, title, body, category, collapse_key = send_android.call_args.args
            assert token.token == "android-token"
            assert category == "daily_checkin"
            assert collapse_key == "daily"

    assert result["sent"] == 1


def test_invalid_ios_token_is_revoked(app, monkeypatch):
    import sys
    fake_payload = types.ModuleType("apns2.payload")
    fake_payload.Payload = lambda **kwargs: kwargs
    monkeypatch.setitem(sys.modules, "apns2.payload", fake_payload)
    sid = _sid()
    with app.app_context():
        _add_token(sid, "bad-ios", "ios")
        token = PushToken.query.filter_by(token="bad-ios").one()
        with patch("services.push_delivery._apns_client") as client_factory:
            client_factory.return_value.send_notification.return_value = types.SimpleNamespace(status=410, reason="Unregistered")
            result = push_delivery._send_ios(token, "Title", "Body", "generic", None)
            db.session.commit()
        refreshed = PushToken.query.filter_by(token="bad-ios").one()

    assert result == {"sent": False, "reason": "Unregistered"}
    assert refreshed.revoked_at is not None


def test_web_token_is_skipped(app):
    sid = _sid()
    with app.app_context():
        _add_token(sid, "web-token", "web")
        result = push_delivery.send_push(sid, "Title", "Body")

    assert result["sent"] == 0
    assert result["skipped"] == [{"token": "web-token", "platform": "web", "reason": "web_push_skipped"}]


def test_debug_push_endpoint_is_gated_and_calls_sender(client, monkeypatch):
    sid = _sid()
    disabled = client.post("/api/debug/push-test", json={"title": "T", "body": "B"}, headers={"X-Session-ID": sid})
    monkeypatch.setenv("DEBUG_PUSH_ENABLED", "true")
    with patch("routes.debug_push.send_push", return_value={"sent": 1, "failed": [], "skipped": []}) as sender:
        enabled = client.post(
            "/api/debug/push-test",
            json={"title": "T", "body": "B", "category": "generic"},
            headers={"X-Session-ID": sid},
        )

    assert disabled.status_code == 404
    assert enabled.status_code == 200
    assert enabled.get_json()["sent"] == 1
    sender.assert_called_once_with(sid, "T", "B", category="generic")
