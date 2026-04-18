"""Unit tests for providers/twilio_client.py.

The twilio package may not be installed in test environments. For tests that
need to exercise the real Client path, we inject a fake `twilio.rest` module
into sys.modules so the lazy import succeeds.
"""

import os
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from providers import twilio_client
from providers.twilio_client import (
    circuit_state,
    reset_circuit,
    send_sms,
)


def _install_fake_twilio(client_factory):
    """Make `from twilio.rest import Client` resolve to our factory."""
    fake_twilio = types.ModuleType("twilio")
    fake_rest = types.ModuleType("twilio.rest")
    fake_rest.Client = client_factory  # type: ignore[attr-defined]
    sys.modules["twilio"] = fake_twilio
    sys.modules["twilio.rest"] = fake_rest


def _uninstall_fake_twilio():
    sys.modules.pop("twilio", None)
    sys.modules.pop("twilio.rest", None)


@pytest.fixture(autouse=True)
def _reset_between_tests():
    """Reset circuit breaker state between tests."""
    reset_circuit()
    _uninstall_fake_twilio()
    yield
    reset_circuit()
    _uninstall_fake_twilio()


class TestDisabledMode:
    def test_pytest_context_disabled_by_default(self):
        # We're in pytest, TWILIO_FORCE_ENABLE is not set
        out = send_sms("+15551234567", "hi")
        assert out["ok"] is True
        assert out.get("mock") is True

    def test_masks_phone_in_mock(self):
        out = send_sms("+15551234567", "hi")
        assert out.get("to") == "4567"  # Last 4 digits only


class TestMissingCredentials:
    def test_no_env_returns_missing_credentials(self, monkeypatch):
        monkeypatch.setenv("TWILIO_FORCE_ENABLE", "true")
        monkeypatch.delenv("TWILIO_DISABLED", raising=False)
        monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
        monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
        monkeypatch.delenv("TWILIO_FROM_NUMBER", raising=False)
        out = send_sms("+15551234567", "hi")
        assert out["ok"] is False
        assert out["error"] == "missing_credentials"


class TestCircuitBreaker:
    def test_starts_closed(self):
        state = circuit_state()
        assert state["open"] is False
        assert state["failures"] == 0

    def test_opens_after_threshold(self, monkeypatch):
        monkeypatch.setenv("TWILIO_FORCE_ENABLE", "true")
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "tok")
        monkeypatch.setenv("TWILIO_FROM_NUMBER", "+111")

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("API down")
        factory = MagicMock(return_value=mock_client)
        _install_fake_twilio(factory)

        for _ in range(3):
            out = send_sms("+12", "hi", max_retries=0)
            assert out["ok"] is False

        state = circuit_state()
        assert state["failures"] >= 3
        assert state["open"] is True

    def test_open_circuit_short_circuits(self, monkeypatch):
        monkeypatch.setenv("TWILIO_FORCE_ENABLE", "true")
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "tok")
        monkeypatch.setenv("TWILIO_FROM_NUMBER", "+111")

        # Force the breaker open
        for _ in range(4):
            twilio_client._record_failure()
        assert circuit_state()["open"] is True

        # Next call should short-circuit without invoking Twilio
        factory = MagicMock()
        _install_fake_twilio(factory)
        out = send_sms("+12", "hi")
        assert out == {"ok": False, "error": "circuit_open"}
        factory.assert_not_called()

    def test_reset_clears_state(self):
        twilio_client._record_failure()
        twilio_client._record_failure()
        assert circuit_state()["failures"] == 2
        reset_circuit()
        assert circuit_state()["failures"] == 0


class TestSuccessPath:
    def test_success_resets_failure_count(self, monkeypatch):
        monkeypatch.setenv("TWILIO_FORCE_ENABLE", "true")
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "tok")
        monkeypatch.setenv("TWILIO_FROM_NUMBER", "+111")

        # Prime one failure
        twilio_client._record_failure()
        assert circuit_state()["failures"] == 1

        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.sid = "SM123"
        mock_client.messages.create.return_value = mock_msg
        _install_fake_twilio(MagicMock(return_value=mock_client))

        out = send_sms("+12", "hi")
        assert out == {"ok": True, "sid": "SM123"}
        assert circuit_state()["failures"] == 0


class TestTwilioPackageMissing:
    def test_import_error_returns_package_missing(self, monkeypatch):
        monkeypatch.setenv("TWILIO_FORCE_ENABLE", "true")
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "tok")
        monkeypatch.setenv("TWILIO_FROM_NUMBER", "+111")

        # Ensure no fake module is installed and twilio is truly absent
        _uninstall_fake_twilio()
        # Mark as explicitly None in sys.modules so the import raises
        with patch.dict("sys.modules", {"twilio.rest": None}):
            out = send_sms("+12", "hi", max_retries=0)
        assert out["ok"] is False


class TestRetry:
    def test_retries_exhaust_then_fail(self, monkeypatch):
        monkeypatch.setenv("TWILIO_FORCE_ENABLE", "true")
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "tok")
        monkeypatch.setenv("TWILIO_FROM_NUMBER", "+111")

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("timeout")
        _install_fake_twilio(MagicMock(return_value=mock_client))

        out = send_sms("+12", "hi", max_retries=2)
        assert out["ok"] is False
        assert "timeout" in out["error"]
        assert mock_client.messages.create.call_count == 3
