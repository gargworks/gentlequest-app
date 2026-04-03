"""Tests for ALIGN — human correction frontier.

Verifies that corrections write verdicts, record deltas, create DPO pairs,
and emit events. The full loop: correct → delta → DPO → event.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture
def brain(tmp_path):
    """Create a minimal brain directory for testing."""
    b = tmp_path / ".brain"
    for d in ["ledger", "engrams", "deltas", "driver", "training"]:
        (b / d).mkdir(parents=True)
    (b / "ledger" / "events.jsonl").touch()
    (b / "ledger" / "interaction_log.jsonl").touch()
    (b / "ledger" / "activity_summary.json").write_text(json.dumps({}))
    (b / "engrams" / "ledger.jsonl").touch()
    os.environ["NUCLEUS_BRAIN_PATH"] = str(b)
    os.environ["NUCLEAR_BRAIN_PATH"] = str(b)
    yield b
    os.environ.pop("NUCLEUS_BRAIN_PATH", None)
    os.environ.pop("NUCLEAR_BRAIN_PATH", None)


class TestRecordCorrection:
    """Verify correction writes verdict, delta, DPO, event."""

    def test_verdict_written(self, brain):
        """Correction should write to human_verdicts.jsonl."""
        from mcp_server_nucleus.runtime.align_ops import record_correction

        result = record_correction(
            context="Generated SQL: UPDATE users SET role='admin'",
            correction="Always include WHERE clause: UPDATE users SET role='admin' WHERE id=123",
        )

        assert result["verdict"] == "corrected"
        assert result["verdict_id"].startswith("v-")

        verdicts_path = brain / "driver" / "human_verdicts.jsonl"
        assert verdicts_path.exists()
        verdict = json.loads(verdicts_path.read_text().strip())
        assert verdict["verdict"] == "corrected"
        assert "UPDATE users" in verdict["context"]
        assert "WHERE" in verdict["correction"]

    def test_delta_created(self, brain):
        """Correction should record an ALIGN Delta."""
        from mcp_server_nucleus.runtime.align_ops import record_correction

        result = record_correction(
            context="Wrong output",
            correction="Right output",
        )

        assert result["delta_id"] is not None

        deltas_path = brain / "deltas" / "deltas.jsonl"
        assert deltas_path.exists()
        delta = json.loads(deltas_path.read_text().strip().splitlines()[-1])
        assert delta["frontier"] == "ALIGN"

    def test_dpo_pair_created(self, brain):
        """Correction should create a DPO preference pair."""
        from mcp_server_nucleus.runtime.align_ops import record_correction

        result = record_correction(
            context="Bad code: eval(user_input)",
            correction="Safe code: ast.literal_eval(user_input)",
            expected="Parse user input safely",
        )

        assert result["pref_id"] is not None

        prefs_path = brain / "training" / "preference_pairs.jsonl"
        assert prefs_path.exists()
        pref = json.loads(prefs_path.read_text().strip().splitlines()[-1])
        assert "ast.literal_eval" in pref["chosen"]
        assert "eval(user_input)" in pref["rejected"]

    def test_event_emitted(self, brain):
        """Correction should emit align_reviewed event to events.jsonl."""
        from mcp_server_nucleus.runtime.align_ops import record_correction

        record_correction(context="wrong", correction="right")

        events_path = brain / "ledger" / "events.jsonl"
        content = events_path.read_text().strip()
        assert content, "events.jsonl should have entries"
        events = [json.loads(l) for l in content.splitlines()]
        align_events = [e for e in events if e["type"] == "align_reviewed"]
        assert len(align_events) >= 1, "align_reviewed event should be emitted"
        assert align_events[-1]["data"]["verdict"] == "corrected"

    def test_severity_recorded(self, brain):
        """Severity should be stored in verdict."""
        from mcp_server_nucleus.runtime.align_ops import record_correction

        record_correction(
            context="Dropped production table",
            correction="Never DROP TABLE without backup",
            severity="high",
        )

        verdicts_path = brain / "driver" / "human_verdicts.jsonl"
        verdict = json.loads(verdicts_path.read_text().strip())
        assert verdict["severity"] == "high"


class TestRecordApproval:
    """Verify approval writes positive signal."""

    def test_approval_written(self, brain):
        """Approval should write accepted verdict."""
        from mcp_server_nucleus.runtime.align_ops import record_approval

        result = record_approval(
            context="Generated clean, idiomatic code",
            notes="Good use of context managers",
        )

        assert result["verdict"] == "accepted"

        verdicts_path = brain / "driver" / "human_verdicts.jsonl"
        verdict = json.loads(verdicts_path.read_text().strip())
        assert verdict["verdict"] == "accepted"
        assert "context managers" in verdict["notes"]

    def test_approval_emits_event(self, brain):
        """Approval should emit align_reviewed event."""
        from mcp_server_nucleus.runtime.align_ops import record_approval

        record_approval(context="Good output")

        events_path = brain / "ledger" / "events.jsonl"
        content = events_path.read_text().strip()
        if content:
            events = [json.loads(l) for l in content.splitlines()]
            align_events = [e for e in events if e["type"] == "align_reviewed"]
            assert len(align_events) >= 1
            assert align_events[-1]["data"]["verdict"] == "accepted"


class TestAlignStats:
    """Verify stats aggregation."""

    def test_empty_stats(self, brain):
        """No verdicts should return zero stats."""
        from mcp_server_nucleus.runtime.align_ops import get_align_stats

        result = get_align_stats()
        assert result["total"] == 0

    def test_stats_with_data(self, brain):
        """Stats should count corrections and approvals."""
        from mcp_server_nucleus.runtime.align_ops import record_correction, record_approval, get_align_stats

        record_correction(context="bad", correction="good", severity="high")
        record_correction(context="bad2", correction="good2", severity="low")
        record_approval(context="great work")

        stats = get_align_stats()
        assert stats["total"] == 3
        assert stats["corrected"] == 2
        assert stats["accepted"] == 1
        assert stats["approval_rate"] == round(1 / 3, 3)
        assert stats["severity_breakdown"]["high"] == 1
        assert stats["severity_breakdown"]["low"] == 1


class TestAlignMCPTool:
    """Verify MCP tool registration."""

    def test_tool_registers(self):
        """nucleus_align should register successfully."""
        from mcp_server_nucleus.tools.align import register

        class FakeMCP:
            def tool(self): return lambda f: f

        helpers = {"make_response": lambda ok, **kw: {"ok": ok, **kw}}
        tools = register(FakeMCP(), helpers)

        names = [name for name, _ in tools]
        assert "nucleus_align" in names

    def test_correct_via_tool(self, brain):
        """nucleus_align(action='correct') should work end-to-end."""
        from mcp_server_nucleus.tools.align import register

        class FakeMCP:
            def tool(self): return lambda f: f

        helpers = {"make_response": lambda ok, **kw: {"ok": ok, **kw}}
        tools = register(FakeMCP(), helpers)

        for name, func in tools:
            if name == "nucleus_align":
                result = func(action="correct", params={
                    "context": "Missing error handling",
                    "correction": "Wrap in try/except with specific exception",
                })
                data = json.loads(result)
                assert data["verdict"] == "corrected"
                break
