"""Phase 4: Autonomous Business Functions — event types, growth Deltas, brief sections.

Tests that:
1. Business event types registered in TRIGGER_EVENTS + _ARCHIVE_WORTHY_EVENTS
2. Growth gate event emission produces expected events
3. Morning brief includes growth and frontier health sections
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture
def brain(tmp_path):
    """Create a minimal .brain directory for testing."""
    b = tmp_path / ".brain"
    for d in ["ledger", "engrams", "deltas", "driver", "training"]:
        (b / d).mkdir(parents=True)
    (b / "ledger" / "events.jsonl").touch()
    (b / "ledger" / "interaction_log.jsonl").touch()
    (b / "ledger" / "activity_summary.json").write_text(json.dumps({}))
    (b / "ledger" / "triggers.json").write_text(json.dumps({"triggers": []}))
    (b / "engrams" / "ledger.jsonl").touch()
    (b / "engrams" / "hook_metrics.jsonl").touch()
    os.environ["NUCLEUS_BRAIN_PATH"] = str(b)
    os.environ["NUCLEAR_BRAIN_PATH"] = str(b)
    yield b
    os.environ.pop("NUCLEUS_BRAIN_PATH", None)
    os.environ.pop("NUCLEAR_BRAIN_PATH", None)


# ── Phase 4a: Business event registration ─────────────────────────────


class TestBusinessEventRegistration:
    """Verify Phase 4 business events are registered in engram_hooks."""

    BUSINESS_EVENTS = [
        "growth_gate_measured",
        "content_published",
        "content_performance_measured",
        "distribution_signal",
        "feature_usage_measured",
        "dogfood_entry",
    ]

    def test_all_business_events_in_trigger(self):
        from mcp_server_nucleus.runtime.engram_hooks import TRIGGER_EVENTS
        for evt in self.BUSINESS_EVENTS:
            assert evt in TRIGGER_EVENTS, f"{evt} missing from TRIGGER_EVENTS"

    def test_trigger_and_skip_still_disjoint(self):
        from mcp_server_nucleus.runtime.engram_hooks import TRIGGER_EVENTS, SKIP_EVENTS
        overlap = set(TRIGGER_EVENTS.keys()) & SKIP_EVENTS
        assert len(overlap) == 0, f"TRIGGER and SKIP overlap: {overlap}"

    def test_event_count_increased_by_6(self):
        """Phase 4 adds 6 business events to TRIGGER_EVENTS."""
        from mcp_server_nucleus.runtime.engram_hooks import TRIGGER_EVENTS
        # Phase 4 business events must all be present
        p4_count = sum(1 for e in self.BUSINESS_EVENTS if e in TRIGGER_EVENTS)
        assert p4_count == 6, f"Expected 6 Phase 4 events, found {p4_count}"

    def test_growth_gate_measured_config(self):
        from mcp_server_nucleus.runtime.engram_hooks import TRIGGER_EVENTS
        cfg = TRIGGER_EVENTS["growth_gate_measured"]
        assert cfg["context"] == "Strategy"
        assert "gate" in cfg["data_fields"]
        assert "on_track" in cfg["data_fields"]

    def test_dogfood_entry_config(self):
        from mcp_server_nucleus.runtime.engram_hooks import TRIGGER_EVENTS
        cfg = TRIGGER_EVENTS["dogfood_entry"]
        assert cfg["context"] == "Strategy"
        assert cfg["intensity"] == 7
        assert "pain_if_broken" in cfg["data_fields"]

    def test_archive_worthy_includes_business_events(self):
        """growth_gate_measured and dogfood_entry should auto-produce training data."""
        from mcp_server_nucleus.runtime.engram_hooks import _ARCHIVE_WORTHY_EVENTS
        assert "growth_gate_measured" in _ARCHIVE_WORTHY_EVENTS
        assert "dogfood_entry" in _ARCHIVE_WORTHY_EVENTS

    def test_content_events_not_archive_worthy(self):
        """Content events are lower-signal, shouldn't auto-produce training data."""
        from mcp_server_nucleus.runtime.engram_hooks import _ARCHIVE_WORTHY_EVENTS
        assert "content_published" not in _ARCHIVE_WORTHY_EVENTS
        assert "content_performance_measured" not in _ARCHIVE_WORTHY_EVENTS


# ── Phase 4b: Growth gate event emission ──────────────────────────────


class TestGrowthGateEvents:
    """Verify growth_ops emits events and Deltas for gate measurements."""

    def test_emit_growth_events_fires_per_gate(self):
        """Each gate should produce a growth_gate_measured event."""
        from mcp_server_nucleus.runtime.growth_ops import _emit_growth_events

        gates = {
            "stars": {"current": 22, "target": 100, "passed": False},
            "pip_installs_30d": {"current": 60, "target": 50, "passed": True},
        }

        with patch("mcp_server_nucleus.runtime.event_ops._emit_event") as mock_emit, \
             patch("mcp_server_nucleus.runtime.delta_ops.record_delta"):
            _emit_growth_events(gates)

            growth_calls = [
                c for c in mock_emit.call_args_list
                if c[0][0] == "growth_gate_measured"
            ]
            assert len(growth_calls) == 2
            gate_names = {c[0][2]["gate"] for c in growth_calls}
            assert gate_names == {"stars", "pip_installs_30d"}

    def test_emit_growth_events_records_deltas(self, brain):
        """Each gate should produce a Delta with direction based on on_track."""
        from mcp_server_nucleus.runtime.growth_ops import _emit_growth_events

        gates = {
            "stars": {"current": 22, "target": 100, "passed": False},
        }

        with patch("mcp_server_nucleus.runtime.event_ops._emit_event"), \
             patch("mcp_server_nucleus.runtime.delta_ops.record_delta") as mock_delta:
            _emit_growth_events(gates)

            assert mock_delta.call_count == 1
            kwargs = mock_delta.call_args[1]
            assert kwargs["frontier"] == "GROUND"
            assert "stars" in kwargs["expected_intent"]
            assert "Behind pace" in kwargs["insight"]

    def test_emit_growth_events_on_track_delta(self, brain):
        """Passing gate should produce positive insight."""
        from mcp_server_nucleus.runtime.growth_ops import _emit_growth_events

        gates = {
            "pip_installs_30d": {"current": 60, "target": 50, "passed": True},
        }

        with patch("mcp_server_nucleus.runtime.event_ops._emit_event"), \
             patch("mcp_server_nucleus.runtime.delta_ops.record_delta") as mock_delta:
            _emit_growth_events(gates)

            kwargs = mock_delta.call_args[1]
            assert "On track" in kwargs["insight"]


# ── Phase 4c: Morning brief business sections ─────────────────────────


class TestMorningBriefBusinessSections:
    """Verify morning brief includes growth and frontier health."""

    def test_retrieve_growth_status_no_data(self, brain):
        from mcp_server_nucleus.runtime.morning_brief_ops import _retrieve_growth_status
        result = _retrieve_growth_status(brain)
        assert "message" in result  # No engrams yet

    def test_retrieve_growth_status_with_engram(self, brain):
        from mcp_server_nucleus.runtime.morning_brief_ops import _retrieve_growth_status
        # Write a growth metrics engram
        ledger = brain / "engrams" / "ledger.jsonl"
        engram = {
            "key": "growth_metrics_20260402",
            "value": "stars=22, pip_30d=60, gates=2/4",
            "context": "Strategy",
            "intensity": 6,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(ledger, "w") as f:
            f.write(json.dumps(engram) + "\n")

        result = _retrieve_growth_status(brain)
        assert result.get("latest_date") == "20260402"
        assert "stars" in result.get("value", "")

    def test_retrieve_frontier_health_empty(self, brain):
        from mcp_server_nucleus.runtime.morning_brief_ops import _retrieve_frontier_health
        result = _retrieve_frontier_health(brain)
        assert "message" in result  # No data yet

    def test_retrieve_frontier_health_with_receipts(self, brain):
        from mcp_server_nucleus.runtime.morning_brief_ops import _retrieve_frontier_health
        # Write verification receipts
        vlog = brain / "verification_log.jsonl"
        receipts = [
            {"tier_reached": 3, "tiers_passed": [0, 1, 2, 3], "tiers_failed": []},
            {"tier_reached": 1, "tiers_passed": [0, 1], "tiers_failed": [2]},
        ]
        with open(vlog, "w") as f:
            for r in receipts:
                f.write(json.dumps(r) + "\n")

        result = _retrieve_frontier_health(brain)
        assert "ground" in result
        assert result["ground"]["total"] == 2
        assert result["ground"]["pass_rate"] == 50.0
