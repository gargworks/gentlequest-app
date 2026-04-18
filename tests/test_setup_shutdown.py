"""Unit tests for setup/shutdown.py."""

import os
import signal
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask

from setup.shutdown import (
    _close_redis,
    _shutdown_background_executor,
    register_graceful_shutdown,
)


@pytest.fixture
def app():
    return Flask(__name__)


class TestShutdownBackgroundExecutor:
    def test_no_raise_on_empty_executor(self):
        # Shouldn't raise even if no jobs are pending
        _shutdown_background_executor(timeout_s=0.1)

    def test_swallows_executor_exceptions(self):
        with patch(
            "setup.shutdown.background_executor.shutdown",
            side_effect=RuntimeError("boom"),
        ):
            # Must not raise
            _shutdown_background_executor()


class TestCloseRedis:
    def test_no_redis_is_noop(self, app):
        app.config["SESSION_REDIS"] = None
        _close_redis(app)  # Should not raise

    def test_calls_close_on_client(self, app):
        client = MagicMock()
        app.config["SESSION_REDIS"] = client
        _close_redis(app)
        client.close.assert_called_once()

    def test_swallows_close_exceptions(self, app):
        client = MagicMock()
        client.close.side_effect = RuntimeError("boom")
        app.config["SESSION_REDIS"] = client
        _close_redis(app)  # Should not raise


class TestRegisterGracefulShutdown:
    def test_handler_registered(self, app):
        original = signal.getsignal(signal.SIGTERM)
        try:
            register_graceful_shutdown(app)
            new_handler = signal.getsignal(signal.SIGTERM)
            assert new_handler is not original, "SIGTERM handler not replaced"
        finally:
            # Restore to avoid affecting other tests
            signal.signal(signal.SIGTERM, original)

    def test_sigint_handler_registered(self, app):
        original = signal.getsignal(signal.SIGINT)
        try:
            register_graceful_shutdown(app)
            new_handler = signal.getsignal(signal.SIGINT)
            assert new_handler is not original
        finally:
            signal.signal(signal.SIGINT, original)

    def test_non_main_thread_non_fatal(self, app):
        """signal.signal() raises ValueError off the main thread — we must swallow."""
        with patch("setup.shutdown.signal.signal", side_effect=ValueError("not main thread")):
            # Must not raise
            register_graceful_shutdown(app)

    def test_signal_handler_drains_and_exits(self, app):
        """Trigger the handler directly and verify it calls sys.exit(0)."""
        # Patch the drain + redis close to avoid side effects
        with (
            patch("setup.shutdown._shutdown_background_executor") as mock_drain,
            patch("setup.shutdown._close_redis") as mock_close,
            patch("setup.shutdown.sys.exit", side_effect=SystemExit(0)) as mock_exit,
        ):
            # Save original and install new handler
            original = signal.getsignal(signal.SIGTERM)
            try:
                register_graceful_shutdown(app)
                handler = signal.getsignal(signal.SIGTERM)
                with pytest.raises(SystemExit):
                    handler(signal.SIGTERM, None)
                mock_drain.assert_called_once()
                mock_close.assert_called_once()
                mock_exit.assert_called_once_with(0)
            finally:
                signal.signal(signal.SIGTERM, original)
