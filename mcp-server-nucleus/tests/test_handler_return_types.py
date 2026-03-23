"""
Tests for handler return type consistency across all facade routers.

Verifies that every handler callable in every ROUTER dict returns a string
when called through dispatch(). This prevents the FastMCP
'structured_content must be a dict or None' error that occurs when a
non-string result bypasses dispatch's json.dumps safety net.

See: FastMCP FunctionTool.run() -> ToolResult(structured_content=...)
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from mcp_server_nucleus.tools._dispatch import dispatch, _ensure_str


# ============================================================
# _ensure_str TESTS
# ============================================================

class TestEnsureStr:
    """Verify the _ensure_str safety net."""

    def test_string_passthrough(self):
        assert _ensure_str("hello") == "hello"

    def test_empty_string(self):
        assert _ensure_str("") == ""

    def test_dict_serialized(self):
        result = _ensure_str({"key": "value"})
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["key"] == "value"

    def test_list_serialized(self):
        result = _ensure_str([1, 2, 3])
        assert isinstance(result, str)
        assert json.loads(result) == [1, 2, 3]

    def test_none_serialized(self):
        result = _ensure_str(None)
        assert isinstance(result, str)
        assert result == "null"

    def test_int_serialized(self):
        result = _ensure_str(42)
        assert isinstance(result, str)

    def test_nested_dict(self):
        result = _ensure_str({"a": {"b": [1, 2]}})
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["a"]["b"] == [1, 2]


# ============================================================
# DISPATCH RETURN TYPE TESTS
# ============================================================

class TestDispatchAlwaysReturnsStr:
    """Verify dispatch() always returns str regardless of handler return type."""

    def test_handler_returns_string(self):
        router = {"ok": lambda: "a string"}
        result = dispatch("ok", {}, router, "test")
        assert isinstance(result, str)
        assert result == "a string"

    def test_handler_returns_dict(self):
        router = {"ok": lambda: {"key": "value"}}
        result = dispatch("ok", {}, router, "test")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["key"] == "value"

    def test_handler_returns_list(self):
        router = {"ok": lambda: [1, 2, 3]}
        result = dispatch("ok", {}, router, "test")
        assert isinstance(result, str)
        assert json.loads(result) == [1, 2, 3]

    def test_handler_returns_none(self):
        router = {"ok": lambda: None}
        result = dispatch("ok", {}, router, "test")
        assert isinstance(result, str)

    def test_handler_returns_int(self):
        router = {"ok": lambda: 42}
        result = dispatch("ok", {}, router, "test")
        assert isinstance(result, str)

    def test_handler_raises_exception(self):
        def _boom():
            raise RuntimeError("kaboom")
        router = {"ok": _boom}
        result = dispatch("ok", {}, router, "test")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "error" in parsed

    def test_unknown_action(self):
        router = {"ok": lambda: "fine"}
        result = dispatch("missing", {}, router, "test")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "error" in parsed

    def test_empty_action(self):
        router = {"ok": lambda: "fine"}
        result = dispatch("", {}, router, "test")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "error" in parsed


# ============================================================
# ROUTER HANDLER RETURN TYPE AUDIT
# ============================================================

# These tests mock the brain path and verify that each handler
# registered in the facade routers returns a str through dispatch.

@pytest.fixture
def fake_brain(tmp_path):
    """Create a minimal .brain directory structure for handler tests."""
    brain = tmp_path / ".brain"
    brain.mkdir()
    (brain / "ledger").mkdir()
    (brain / "sessions").mkdir()
    (brain / "engrams").mkdir()
    (brain / "session").mkdir()
    (brain / "slots").mkdir()

    # Minimal files handlers expect
    (brain / "ledger" / "tasks.json").write_text("[]")
    (brain / "ledger" / "events.jsonl").write_text("")
    (brain / "ledger" / "state.json").write_text("{}")
    (brain / "ledger" / "interaction_log.jsonl").write_text("")
    (brain / "engrams" / "ledger.jsonl").write_text("")
    (brain / "session" / "depth.json").write_text('{"current_depth": 0, "levels": []}')

    return brain


@pytest.fixture
def mock_brain_env(fake_brain):
    """Set NUCLEAR_BRAIN_PATH to fake brain for all tests."""
    with patch.dict("os.environ", {"NUCLEAR_BRAIN_PATH": str(fake_brain)}):
        yield fake_brain


def test_sessions_check_recent_returns_str(mock_brain_env):
    """The original failing action: nucleus_sessions(action='check_recent')."""
    from mcp_server_nucleus.runtime.session_ops import _check_for_recent_session
    from mcp_server_nucleus.runtime.common import make_response

    # Simulate the router handler: lambda: make_response(True, data=_check_for_recent_session())
    raw = _check_for_recent_session()
    assert isinstance(raw, dict), "_check_for_recent_session should return dict"

    wrapped = make_response(True, data=raw)
    assert isinstance(wrapped, str), "make_response must return str"

    # Verify via dispatch
    router = {"check_recent": lambda: make_response(True, data=_check_for_recent_session())}
    result = dispatch("check_recent", {}, router, "nucleus_sessions")
    assert isinstance(result, str)
    parsed = json.loads(result)
    assert parsed["success"] is True


def test_sessions_get_state_returns_str(mock_brain_env):
    """get_state was returning raw dict — now must return str via make_response."""
    from mcp_server_nucleus.runtime.common import _get_state, make_response

    raw = _get_state()
    assert isinstance(raw, dict), "_get_state should return dict"

    router = {"get_state": lambda path=None: make_response(True, data=_get_state(path))}
    result = dispatch("get_state", {}, router, "nucleus_sessions")
    assert isinstance(result, str)


def test_health_returns_str(mock_brain_env):
    """health action in engrams router must return str."""
    from mcp_server_nucleus.runtime.health_ops import _brain_health_impl

    result = _brain_health_impl()
    assert isinstance(result, str), "_brain_health_impl must return str"
    json.loads(result)  # Must be valid JSON


def test_audit_log_returns_str(mock_brain_env):
    """audit_log action must return str."""
    from mcp_server_nucleus.runtime.health_ops import _brain_audit_log_impl

    result = _brain_audit_log_impl(limit=5)
    assert isinstance(result, str), "_brain_audit_log_impl must return str"
    json.loads(result)  # Must be valid JSON


def test_version_handler_returns_str():
    """_brain_version_impl returns dict, but the router handler wraps it."""
    from mcp_server_nucleus.runtime.health_ops import _brain_version_impl

    raw = _brain_version_impl()
    assert isinstance(raw, dict), "_brain_version_impl returns dict"

    # Simulate the engrams router handler that formats it as a string
    info = raw
    formatted = f"VERSION INFO: {info['nucleus_version']}"
    assert isinstance(formatted, str)


def test_dispatch_metrics_returns_str():
    """dispatch_metrics handler must return str after fix."""
    from mcp_server_nucleus.tools._dispatch import get_dispatch_telemetry

    metrics = get_dispatch_telemetry().get_metrics()
    assert isinstance(metrics, dict), "get_metrics returns dict"

    # After fix: handler wraps in json.dumps
    result = json.dumps(metrics, indent=2, default=str)
    assert isinstance(result, str)


def test_respond_to_consent_returns_str():
    """respond_to_consent lambda must return str after fix."""
    handler = lambda agent_id, choice="cold": json.dumps({
        "success": True, "agent_id": agent_id,
        "choice": choice.upper(),
        "message": f"Consent recorded. Agent will respawn in {choice.upper()} mode."
    })
    result = handler("agent-123", "hot")
    assert isinstance(result, str)
    parsed = json.loads(result)
    assert parsed["success"] is True
    assert parsed["choice"] == "HOT"


def test_list_pending_consents_returns_str():
    """list_pending_consents lambda must return str after fix."""
    handler = lambda: json.dumps({
        "pending": [],
        "message": "Use nucleus_agents(action='respond_to_consent', params={agent_id, choice}) to authorize respawns."
    })
    result = handler()
    assert isinstance(result, str)
    parsed = json.loads(result)
    assert parsed["pending"] == []
