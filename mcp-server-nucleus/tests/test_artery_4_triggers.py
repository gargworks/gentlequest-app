"""Artery 4: Trigger evaluation fires on event emission.

Verifies that _emit_event evaluates triggers.json and logs matches
to activity_summary.json. Phase 1 is log-only (no dispatch).
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def trigger_brain(tmp_path):
    """Brain with triggers.json and minimal event infrastructure."""
    brain = tmp_path / ".brain"
    (brain / "ledger").mkdir(parents=True)
    (brain / "engrams").mkdir(parents=True)

    triggers = {"triggers": [
        {"event_type": "task_completed", "target_agent": "synthesizer", "emitter_filter": None},
        {"event_type": "deploy_complete", "target_agent": "devops", "emitter_filter": ["builder"]},
    ]}
    (brain / "ledger" / "triggers.json").write_text(json.dumps(triggers))
    (brain / "ledger" / "activity_summary.json").write_text(json.dumps({}))
    (brain / "ledger" / "events.jsonl").touch()
    (brain / "ledger" / "interaction_log.jsonl").touch()
    return brain


class TestArteryTriggers:
    """Verify _emit_event evaluates triggers and logs matches."""

    def test_trigger_fires_on_matching_event(self, trigger_brain):
        """task_completed should match synthesizer trigger."""
        with patch("mcp_server_nucleus.runtime.event_ops.get_brain_path",
                    return_value=trigger_brain):
            with patch("mcp_server_nucleus.runtime.trigger_ops.get_brain_path",
                        return_value=trigger_brain):
                from mcp_server_nucleus.runtime.event_ops import _emit_event
                _emit_event("task_completed", "test_slot", {"task": "test-1"})

        summary = json.loads(
            (trigger_brain / "ledger" / "activity_summary.json").read_text()
        )
        assert summary.get("trigger_match_count") == 1
        assert "synthesizer" in summary["last_trigger_match"]["matched_agents"]

    def test_no_trigger_on_unmatched_event(self, trigger_brain):
        """engram_written has no matching trigger — no trigger_match_count."""
        with patch("mcp_server_nucleus.runtime.event_ops.get_brain_path",
                    return_value=trigger_brain):
            from mcp_server_nucleus.runtime.event_ops import _emit_event
            _emit_event("engram_written", "test_slot", {})

        summary = json.loads(
            (trigger_brain / "ledger" / "activity_summary.json").read_text()
        )
        assert "trigger_match_count" not in summary

    def test_emitter_filter_respected(self, trigger_brain):
        """deploy_complete from 'builder' matches; from 'heartbeat' does not."""
        with patch("mcp_server_nucleus.runtime.event_ops.get_brain_path",
                    return_value=trigger_brain):
            with patch("mcp_server_nucleus.runtime.trigger_ops.get_brain_path",
                        return_value=trigger_brain):
                from mcp_server_nucleus.runtime.event_ops import _emit_event

                _emit_event("deploy_complete", "builder", {})
                summary = json.loads(
                    (trigger_brain / "ledger" / "activity_summary.json").read_text()
                )
                assert summary.get("trigger_match_count") == 1
                assert "devops" in summary["last_trigger_match"]["matched_agents"]

                # Reset summary
                (trigger_brain / "ledger" / "activity_summary.json").write_text(
                    json.dumps({})
                )

                _emit_event("deploy_complete", "heartbeat", {})
                summary = json.loads(
                    (trigger_brain / "ledger" / "activity_summary.json").read_text()
                )
                assert "trigger_match_count" not in summary

    def test_trigger_never_breaks_event_emission(self, trigger_brain):
        """Corrupted triggers.json must not prevent event from being written."""
        (trigger_brain / "ledger" / "triggers.json").write_text("CORRUPT")

        with patch("mcp_server_nucleus.runtime.event_ops.get_brain_path",
                    return_value=trigger_brain):
            from mcp_server_nucleus.runtime.event_ops import _emit_event
            event_id = _emit_event("task_completed", "test", {"x": 1})

        assert event_id is not None
        events = (trigger_brain / "ledger" / "events.jsonl").read_text().strip()
        assert len(events) > 0

    def test_artery_4_kill_switch(self, trigger_brain):
        """NUCLEUS_DISABLE_ARTERY_4 should skip trigger evaluation entirely."""
        os.environ["NUCLEUS_DISABLE_ARTERY_4"] = "1"
        try:
            with patch("mcp_server_nucleus.runtime.event_ops.get_brain_path",
                        return_value=trigger_brain):
                from mcp_server_nucleus.runtime.event_ops import _emit_event
                _emit_event("task_completed", "test", {})

            summary = json.loads(
                (trigger_brain / "ledger" / "activity_summary.json").read_text()
            )
            assert "trigger_match_count" not in summary
        finally:
            os.environ.pop("NUCLEUS_DISABLE_ARTERY_4", None)
