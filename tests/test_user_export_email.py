import os
import sys
import uuid
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import db


@pytest.fixture
def app(monkeypatch):
    os.environ["PYTEST_CURRENT_TEST"] = "true"
    monkeypatch.delenv("SENDGRID_API_KEY", raising=False)
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


def test_export_email_sends_when_sendgrid_configured(client, monkeypatch):
    sid = _sid()
    monkeypatch.setenv("SENDGRID_API_KEY", "SG.test-key")

    with patch("services.export_email.requests.post") as post:
        post.return_value.raise_for_status.return_value = None
        response = client.post("/api/user/export", headers={"X-Session-ID": sid, "X-User-Email": "user@example.com"})

    assert response.status_code == 202
    assert response.get_json() == {"delivery": "email", "email": "u***r@example.com"}
    payload = post.call_args.kwargs["json"]
    assert payload["personalizations"][0]["to"][0]["email"] == "user@example.com"
    assert payload["attachments"][0]["filename"] == "gentlequest-data-export.json"
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer SG.test-key"


def test_export_falls_back_inline_without_sendgrid_key(client, monkeypatch):
    sid = _sid()
    monkeypatch.delenv("SENDGRID_API_KEY", raising=False)

    with patch("services.export_email.requests.post") as post:
        response = client.post("/api/user/export", headers={"X-Session-ID": sid, "X-User-Email": "user@example.com"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["delivery"] == "inline_json"
    assert data["profile"]["email"] == "user@example.com"
    post.assert_not_called()
