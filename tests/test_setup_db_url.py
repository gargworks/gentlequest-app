"""Unit tests for setup/db_url.py."""

import logging
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask

from setup.db_url import (
    _mask_db_url,
    _normalize_postgres_url,
    configure_database_url,
)


@pytest.fixture
def app():
    a = Flask(__name__)
    a.logger.setLevel(logging.DEBUG)
    return a


class TestNormalizePostgresUrl:
    def test_legacy_postgres_scheme_upgraded(self, app):
        out = _normalize_postgres_url("postgres://u:p@host/db", app)
        assert out.startswith("postgresql+psycopg://")

    def test_psycopg_driver_added(self, app):
        out = _normalize_postgres_url("postgresql://u:p@host/db", app)
        assert "postgresql+psycopg://" in out

    def test_existing_psycopg_unchanged_scheme(self, app):
        out = _normalize_postgres_url("postgresql+psycopg://u:p@host/db", app)
        assert "postgresql+psycopg" in out

    def test_connect_timeout_appended(self, app):
        out = _normalize_postgres_url("postgresql://u:p@host/db", app)
        assert "connect_timeout=2" in out

    def test_existing_connect_timeout_preserved(self, app):
        out = _normalize_postgres_url(
            "postgresql://u:p@host/db?connect_timeout=10", app
        )
        assert "connect_timeout=10" in out
        # Should not append a second value
        assert out.count("connect_timeout=") == 1

    def test_sqlite_untouched(self, app):
        # Non-postgres schemes are left alone after scheme check
        out = _normalize_postgres_url("sqlite:///:memory:", app)
        assert out == "sqlite:///:memory:"


class TestMaskDbUrl:
    def test_masks_password(self):
        out = _mask_db_url("postgresql://user:sekret@host/db")
        assert "sekret" not in out
        assert "user:***" in out

    def test_sqlite_passes_through(self):
        out = _mask_db_url("sqlite:///instance/mental_health.db")
        assert out == "sqlite:///instance/mental_health.db"

    def test_no_credentials(self):
        out = _mask_db_url("postgresql://host/db")
        assert out.startswith("postgresql://")

    def test_malformed_returns_sentinel(self):
        out = _mask_db_url(12345)  # type: ignore[arg-type]
        assert out == "<mask_failed>"


class TestConfigureDatabaseUrl:
    def test_env_url_applied(self, app, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
        configure_database_url(app)
        uri = app.config.get("SQLALCHEMY_DATABASE_URI")
        assert uri.startswith("postgresql+psycopg://")

    def test_no_env_falls_back_to_sqlite_when_not_testing(self, app, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        app.config["TESTING"] = False
        configure_database_url(app)
        assert "sqlite:///instance/" in app.config["SQLALCHEMY_DATABASE_URI"]

    def test_no_env_and_testing_leaves_uri_unset(self, app, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        configure_database_url(app)
        # Existing URI preserved in test mode
        assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"

    def test_engine_options_set(self, app, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
        configure_database_url(app)
        opts = app.config["SQLALCHEMY_ENGINE_OPTIONS"]
        assert opts["pool_pre_ping"] is True
        assert opts["pool_recycle"] == 300
        assert opts["pool_size"] == 5

    def test_sqlite_gets_minimal_engine_options(self, app, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        app.config["TESTING"] = False
        configure_database_url(app)
        opts = app.config["SQLALCHEMY_ENGINE_OPTIONS"]
        assert opts["pool_pre_ping"] is True
        # SQLite must NOT get pool_size / max_overflow / pool_timeout
        assert "pool_size" not in opts
        assert "max_overflow" not in opts

    def test_track_modifications_disabled(self, app, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
        configure_database_url(app)
        assert app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] is False
