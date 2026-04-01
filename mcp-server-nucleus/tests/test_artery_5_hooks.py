"""Artery 5: Extensible event hook registry.

Verifies register_event_hook() fires callbacks on _emit_event,
and that a broken hook never prevents event emission or other hooks.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def hook_brain(tmp_path):
    """Minimal brain for event emission."""
    brain = tmp_path / ".brain"
    (brain / "ledger").mkdir(parents=True)
    (brain / "engrams").mkdir(parents=True)

    (brain / "ledger" / "events.jsonl").touch()
    (brain / "ledger" / "interaction_log.jsonl").touch()
    (brain / "ledger" / "activity_summary.json").write_text(json.dumps({}))
    (brain / "ledger" / "triggers.json").write_text(json.dumps({"triggers": []}))
    return brain


@pytest.fixture(autouse=True)
def _clear_hooks():
    """Clear the hook registry before and after each test."""
    from mcp_server_nucleus.runtime.event_ops import _event_hooks
    _event_hooks.clear()
    yield
    _event_hooks.clear()


class TestArteryEventHookRegistry:
    """Verify event hook registry fires and is resilient."""

    def test_hook_fires_on_event(self, hook_brain):
        """Registered hook should be called on event emission."""
        from mcp_server_nucleus.runtime.event_ops import (
            _emit_event, register_event_hook,
        )

        received = []

        def test_hook(event_type, emitter, data):
            received.append({"type": event_type, "emitter": emitter})

        register_event_hook(test_hook)

        with patch("mcp_server_nucleus.runtime.event_ops.get_brain_path",
                    return_value=hook_brain):
            _emit_event("test_event", "test_emitter", {"key": "value"})

        assert len(received) == 1
        assert received[0]["type"] == "test_event"
        assert received[0]["emitter"] == "test_emitter"

    def test_hook_exception_doesnt_break_emission(self, hook_brain):
        """A hook that throws should not prevent the event or other hooks."""
        from mcp_server_nucleus.runtime.event_ops import (
            _emit_event, register_event_hook,
        )

        good_calls = []

        def broken_hook(event_type, emitter, data):
            raise RuntimeError("Hook broke!")

        def good_hook(event_type, emitter, data):
            good_calls.append(True)

        register_event_hook(broken_hook)
        register_event_hook(good_hook)

        with patch("mcp_server_nucleus.runtime.event_ops.get_brain_path",
                    return_value=hook_brain):
            event_id = _emit_event("test", "test", {})

        assert event_id is not None
        assert len(good_calls) == 1, "Good hook should fire after broken hook"
        events = (hook_brain / "ledger" / "events.jsonl").read_text().strip()
        assert len(events) > 0

    def test_multiple_hooks_all_fire(self, hook_brain):
        """All registered hooks should fire on every event."""
        from mcp_server_nucleus.runtime.event_ops import (
            _emit_event, register_event_hook,
        )

        counts = {"a": 0, "b": 0, "c": 0}
        register_event_hook(lambda *_: counts.update(a=counts["a"] + 1))
        register_event_hook(lambda *_: counts.update(b=counts["b"] + 1))
        register_event_hook(lambda *_: counts.update(c=counts["c"] + 1))

        with patch("mcp_server_nucleus.runtime.event_ops.get_brain_path",
                    return_value=hook_brain):
            _emit_event("test", "test", {})

        assert counts == {"a": 1, "b": 1, "c": 1}

    def test_no_hooks_is_noop(self, hook_brain):
        """With no hooks registered, event emission still works."""
        from mcp_server_nucleus.runtime.event_ops import _emit_event

        with patch("mcp_server_nucleus.runtime.event_ops.get_brain_path",
                    return_value=hook_brain):
            event_id = _emit_event("test", "test", {})

        assert event_id is not None
