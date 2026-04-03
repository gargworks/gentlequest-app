"""Tests for ambient frontier health — visible in every tool response."""

import json
import os
import time
from pathlib import Path

import pytest


@pytest.fixture
def brain(tmp_path):
    b = tmp_path / ".brain"
    for d in ["ledger", "engrams", "deltas", "driver", "training", "meta"]:
        (b / d).mkdir(parents=True)
    (b / "ledger" / "events.jsonl").touch()
    (b / "ledger" / "interaction_log.jsonl").touch()
    (b / "ledger" / "activity_summary.json").write_text(json.dumps({}))
    (b / "engrams" / "ledger.jsonl").touch()
    os.environ["NUCLEUS_BRAIN_PATH"] = str(b)
    os.environ["NUCLEAR_BRAIN_PATH"] = str(b)
    os.environ["NUCLEUS_AMBIENT_HEALTH"] = "1"
    yield b
    os.environ.pop("NUCLEUS_BRAIN_PATH", None)
    os.environ.pop("NUCLEAR_BRAIN_PATH", None)
    os.environ.pop("NUCLEUS_AMBIENT_HEALTH", None)


@pytest.fixture(autouse=True)
def clear_health_cache():
    """Reset ambient health cache between tests."""
    from mcp_server_nucleus.tools._dispatch import _health_cache
    _health_cache["line"] = ""
    _health_cache["expires"] = 0.0
    yield
    _health_cache["line"] = ""
    _health_cache["expires"] = 0.0


class TestAmbientHealthLine:
    """Test the one-line frontier health footer."""

    def test_all_dashes_when_empty(self, brain):
        from mcp_server_nucleus.tools._dispatch import _ambient_health_line
        line = _ambient_health_line()
        assert "GROUND —" in line
        assert "ALIGN —" in line
        assert "COMPOUND —" in line

    def test_shows_counts_with_data(self, brain):
        from mcp_server_nucleus.tools._dispatch import _ambient_health_line
        # Write some data
        (brain / "verification_log.jsonl").write_text('{"verified": true}\n{"verified": true}\n')
        (brain / "driver" / "human_verdicts.jsonl").write_text('{"verdict": "corrected"}\n')
        (brain / "deltas" / "deltas.jsonl").write_text('{"delta_id": "d1"}\n{"delta_id": "d2"}\n{"delta_id": "d3"}\n')

        line = _ambient_health_line()
        assert "GROUND 2" in line
        assert "ALIGN 1" in line
        assert "COMPOUND 3" in line

    def test_disabled_without_env_var(self, brain):
        from mcp_server_nucleus.tools._dispatch import _ambient_health_line
        os.environ.pop("NUCLEUS_AMBIENT_HEALTH", None)
        line = _ambient_health_line()
        assert line == ""

    def test_cache_works(self, brain):
        from mcp_server_nucleus.tools._dispatch import _ambient_health_line, _health_cache
        (brain / "verification_log.jsonl").write_text('{"verified": true}\n')

        line1 = _ambient_health_line()
        assert "GROUND 1" in line1

        # Add more data — cache should return old value
        (brain / "verification_log.jsonl").write_text('{"verified": true}\n' * 5)
        line2 = _ambient_health_line()
        assert line2 == line1  # cached

        # Expire cache
        _health_cache["expires"] = 0.0
        line3 = _ambient_health_line()
        assert "GROUND 5" in line3

    def test_silent_fail_on_bad_brain(self, brain):
        from mcp_server_nucleus.tools._dispatch import _ambient_health_line
        os.environ["NUCLEUS_BRAIN_PATH"] = "/nonexistent/path"
        os.environ["NUCLEAR_BRAIN_PATH"] = "/nonexistent/path"
        line = _ambient_health_line()
        assert line == ""  # silent fail, no crash


class TestDispatchWithHealth:
    """Test that dispatch() appends health footer."""

    def test_dispatch_appends_footer(self, brain):
        from mcp_server_nucleus.tools._dispatch import dispatch
        router = {"ping": lambda: '{"pong": true}'}
        result = dispatch("ping", {}, router, "test_tool")
        assert '{"pong": true}' in result
        assert "[frontiers:" in result

    def test_dispatch_error_no_footer(self, brain):
        from mcp_server_nucleus.tools._dispatch import dispatch
        router = {"fail": lambda: (_ for _ in ()).throw(RuntimeError("boom"))}
        result = dispatch("fail", {}, router, "test_tool")
        assert "error" in result
        # Errors should NOT have health footer
        assert "[frontiers:" not in result


class TestBrainHealthResource:
    """Test brain://health MCP resource."""

    def test_health_resource_empty(self, brain):
        """Health resource with no data should return zero counts."""
        from mcp_server_nucleus.server import register_resources
        from unittest.mock import MagicMock

        mock_mcp = MagicMock()
        resources = {}
        def fake_resource(uri):
            def decorator(func):
                resources[uri] = func
                return func
            return decorator
        mock_mcp.resource = fake_resource

        helpers = {
            "get_state": lambda: {},
            "read_events": lambda limit=10: [],
            "get_triggers_impl": None,
            "depth_show": None,
            "resource_context_impl": None,
        }
        register_resources(mock_mcp, helpers)

        assert "brain://health" in resources
        result = json.loads(resources["brain://health"]())
        assert result["ground"]["total"] == 0
        assert result["align"]["total"] == 0
        assert result["compound"]["deltas"] == 0

    def test_health_resource_with_data(self, brain):
        """Health resource should count real data."""
        from mcp_server_nucleus.server import register_resources
        from unittest.mock import MagicMock

        # Write data
        (brain / "verification_log.jsonl").write_text(
            '{"tiers_failed": []}\n{"tiers_failed": [2]}\n'
        )
        (brain / "driver" / "human_verdicts.jsonl").write_text(
            '{"verdict": "corrected"}\n{"verdict": "accepted"}\n'
        )
        (brain / "deltas" / "deltas.jsonl").write_text('{"delta_id": "d1"}\n')

        mock_mcp = MagicMock()
        resources = {}
        def fake_resource(uri):
            def decorator(func):
                resources[uri] = func
                return func
            return decorator
        mock_mcp.resource = fake_resource

        helpers = {
            "get_state": lambda: {},
            "read_events": lambda limit=10: [],
            "get_triggers_impl": None,
            "depth_show": None,
            "resource_context_impl": None,
        }
        register_resources(mock_mcp, helpers)

        result = json.loads(resources["brain://health"]())
        assert result["ground"]["total"] == 2
        assert result["ground"]["pass_rate"] == 50.0
        assert result["align"]["total"] == 2
        assert result["align"]["corrected"] == 1
        assert result["align"]["accepted"] == 1
        assert result["compound"]["deltas"] == 1
