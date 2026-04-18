"""Unit tests for setup/error_handlers.py."""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["PYTEST_CURRENT_TEST"] = "true"

from app import create_app
from models import db


@pytest.fixture
def client():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "RATE_LIMIT_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
        yield app.test_client()


class TestRequestIDMiddleware:
    def test_response_has_request_id_header(self, client):
        r = client.get("/api/ping")
        assert "X-Request-ID" in r.headers
        assert len(r.headers["X-Request-ID"]) > 0

    def test_response_has_response_time_header(self, client):
        r = client.get("/api/ping")
        assert "X-Response-Time" in r.headers
        # Numeric value
        assert r.headers["X-Response-Time"].isdigit()

    def test_inbound_request_id_preserved(self, client):
        r = client.get("/api/ping", headers={"X-Request-ID": "trace-abc"})
        assert r.headers.get("X-Request-ID") == "trace-abc"


class TestErrorHandlers:
    def test_404_on_api_returns_json(self, client):
        r = client.get("/api/totally-missing")
        assert r.status_code == 404
        assert r.is_json
        assert r.json.get("error") == "Not found"

    def test_404_on_browser_returns_html(self, client):
        r = client.get("/does-not-exist")
        assert r.status_code == 404
        assert "html" in r.content_type.lower()

    def test_405_method_not_allowed(self, client):
        # POST on a GET-only endpoint
        r = client.post("/api/ping")
        assert r.status_code == 405
        assert r.is_json
        assert r.json.get("error") == "Method not allowed"

    def test_handlers_registered(self, client):
        # Smoke check: confirm the app has explicit handlers for 404/405
        app = client.application
        # Flask stores handlers keyed by error code under the None (global) blueprint
        codes = set()
        for bp_key, handlers in app.error_handler_spec.items():
            codes.update(handlers.keys())
        assert 404 in codes
        assert 405 in codes
        assert 413 in codes
        assert 429 in codes
        assert 500 in codes
