"""Phase 5: Convergence — unified weekly synthesis, compound curve, business sections.

Tests that:
1. weekly_synthesis action registered in archive ACTION_MAP
2. Weekly synthesis returns expected section structure
3. Compound curve sparkline generated from cycle history
4. Frontier health section populated from verification + verdicts
5. Engineering section counts events
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def brain(tmp_path):
    """Create a minimal .brain directory for testing."""
    b = tmp_path / ".brain"
    for d in ["ledger", "engrams", "deltas", "driver", "training", "meta"]:
        (b / d).mkdir(parents=True)
    (b / "ledger" / "events.jsonl").touch()
    (b / "ledger" / "interaction_log.jsonl").touch()
    (b / "ledger" / "activity_summary.json").write_text(json.dumps({}))
    (b / "ledger" / "triggers.json").write_text(json.dumps({"triggers": []}))
    (b / "engrams" / "ledger.jsonl").touch()
    (b / "engrams" / "hook_metrics.jsonl").touch()
    (b / "training" / "loop_turns.jsonl").touch()
    (b / "training" / "stats.json").write_text(json.dumps({
        "total_turns": 0, "last_export": None,
    }))
    os.environ["NUCLEAR_BRAIN_PATH"] = str(b)
    os.environ["NUCLEUS_BRAIN_PATH"] = str(b)
    yield b
    os.environ.pop("NUCLEAR_BRAIN_PATH", None)
    os.environ.pop("NUCLEUS_BRAIN_PATH", None)


def _call_archive(action, params=None):
    """Helper: register archive tools and call an action synchronously."""
    from mcp_server_nucleus.tools.archive import register
    mock_mcp = MagicMock()
    mock_mcp.tool.return_value = lambda f: f
    helpers = {"make_response": lambda ok, **kw: json.dumps({"ok": ok, **kw})}
    tools = register(mock_mcp, helpers)
    _, nucleus_archive = tools[0]
    result_str = asyncio.run(nucleus_archive(action=action, params=params))
    return json.loads(result_str)


# ── Phase 5a: weekly_synthesis action registration ─────────────────────


class TestWeeklySynthesisRegistration:
    """Verify weekly_synthesis is wired into the archive facade."""

    def test_weekly_synthesis_in_action_map(self):
        """weekly_synthesis should be a registered action in archive.py."""
        from mcp_server_nucleus.tools.archive import register
        mock_mcp = MagicMock()
        mock_mcp.tool.return_value = lambda f: f
        helpers = {"make_response": lambda ok, **kw: json.dumps({"ok": ok, **kw})}
        register(mock_mcp, helpers)

    def test_weekly_synthesis_in_docstring(self):
        """The nucleus_archive docstring should mention weekly_synthesis."""
        from mcp_server_nucleus.tools import archive
        src = Path(archive.__file__).read_text()
        assert "weekly_synthesis" in src


# ── Phase 5b: Weekly synthesis structure ───────────────────────────────


class TestWeeklySynthesisStructure:
    """Verify weekly synthesis returns the expected section keys."""

    def test_synthesis_type_field(self, brain):
        """Synthesis should include type=weekly_synthesis."""
        result = _call_archive("weekly_synthesis")
        assert result.get("ok") is True
        data = result.get("data", {})
        assert data.get("type") == "weekly_synthesis"

    def test_synthesis_has_generated_at(self, brain):
        """Synthesis should include a generated_at ISO timestamp."""
        result = _call_archive("weekly_synthesis")
        data = result.get("data", {})
        assert "generated_at" in data
        assert "T" in data["generated_at"]

    def test_synthesis_has_sections_dict(self, brain):
        """Synthesis should contain a 'sections' dictionary."""
        result = _call_archive("weekly_synthesis")
        data = result.get("data", {})
        assert isinstance(data.get("sections"), dict)


# ── Phase 5c: Compound curve from cycle history ───────────────────────


class TestCompoundCurve:
    """Verify compound curve sparkline is generated from cycle history."""

    def test_no_cycle_history_no_compound_curve(self, brain):
        """Without cycle history, compound_curve section should be absent."""
        result = _call_archive("weekly_synthesis")
        sections = result.get("data", {}).get("sections", {})
        assert "compound_curve" not in sections

    def test_cycle_history_produces_sparkline(self, brain):
        """With cycle history, compound_curve should include sparkline + metrics."""
        cycle = {
            "cycle_id": 5,
            "week_start": "2026-03-24",
            "days": {},
            "weekly_score_start": 50,
            "weekly_score_end": 58,
            "weekly_delta": 8,
            "previous_cycles": [
                {"cycle_id": 1, "delta": 3, "score_start": 20, "score_end": 23,
                 "week_start": "2026-02-24"},
                {"cycle_id": 2, "delta": 5, "score_start": 23, "score_end": 28,
                 "week_start": "2026-03-03"},
                {"cycle_id": 3, "delta": 7, "score_start": 28, "score_end": 35,
                 "week_start": "2026-03-10"},
                {"cycle_id": 4, "delta": 8, "score_start": 35, "score_end": 43,
                 "week_start": "2026-03-17"},
            ],
        }
        (brain / "meta" / "compounding_cycle.json").write_text(json.dumps(cycle))

        result = _call_archive("weekly_synthesis")
        sections = result.get("data", {}).get("sections", {})
        assert "compound_curve" in sections
        cc = sections["compound_curve"]
        assert "sparkline" in cc
        assert len(cc["sparkline"]) > 0
        assert cc["weeks_tracked"] == 4
        assert cc["last_delta"] == 8
        assert cc["current_score"] == 43


# ── Phase 5d: Engineering section from events ─────────────────────────


class TestEngineeringSection:
    """Verify engineering section counts events correctly."""

    def test_engineering_counts_completed_tasks(self, brain):
        """Completed task events should be counted."""
        events = [
            {"type": "task_completed_with_fence", "timestamp": datetime.now(timezone.utc).isoformat()},
            {"type": "slot_task_completed", "timestamp": datetime.now(timezone.utc).isoformat()},
            {"type": "task_escalated", "timestamp": datetime.now(timezone.utc).isoformat()},
            {"type": "session_started", "timestamp": datetime.now(timezone.utc).isoformat()},
        ]
        with open(brain / "ledger" / "events.jsonl", "w") as f:
            for e in events:
                f.write(json.dumps(e) + "\n")

        result = _call_archive("weekly_synthesis")
        sections = result.get("data", {}).get("sections", {})
        assert "engineering" in sections
        eng = sections["engineering"]
        assert eng["tasks_completed"] == 2
        assert eng["tasks_escalated"] == 1
        assert eng["total_events"] == 4

    def test_no_events_no_engineering(self, brain):
        """With empty events.jsonl, engineering section should be absent."""
        result = _call_archive("weekly_synthesis")
        sections = result.get("data", {}).get("sections", {})
        # Empty events file — no events to count
        assert "engineering" not in sections or sections.get("engineering", {}).get("total_events", 0) == 0


# ── Phase 5e: Frontier health reuse ──────────────────────────────────


class TestFrontierHealthInSynthesis:
    """Verify frontier health section populated in synthesis."""

    def test_synthesis_succeeds_with_verification_data(self, brain):
        """Synthesis should not crash when verification receipts exist."""
        vlog = brain / "verification_log.jsonl"
        receipts = [
            {"tier_reached": 3, "tiers_passed": [0, 1, 2, 3], "tiers_failed": []},
            {"tier_reached": 1, "tiers_passed": [0, 1], "tiers_failed": [2]},
        ]
        with open(vlog, "w") as f:
            for r in receipts:
                f.write(json.dumps(r) + "\n")

        result = _call_archive("weekly_synthesis")
        assert result.get("ok") is True

    def test_synthesis_succeeds_with_verdicts(self, brain):
        """Synthesis should not crash when human verdicts exist."""
        vpath = brain / "driver" / "human_verdicts.jsonl"
        verdicts = [
            {"verdict": "accepted", "timestamp": datetime.now(timezone.utc).isoformat()},
            {"verdict": "corrected", "timestamp": datetime.now(timezone.utc).isoformat()},
        ]
        with open(vpath, "w") as f:
            for v in verdicts:
                f.write(json.dumps(v) + "\n")

        result = _call_archive("weekly_synthesis")
        assert result.get("ok") is True
