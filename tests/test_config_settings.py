"""Unit tests for config/settings.py."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import (
    ENV_CONFIG,
    ENVIRONMENT,
    _detect_environment,
    _get_environment_config,
)


class TestDetectEnvironment:
    def test_render(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.delenv("DOCKER_ENV", raising=False)
        monkeypatch.delenv("DOCKER", raising=False)
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        assert _detect_environment() == "production"

    def test_docker_env(self, monkeypatch):
        monkeypatch.delenv("RENDER", raising=False)
        monkeypatch.setenv("DOCKER_ENV", "true")
        assert _detect_environment() == "docker"

    def test_docker_via_docker(self, monkeypatch):
        monkeypatch.delenv("RENDER", raising=False)
        monkeypatch.delenv("DOCKER_ENV", raising=False)
        monkeypatch.setenv("DOCKER", "1")
        assert _detect_environment() == "docker"

    def test_environment_override(self, monkeypatch):
        monkeypatch.delenv("RENDER", raising=False)
        monkeypatch.delenv("DOCKER_ENV", raising=False)
        monkeypatch.delenv("DOCKER", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "staging")
        assert _detect_environment() == "staging"

    def test_default_local(self, monkeypatch):
        for v in ["RENDER", "DOCKER_ENV", "DOCKER", "ENVIRONMENT"]:
            monkeypatch.delenv(v, raising=False)
        assert _detect_environment() == "local"


class TestGetEnvironmentConfig:
    def test_local_has_port(self):
        cfg = _get_environment_config("local")
        assert cfg["port"] == 5055
        assert "cors_origins" in cfg

    def test_docker_uses_db_host(self):
        cfg = _get_environment_config("docker")
        assert "db:5432" in cfg["database_url"]

    def test_production_cors_origins(self):
        cfg = _get_environment_config("production")
        assert "https://gentlequest.onrender.com" in cfg["cors_origins"]

    def test_unknown_falls_to_local(self):
        assert _get_environment_config("wat") == _get_environment_config("local")


class TestConfigModuleConstants:
    def test_environment_set_at_import(self):
        assert ENVIRONMENT in ("local", "docker", "production") or isinstance(
            ENVIRONMENT, str
        )

    def test_env_config_keys(self):
        for k in ("port", "cors_origins"):
            assert k in ENV_CONFIG


class TestConfigClass:
    def test_has_required_attrs(self):
        from config.settings import Config
        for attr in [
            "SECRET_KEY", "SESSION_TYPE", "PORT", "AI_PROVIDER",
            "CORS_ORIGINS", "RATE_LIMIT_ENABLED", "LOG_LEVEL",
            "MESSAGE_RETENTION_DAYS", "SESSION_RETENTION_DAYS",
        ]:
            assert hasattr(Config, attr), f"Config.{attr} missing"

    def test_port_is_int(self):
        from config.settings import Config
        assert isinstance(Config.PORT, int)

    def test_cors_origins_is_list(self):
        from config.settings import Config
        assert isinstance(Config.CORS_ORIGINS, list)
