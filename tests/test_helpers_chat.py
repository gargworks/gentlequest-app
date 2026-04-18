"""Unit tests for helpers/chat_helpers.py."""

import os
import sys
import uuid
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["PYTEST_CURRENT_TEST"] = "true"

from app import create_app
from helpers.chat_helpers import (
    _apply_layer_2_safety,
    _build_failover_chain,
    _call_provider,
    _convert_risk_level_to_score,
    _get_ai_response_with_failover,
    _get_fallback_html,
    _is_failure_response,
    _is_quota_or_rate_limit_error,
    _log_conversation,
    _log_tool_calls,
    _parse_csv_env,
    _provider_keys_available,
)
from models import Message, db


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
# _is_failure_response
# ---------------------------------------------------------------------------

class TestIsFailureResponse:
    def test_empty_is_failure(self):
        assert _is_failure_response("") is True
        assert _is_failure_response(None) is True
        assert _is_failure_response("   ") is True

    def test_configuration_error_marker(self):
        assert _is_failure_response("Configuration error: missing key") is True

    def test_generating_error_marker(self):
        assert _is_failure_response("Error generating response: timeout") is True

    def test_connecting_marker(self):
        assert (
            _is_failure_response("I'm having trouble connecting to my AI services")
            is True
        )

    def test_normal_response_not_failure(self):
        assert _is_failure_response("Here is a helpful response.") is False

    def test_case_insensitive_detection(self):
        assert _is_failure_response("CONFIGURATION ERROR: missing") is True


# ---------------------------------------------------------------------------
# _is_quota_or_rate_limit_error
# ---------------------------------------------------------------------------

class TestIsQuotaOrRateLimitError:
    def test_empty_returns_false(self):
        assert _is_quota_or_rate_limit_error("") is False
        assert _is_quota_or_rate_limit_error(None) is False

    @pytest.mark.parametrize("s", [
        "quota exceeded",
        "rate limit reached",
        "RateLimit hit",
        "resource_exhausted",
        "Resource Exhausted",
        "429 Too Many Requests",
        "limit: 0 for quota metric",
    ])
    def test_positive_tokens(self, s):
        assert _is_quota_or_rate_limit_error(s) is True

    def test_normal_error_returns_false(self):
        assert _is_quota_or_rate_limit_error("Something went wrong") is False


# ---------------------------------------------------------------------------
# _parse_csv_env
# ---------------------------------------------------------------------------

class TestParseCsvEnv:
    def test_parses_csv(self):
        assert _parse_csv_env("a,b,c") == ["a", "b", "c"]

    def test_strips_whitespace(self):
        assert _parse_csv_env("  a  ,  b ,c ") == ["a", "b", "c"]

    def test_empty_values_dropped(self):
        assert _parse_csv_env("a,,b") == ["a", "b"]

    def test_empty_string_returns_empty_list(self):
        assert _parse_csv_env("") == []

    def test_none_returns_empty_list(self):
        assert _parse_csv_env(None) == []


# ---------------------------------------------------------------------------
# _provider_keys_available
# ---------------------------------------------------------------------------

class TestProviderKeysAvailable:
    def test_all_absent(self, monkeypatch):
        for k in ["GEMINI_API_KEY", "GEMINI_API_KEYS", "OPENAI_API_KEY",
                  "PERPLEXITY_API_KEY", "PPLX_API_KEY"]:
            monkeypatch.delenv(k, raising=False)
        result = _provider_keys_available()
        assert result == {"gemini": False, "openai": False, "perplexity": False}

    def test_gemini_present(self, monkeypatch):
        for k in ["OPENAI_API_KEY", "PERPLEXITY_API_KEY", "PPLX_API_KEY",
                  "GEMINI_API_KEYS"]:
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("GEMINI_API_KEY", "abc")
        assert _provider_keys_available()["gemini"] is True

    def test_pplx_alias(self, monkeypatch):
        for k in ["GEMINI_API_KEY", "GEMINI_API_KEYS", "OPENAI_API_KEY",
                  "PERPLEXITY_API_KEY"]:
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("PPLX_API_KEY", "xyz")
        assert _provider_keys_available()["perplexity"] is True


# ---------------------------------------------------------------------------
# _build_failover_chain
# ---------------------------------------------------------------------------

class TestBuildFailoverChain:
    def test_configured_provider_first(self, app, monkeypatch):
        for k in ["OPENAI_API_KEY", "PERPLEXITY_API_KEY", "PPLX_API_KEY",
                  "GEMINI_API_KEYS"]:
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("GEMINI_API_KEY", "g")
        monkeypatch.setenv("OPENAI_API_KEY", "o")
        app.config["AI_PROVIDER"] = "openai"
        with app.app_context():
            chain = _build_failover_chain()
        assert chain[0] == "openai"
        assert "gemini" in chain

    def test_fallback_to_gemini_when_no_keys(self, app, monkeypatch):
        for k in ["GEMINI_API_KEY", "GEMINI_API_KEYS", "OPENAI_API_KEY",
                  "PERPLEXITY_API_KEY", "PPLX_API_KEY"]:
            monkeypatch.delenv(k, raising=False)
        app.config["AI_PROVIDER"] = "gemini"
        with app.app_context():
            chain = _build_failover_chain()
        assert chain == ["gemini"]

    def test_chain_contains_only_available(self, app, monkeypatch):
        for k in ["OPENAI_API_KEY", "PERPLEXITY_API_KEY", "PPLX_API_KEY",
                  "GEMINI_API_KEYS"]:
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("GEMINI_API_KEY", "g")
        app.config["AI_PROVIDER"] = "gemini"
        with app.app_context():
            chain = _build_failover_chain()
        assert "openai" not in chain
        assert "perplexity" not in chain


# ---------------------------------------------------------------------------
# _convert_risk_level_to_score
# ---------------------------------------------------------------------------

class TestConvertRiskLevelToScore:
    def test_known_levels(self):
        assert _convert_risk_level_to_score("low") == 0.0
        assert _convert_risk_level_to_score("medium") == 0.5
        assert _convert_risk_level_to_score("high") == 0.8
        assert _convert_risk_level_to_score("crisis") == 1.0

    def test_uppercase_handled(self):
        assert _convert_risk_level_to_score("CRISIS") == 1.0

    def test_unknown_defaults_zero(self):
        assert _convert_risk_level_to_score("unknown") == 0.0


# ---------------------------------------------------------------------------
# _get_fallback_html
# ---------------------------------------------------------------------------

class TestGetFallbackHtml:
    def test_contains_basics(self, app):
        html = _get_fallback_html(app)
        assert "<html>" in html
        assert "GentleQuest" in html or "AI Mental Health" in html
        assert "/api/health" in html

    def test_references_platform(self, app):
        html = _get_fallback_html(app)
        assert "Platform" in html


# ---------------------------------------------------------------------------
# _log_tool_calls
# ---------------------------------------------------------------------------

class TestLogToolCalls:
    def test_no_raise_on_empty_list(self, app):
        _log_tool_calls("s1", [])

    def test_no_raise_on_malformed_entries(self, app):
        _log_tool_calls("s1", [{"name": "x"}, {}])


# ---------------------------------------------------------------------------
# _log_conversation
# ---------------------------------------------------------------------------

class TestLogConversation:
    def test_persists_user_and_ai_messages(self, app):
        sid = str(uuid.uuid4())
        with patch(
            "helpers.chat_helpers.AlertManager.create_alert", return_value=None
        ):
            _log_conversation(sid, "hello", "hi there", "low")
        msgs = Message.query.filter_by(session_id=sid).all()
        assert len(msgs) == 2
        user_msgs = [m for m in msgs if m.is_user]
        ai_msgs = [m for m in msgs if not m.is_user]
        assert len(user_msgs) == 1 and user_msgs[0].content == "hello"
        assert len(ai_msgs) == 1 and ai_msgs[0].content == "hi there"

    def test_triggers_alert_on_high_risk(self, app):
        sid = str(uuid.uuid4())
        with patch(
            "helpers.chat_helpers.AlertManager.create_alert", return_value=99
        ) as mock_alert:
            _log_conversation(sid, "I am hopeless", "reach out...", "high")
        mock_alert.assert_called_once()

    def test_no_alert_on_low_risk(self, app):
        sid = str(uuid.uuid4())
        with patch(
            "helpers.chat_helpers.AlertManager.create_alert"
        ) as mock_alert:
            _log_conversation(sid, "hi", "hello", "low")
        mock_alert.assert_not_called()


# ---------------------------------------------------------------------------
# _apply_layer_2_safety
# ---------------------------------------------------------------------------

class TestApplyLayer2Safety:
    def test_empty_response_short_circuits(self, app):
        with app.app_context():
            resp, blocked = _apply_layer_2_safety("u", "", "s", "low")
        assert resp == "" and blocked is False

    def test_safe_pass_through(self, app):
        with app.app_context(), patch(
            "providers.safety.check_safety_llm", return_value=(True, "ok")
        ):
            resp, blocked = _apply_layer_2_safety("u", "hi", "s", "low")
        assert resp == "hi" and blocked is False

    def test_unsafe_blocks_and_logs(self, app):
        sid = str(uuid.uuid4())
        with app.app_context(), patch(
            "providers.safety.check_safety_llm", return_value=(False, "blocked msg")
        ), patch(
            "helpers.chat_helpers.AlertManager.create_alert", return_value=None
        ):
            resp, blocked = _apply_layer_2_safety("u", "bad", sid, "low")
        assert blocked is True
        assert resp == "blocked msg"

    def test_timeout_fails_open(self, app, monkeypatch):
        # Patch executor.submit to return a future whose .result times out
        from concurrent.futures import TimeoutError as FuturesTimeoutError

        class _FakeFuture:
            def result(self, timeout):
                raise FuturesTimeoutError()

        with app.app_context(), patch(
            "helpers.chat_helpers._safety_executor.submit",
            return_value=_FakeFuture(),
        ):
            resp, blocked = _apply_layer_2_safety("u", "hi", "s", "low")
        assert resp == "hi" and blocked is False

    def test_exception_fails_open(self, app):
        with app.app_context(), patch(
            "providers.safety.check_safety_llm", side_effect=RuntimeError("x")
        ):
            resp, blocked = _apply_layer_2_safety("u", "hi", "s", "low")
        assert resp == "hi" and blocked is False


# ---------------------------------------------------------------------------
# _get_ai_response_with_failover
# ---------------------------------------------------------------------------

class TestGetAIResponseWithFailover:
    def test_first_provider_wins(self, app, monkeypatch):
        for k in ["OPENAI_API_KEY", "PERPLEXITY_API_KEY", "PPLX_API_KEY",
                  "GEMINI_API_KEYS"]:
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("GEMINI_API_KEY", "g")
        app.config["AI_PROVIDER"] = "gemini"
        with app.app_context(), patch(
            "helpers.chat_helpers._call_provider", return_value="good reply"
        ):
            resp, used = _get_ai_response_with_failover("hi", "s", "low")
        assert resp == "good reply"
        assert used == "gemini"

    def test_falls_through_to_next_provider(self, app, monkeypatch):
        for k in ["PERPLEXITY_API_KEY", "PPLX_API_KEY", "GEMINI_API_KEYS"]:
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("GEMINI_API_KEY", "g")
        monkeypatch.setenv("OPENAI_API_KEY", "o")
        app.config["AI_PROVIDER"] = "gemini"

        def fake_call(provider, *a, **kw):
            if provider == "gemini":
                return "Error generating response: quota exceeded"
            return "openai reply"

        with app.app_context(), patch(
            "helpers.chat_helpers._call_provider", side_effect=fake_call
        ):
            resp, used = _get_ai_response_with_failover("hi", "s", "low")
        assert resp == "openai reply"
        assert used == "openai"

    def test_all_fail_with_quota_returns_friendly_msg(self, app, monkeypatch):
        for k in ["OPENAI_API_KEY", "PERPLEXITY_API_KEY", "PPLX_API_KEY",
                  "GEMINI_API_KEYS"]:
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("GEMINI_API_KEY", "g")
        app.config["AI_PROVIDER"] = "gemini"
        with app.app_context(), patch(
            "helpers.chat_helpers._call_provider",
            return_value="Error generating response: 429 quota exceeded",
        ):
            resp, used = _get_ai_response_with_failover("hi", "s", "low")
        assert "limit" in resp.lower() or "try again" in resp.lower()


# ---------------------------------------------------------------------------
# _call_provider
# ---------------------------------------------------------------------------

class TestCallProvider:
    def test_routes_to_gemini(self, app):
        with app.app_context(), patch(
            "providers.gemini.get_gemini_response", return_value="g"
        ) as m:
            out = _call_provider("gemini", "hi", "s", "low")
        assert out == "g"
        m.assert_called_once()

    def test_routes_to_openai(self, app):
        with app.app_context(), patch(
            "providers.openai.get_openai_response", return_value="o"
        ) as m:
            out = _call_provider("openai", "hi", "s", "low")
        assert out == "o"
        m.assert_called_once()

    def test_unknown_provider_defaults_to_gemini(self, app):
        with app.app_context(), patch(
            "providers.gemini.get_gemini_response", return_value="fallback"
        ):
            out = _call_provider("unknown", "hi", "s", "low")
        assert out == "fallback"
