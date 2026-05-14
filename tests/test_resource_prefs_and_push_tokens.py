import os
import sys
import time
import uuid

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import PushToken, db


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


def _headers(session_id):
    return {"X-Session-ID": session_id}


def test_favorite_toggle_round_trip(client):
    sid = _sid()

    on = client.post(
        "/api/user/resources/favorite",
        json={"resource_id": "box-breathing", "favorite": True},
        headers=_headers(sid),
    )
    favorites = client.get("/api/user/resources/favorites", headers=_headers(sid))
    off = client.post(
        "/api/user/resources/favorite",
        json={"resource_id": "box-breathing", "favorite": False},
        headers=_headers(sid),
    )
    favorites_after = client.get("/api/user/resources/favorites", headers=_headers(sid))

    assert on.status_code == 200
    assert on.get_json() == {"resource_id": "box-breathing", "favorite": True}
    assert favorites.get_json() == ["box-breathing"]
    assert off.status_code == 200
    assert off.get_json() == {"resource_id": "box-breathing", "favorite": False}
    assert favorites_after.get_json() == []


def test_recents_ordering_limit_returns_newest_three(client):
    sid = _sid()

    for i in range(5):
        response = client.post(
            "/api/user/resources/opened",
            json={"resource_id": f"resource-{i}"},
            headers=_headers(sid),
        )
        assert response.status_code == 200
        time.sleep(0.01)

    recents = client.get("/api/user/resources/recents?limit=3", headers=_headers(sid))

    assert recents.status_code == 200
    assert recents.get_json() == ["resource-4", "resource-3", "resource-2"]


def test_push_token_upsert_same_session_token_is_idempotent(client):
    sid = _sid()

    first = client.post(
        "/api/user/push-tokens",
        json={"token": "abc123", "platform": "ios"},
        headers=_headers(sid),
    )
    second = client.post(
        "/api/user/push-tokens",
        json={"token": "abc123", "platform": "ios"},
        headers=_headers(sid),
    )
    listed = client.get("/api/user/push-tokens", headers=_headers(sid))

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.get_json()["id"] == first.get_json()["id"]
    assert len(listed.get_json()) == 1


def test_push_token_delete_sets_revoked_at_and_get_excludes_revoked(client):
    sid = _sid()
    client.post(
        "/api/user/push-tokens",
        json={"token": "abc123", "platform": "ios"},
        headers=_headers(sid),
    )

    deleted = client.delete("/api/user/push-tokens/abc123", headers=_headers(sid))
    listed = client.get("/api/user/push-tokens", headers=_headers(sid))

    assert deleted.status_code == 200
    assert deleted.get_json() == {"revoked": True}
    assert listed.get_json() == []
    with client.application.app_context():
        token = PushToken.query.filter_by(session_id=sid, token="abc123").first()
        assert token.revoked_at is not None


def test_validation_missing_resource_id_or_token_returns_400(client):
    sid = _sid()

    missing_resource = client.post(
        "/api/user/resources/favorite",
        json={"favorite": True},
        headers=_headers(sid),
    )
    missing_token = client.post(
        "/api/user/push-tokens",
        json={"platform": "ios"},
        headers=_headers(sid),
    )

    assert missing_resource.status_code == 400
    assert missing_resource.get_json()["error"] == "resource_id is required"
    assert missing_token.status_code == 400
    assert missing_token.get_json()["error"] == "token is required"
