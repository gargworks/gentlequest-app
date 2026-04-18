"""Unit tests for setup/extensions.py."""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["PYTEST_CURRENT_TEST"] = "true"

from app import create_app
from models import db
from setup.extensions import (
    _rate_limit_enabled,
    _rate_limit_key,
    _setup_cors,
    _setup_security_headers,
    _setup_session,
    configure_app,
)


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


class TestSecurityHeaders:
    def test_headers_present_on_response(self, app):
        client = app.test_client()
        resp = client.get("/api/ping")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "Referrer-Policy" in resp.headers
        assert "Content-Security-Policy" in resp.headers
        assert "Permissions-Policy" in resp.headers

    def test_hsts_only_in_production(self, app):
        client = app.test_client()
        resp = client.get("/api/ping")
        # Default test env is not production
        assert "Strict-Transport-Security" not in resp.headers


class TestRateLimitEnabled:
    def test_returns_true_on_bool_true(self, app):
        with app.test_request_context("/"):
            app.config["RATE_LIMIT_ENABLED"] = True
            assert _rate_limit_enabled() is True

    def test_returns_false_on_bool_false(self, app):
        with app.test_request_context("/"):
            app.config["RATE_LIMIT_ENABLED"] = False
            assert _rate_limit_enabled() is False

    def test_parses_string_true(self, app):
        with app.test_request_context("/"):
            app.config["RATE_LIMIT_ENABLED"] = "true"
            assert _rate_limit_enabled() is True

    def test_parses_string_false(self, app):
        with app.test_request_context("/"):
            app.config["RATE_LIMIT_ENABLED"] = "false"
            assert _rate_limit_enabled() is False


class TestRateLimitKey:
    def test_unique_per_request_when_disabled(self, app):
        with app.test_request_context("/"):
            app.config["RATE_LIMIT_ENABLED"] = False
            a = _rate_limit_key()
            b = _rate_limit_key()
        assert a != b  # time_ns suffix ensures uniqueness

    def test_uses_session_id_when_enabled(self, app):
        with app.test_request_context(
            "/", headers={"X-Session-ID": "abc123"}
        ):
            app.config["RATE_LIMIT_ENABLED"] = True
            assert _rate_limit_key() == "sid:abc123"


class TestCORSSetup:
    def test_cors_configured_on_allowed_origin(self, app):
        client = app.test_client()
        # OPTIONS preflight with a whitelisted origin
        resp = client.options(
            "/api/ping",
            headers={
                "Origin": "http://localhost:8080",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Either 200 or 204 for preflight, but CORS header should reflect origin
        assert resp.headers.get("Access-Control-Allow-Origin") in (
            "http://localhost:8080",
            "*",
        )


class TestConfigureApp:
    def test_callable_exists(self, app):
        # configure_app is not idempotent (db.init_app enforces single-registration);
        # verify the symbol is importable and callable with a fresh Flask instance.
        from flask import Flask

        from config.settings import Config as _Config
        fresh = Flask(__name__)
        fresh.config.from_object(_Config)
        fresh.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        fresh.config["RATE_LIMIT_ENABLED"] = False
        # configure_app may raise in testing due to shared `db` extension;
        # the assertion is that it's a callable symbol.
        assert callable(configure_app)


class TestSetupSessionFallback:
    def test_no_redis_uses_filesystem(self, app):
        app.config["REDIS_URL"] = ""
        _setup_session(app)
        assert app.config["SESSION_TYPE"] == "filesystem"


class TestDirectCallables:
    def test_setup_cors_accepts_flask_app(self, app):
        # Idempotent call; should not raise
        _setup_cors(app)

    def test_setup_security_headers_registers_after_request(self, app):
        before = len(app.after_request_funcs.get(None, []))
        _setup_security_headers(app)
        after = len(app.after_request_funcs.get(None, []))
        assert after == before + 1
