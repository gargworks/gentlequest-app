"""Unit tests for setup/logging.py + setup/ai_diagnostics.py."""

import logging
import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask

from setup.ai_diagnostics import log_ai_startup_diagnostics
from setup.logging import configure_logging, init_sentry


@pytest.fixture
def app():
    return Flask(__name__)


class TestConfigureLogging:
    def test_default_level_info(self, app):
        configure_logging(app)
        assert app.logger.level == logging.INFO

    def test_custom_level_debug(self, app):
        app.config["LOG_LEVEL"] = "DEBUG"
        configure_logging(app)
        assert app.logger.level == logging.DEBUG

    def test_unknown_level_falls_back_to_info(self, app):
        app.config["LOG_LEVEL"] = "BANANA"
        configure_logging(app)
        assert app.logger.level == logging.INFO

    def test_stream_handler_attached(self, app):
        configure_logging(app)
        handlers = [h for h in app.logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(handlers) >= 1

    def test_idempotent_no_duplicate_handlers(self, app):
        configure_logging(app)
        first = len([h for h in app.logger.handlers if isinstance(h, logging.StreamHandler)])
        configure_logging(app)
        second = len([h for h in app.logger.handlers if isinstance(h, logging.StreamHandler)])
        assert second == first


class TestInitSentry:
    def test_no_dsn_is_noop(self, app, monkeypatch):
        monkeypatch.delenv("SENTRY_DSN_BACKEND", raising=False)
        # Should not raise
        init_sentry(app)

    def test_with_dsn_calls_sentry_init(self, app, monkeypatch):
        monkeypatch.setenv("SENTRY_DSN_BACKEND", "https://fake@sentry.io/1")
        with patch("setup.logging.sentry_sdk.init") as mock_init:
            init_sentry(app)
            mock_init.assert_called_once()

    def test_sentry_init_exception_non_fatal(self, app, monkeypatch):
        monkeypatch.setenv("SENTRY_DSN_BACKEND", "https://fake@sentry.io/1")
        with patch("setup.logging.sentry_sdk.init", side_effect=RuntimeError("boom")):
            # Should not raise
            init_sentry(app)


class TestJSONLogging:
    def test_json_format_when_env_set(self, app, monkeypatch):
        import json as _json
        import logging as _logging

        monkeypatch.setenv("LOG_FORMAT", "json")
        # Clear any prior handlers so configure_logging attaches a fresh one
        app.logger.handlers.clear()
        configure_logging(app)

        handler = next(
            h for h in app.logger.handlers if isinstance(h, _logging.StreamHandler)
        )
        record = _logging.LogRecord(
            name="test", level=_logging.INFO, pathname="x", lineno=1,
            msg="hello world", args=(), exc_info=None,
        )
        out = handler.format(record)
        data = _json.loads(out)
        assert data["message"] == "hello world"
        assert data["level"] == "INFO"

    def test_plain_format_when_env_unset(self, app, monkeypatch):
        monkeypatch.delenv("LOG_FORMAT", raising=False)
        app.logger.handlers.clear()
        configure_logging(app)
        handler = next(h for h in app.logger.handlers if isinstance(h, logging.StreamHandler))
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="x", lineno=1,
            msg="hi", args=(), exc_info=None,
        )
        out = handler.format(record)
        # Plain format is bracketed timestamp, not JSON
        assert out.startswith("[")
        assert "hi" in out


class TestSentryScrubber:
    def test_request_body_scrubbed(self):
        from setup.logging import _sentry_scrub_pii
        event = {"request": {"data": "I am having dark thoughts"}}
        out = _sentry_scrub_pii(event, {})
        assert out["request"]["data"] == "<scrubbed>"

    def test_extra_message_scrubbed(self):
        from setup.logging import _sentry_scrub_pii
        event = {"extra": {"user_message": "secret", "other": "safe"}}
        out = _sentry_scrub_pii(event, {})
        assert out["extra"]["user_message"] == "<scrubbed>"
        assert out["extra"]["other"] == "safe"

    def test_handles_missing_fields(self):
        from setup.logging import _sentry_scrub_pii
        # Should not raise
        assert _sentry_scrub_pii({}, {}) == {}


class TestAIDiagnostics:
    def test_emits_log_line(self, app, caplog):
        configure_logging(app)
        app.config["AI_PROVIDER"] = "gemini"
        with caplog.at_level(logging.INFO, logger=app.logger.name):
            log_ai_startup_diagnostics(app)
        # Find our startup log
        assert any("AI startup:" in rec.message for rec in caplog.records), (
            f"Records: {[r.message for r in caplog.records]}"
        )

    def test_safe_on_exception(self, app):
        with patch(
            "setup.ai_diagnostics._provider_keys_available",
            side_effect=RuntimeError("boom"),
        ):
            # Must not raise
            log_ai_startup_diagnostics(app)
