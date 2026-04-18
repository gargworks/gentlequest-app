"""Tests for /api/health/deep admin-gated deep health probe."""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["PYTEST_CURRENT_TEST"] = "true"

from app import create_app
from models import db


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "RATE_LIMIT_ENABLED": False,
        "ADMIN_API_TOKEN": "test-admin-token",
    })
    with app.app_context():
        db.create_all()
        yield app


class TestHealthDeep:
    def test_unauthorized_without_token(self, app):
        c = app.test_client()
        r = c.get("/api/health/deep")
        assert r.status_code == 401

    def test_unauthorized_with_wrong_token(self, app):
        c = app.test_client()
        r = c.get("/api/health/deep", headers={"X-Admin-Token": "wrong"})
        assert r.status_code == 401

    def test_authorized_with_correct_token(self, app):
        c = app.test_client()
        r = c.get("/api/health/deep", headers={"X-Admin-Token": "test-admin-token"})
        assert r.status_code == 200
        assert r.is_json

    def test_response_schema(self, app):
        c = app.test_client()
        r = c.get("/api/health/deep", headers={"X-Admin-Token": "test-admin-token"})
        data = r.json
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "db" in data and "status" in data["db"] and "latency_ms" in data["db"]
        assert "redis" in data and "status" in data["redis"]
        assert "ollama" in data and "status" in data["ollama"]
        assert "system" in data
        # disk_free_gb and memory_percent are either a number or None (if psutil fails)
        assert "disk_free_gb" in data["system"]
        assert "memory_percent" in data["system"]
        assert "environment" in data
        assert "version" in data

    def test_no_admin_token_configured_returns_401(self, app):
        # Even with a valid-looking token, if ADMIN_API_TOKEN is unset, deny
        app.config["ADMIN_API_TOKEN"] = ""
        c = app.test_client()
        r = c.get("/api/health/deep", headers={"X-Admin-Token": "anything"})
        assert r.status_code == 401
