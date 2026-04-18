"""Unit tests for helpers/health_helpers.py."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["PYTEST_CURRENT_TEST"] = "true"

from app import create_app
from helpers.health_helpers import (
    _check_database_health,
    _check_ollama_health,
    _check_redis_health,
    _detect_platform,
)
from models import db


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


# ---------------------------------------------------------------------------
# _check_database_health
# ---------------------------------------------------------------------------

class TestDatabaseHealth:
    def test_healthy_on_sqlite(self, app):
        assert _check_database_health() == "healthy"

    def test_unhealthy_on_broken_engine(self, app):
        # Patch the bind to something that raises on execute
        with patch.object(db.session, "execute", side_effect=Exception("boom")):
            assert _check_database_health() == "unhealthy"


# ---------------------------------------------------------------------------
# _check_redis_health
# ---------------------------------------------------------------------------

class TestRedisHealth:
    def test_filesystem_session_returns_using_filesystem(self, app):
        app.config["SESSION_TYPE"] = "filesystem"
        assert _check_redis_health() == "using filesystem"

    def test_redis_session_without_client_returns_not_configured(self, app):
        app.config["SESSION_TYPE"] = "redis"
        app.config["SESSION_REDIS"] = None
        assert _check_redis_health() == "not configured"

    def test_redis_healthy_when_ping_succeeds(self, app):
        app.config["SESSION_TYPE"] = "redis"
        fake = MagicMock()
        fake.ping.return_value = True
        app.config["SESSION_REDIS"] = fake
        assert _check_redis_health() == "healthy"

    def test_redis_unhealthy_when_ping_raises(self, app):
        app.config["SESSION_TYPE"] = "redis"
        fake = MagicMock()
        fake.ping.side_effect = Exception("refused")
        app.config["SESSION_REDIS"] = fake
        assert _check_redis_health() == "unhealthy"


# ---------------------------------------------------------------------------
# _check_ollama_health
# ---------------------------------------------------------------------------

class TestOllamaHealth:
    def test_healthy_with_model_loaded(self):
        fake = MagicMock()
        fake.raise_for_status = MagicMock()
        fake.json.return_value = {"models": [{"name": "third-brother:7b"}]}
        with patch("helpers.health_helpers.requests.get", return_value=fake):
            result = _check_ollama_health()
            assert result["status"] == "healthy"
            assert result["model_loaded"] is True

    def test_healthy_without_target_model(self):
        fake = MagicMock()
        fake.raise_for_status = MagicMock()
        fake.json.return_value = {"models": [{"name": "llama3:8b"}]}
        with patch("helpers.health_helpers.requests.get", return_value=fake):
            result = _check_ollama_health()
            assert result["status"] == "healthy"
            assert result["model_loaded"] is False

    def test_unreachable_on_connection_error(self):
        import requests as _req
        with patch("helpers.health_helpers.requests.get", side_effect=_req.ConnectionError()):
            assert _check_ollama_health()["status"] == "unreachable"

    def test_timeout_status(self):
        import requests as _req
        with patch("helpers.health_helpers.requests.get", side_effect=_req.Timeout()):
            assert _check_ollama_health()["status"] == "timeout"

    def test_unhealthy_on_other_exception(self):
        with patch("helpers.health_helpers.requests.get", side_effect=RuntimeError("wat")):
            assert _check_ollama_health()["status"].startswith("unhealthy")


# ---------------------------------------------------------------------------
# _detect_platform
# ---------------------------------------------------------------------------

class TestDetectPlatform:
    def test_render(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.delenv("DOCKER_ENV", raising=False)
        monkeypatch.delenv("DOCKER", raising=False)
        assert _detect_platform() == "render"

    def test_docker_via_docker_env(self, monkeypatch):
        monkeypatch.delenv("RENDER", raising=False)
        monkeypatch.setenv("DOCKER_ENV", "true")
        assert _detect_platform() == "docker"

    def test_docker_via_docker(self, monkeypatch):
        monkeypatch.delenv("RENDER", raising=False)
        monkeypatch.delenv("DOCKER_ENV", raising=False)
        monkeypatch.setenv("DOCKER", "1")
        assert _detect_platform() == "docker"

    def test_local_default(self, monkeypatch):
        monkeypatch.delenv("RENDER", raising=False)
        monkeypatch.delenv("DOCKER_ENV", raising=False)
        monkeypatch.delenv("DOCKER", raising=False)
        assert _detect_platform() == "local"
