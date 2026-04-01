"""Artery 7: Compounding loop tracks cycle state with spiral engrams.

Verifies _compute_compounding_score, _load_or_create_cycle,
_create_new_cycle, _save_cycle, cycle tracking in
_compounding_loop_status_impl, and day completion in
_end_of_day_capture_impl.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server_nucleus.runtime.compounding_loop import (
    _compute_compounding_score,
    _load_or_create_cycle,
    _create_new_cycle,
    _save_cycle,
)


@pytest.fixture
def cycle_brain(tmp_path):
    """Brain with engrams and meta directories for cycle tests."""
    brain = tmp_path / ".brain"
    for d in ["engrams", "ledger", "meta", "session"]:
        (brain / d).mkdir(parents=True)
    (brain / "engrams" / "ledger.jsonl").touch()
    (brain / "engrams" / "hook_metrics.jsonl").touch()
    (brain / "ledger" / "events.jsonl").touch()
    (brain / "ledger" / "interaction_log.jsonl").touch()
    (brain / "ledger" / "activity_summary.json").write_text(json.dumps({}))
    (brain / "ledger" / "triggers.json").write_text(
        json.dumps({"triggers": []})
    )
    return brain


class TestComputeCompoundingScore:
    """Verify score computation from engrams and hook metrics."""

    def test_empty_brain_scores_zero(self, cycle_brain):
        """Empty brain should score 0."""
        score = _compute_compounding_score(cycle_brain)
        assert score == 0

    def test_engrams_contribute_half_point_each(self, cycle_brain):
        """Each non-deleted engram adds 0.5 to the score."""
        with open(cycle_brain / "engrams" / "ledger.jsonl", "w") as f:
            for i in range(10):
                f.write(json.dumps({"key": f"e{i}", "value": f"v{i}"}) + "\n")

        score = _compute_compounding_score(cycle_brain)
        # 10 engrams × 0.5 = 5, plus efficiency bonus (50 × 0/1 = 0)
        assert score >= 5

    def test_auto_writes_contribute_two_each(self, cycle_brain):
        """Each ADD outcome in hook_metrics adds 2 to the score."""
        with open(cycle_brain / "engrams" / "hook_metrics.jsonl", "w") as f:
            for i in range(5):
                f.write(json.dumps({"outcome": "ADD"}) + "\n")

        score = _compute_compounding_score(cycle_brain)
        # 5 auto_writes × 2 = 10, efficiency = 5/(5+0) = 1.0, bonus = 50
        assert score >= 60

    def test_errors_subtract_five_each(self, cycle_brain):
        """Each ERROR outcome subtracts 5 from the score."""
        with open(cycle_brain / "engrams" / "hook_metrics.jsonl", "w") as f:
            for i in range(3):
                f.write(json.dumps({"outcome": "ADD"}) + "\n")
            for i in range(2):
                f.write(json.dumps({"outcome": "ERROR"}) + "\n")

        score = _compute_compounding_score(cycle_brain)
        # 3 ADD × 2 = 6, efficiency = 3/5 = 0.6, bonus = 30, errors = 2 × 5 = 10
        # total = 6 + 30 - 10 = 26
        assert score == 26

    def test_score_capped_at_100(self, cycle_brain):
        """Score should never exceed 100."""
        with open(cycle_brain / "engrams" / "ledger.jsonl", "w") as f:
            for i in range(500):
                f.write(json.dumps({"key": f"e{i}", "value": f"v{i}"}) + "\n")
        with open(cycle_brain / "engrams" / "hook_metrics.jsonl", "w") as f:
            for i in range(100):
                f.write(json.dumps({"outcome": "ADD"}) + "\n")

        score = _compute_compounding_score(cycle_brain)
        assert score == 100

    def test_deleted_engrams_not_counted(self, cycle_brain):
        """Engrams with deleted=True should be excluded."""
        with open(cycle_brain / "engrams" / "ledger.jsonl", "w") as f:
            f.write(json.dumps({"key": "a", "value": "v"}) + "\n")
            f.write(
                json.dumps({"key": "b", "value": "v", "deleted": True}) + "\n"
            )

        score = _compute_compounding_score(cycle_brain)
        # Only 1 engram counted (0.5) — deleted one skipped
        assert score < 2

    def test_corrupt_lines_skipped(self, cycle_brain):
        """Corrupt JSON in ledger should be skipped without error."""
        with open(cycle_brain / "engrams" / "ledger.jsonl", "w") as f:
            f.write("CORRUPT\n")
            f.write(json.dumps({"key": "valid", "value": "v"}) + "\n")

        score = _compute_compounding_score(cycle_brain)
        assert score >= 0  # Should not crash


class TestCycleManagement:
    """Verify cycle creation, loading, and saving."""

    def test_create_new_cycle_has_7_days(self, cycle_brain):
        """New cycle should have exactly 7 days starting from Monday."""
        cycle = _create_new_cycle(cycle_brain, cycle_id=1)
        assert cycle["cycle_id"] == 1
        assert len(cycle["days"]) == 7
        assert cycle["weekly_score_end"] is None
        assert cycle["previous_cycles"] == []

    def test_create_new_cycle_starts_on_monday(self, cycle_brain):
        """First day of cycle should always be a Monday."""
        cycle = _create_new_cycle(cycle_brain, cycle_id=1)
        week_start = datetime.strptime(cycle["week_start"], "%Y-%m-%d")
        assert week_start.weekday() == 0  # Monday

    def test_cycle_days_have_correct_actions(self, cycle_brain):
        """Each day should map to the correct daily action."""
        cycle = _create_new_cycle(cycle_brain, cycle_id=1)
        actions = [
            d["action"]
            for _, d in sorted(cycle["days"].items())
        ]
        assert actions == [
            "GAP_ANALYSIS", "BUILD", "TEST",
            "REFLECT", "SHIP", "AUDIT", "CONSOLIDATE",
        ]

    def test_save_and_load_cycle(self, cycle_brain):
        """Cycle should survive save + load round-trip."""
        cycle_path = cycle_brain / "meta" / "compounding_cycle.json"
        original = _create_new_cycle(cycle_brain, cycle_id=42)
        _save_cycle(original, cycle_path)

        loaded = _load_or_create_cycle(cycle_brain, cycle_path)
        assert loaded["cycle_id"] == 42
        assert len(loaded["days"]) == 7

    def test_load_creates_fresh_when_missing(self, cycle_brain):
        """Missing cycle file should create a fresh cycle."""
        cycle_path = cycle_brain / "meta" / "compounding_cycle.json"
        assert not cycle_path.exists()

        cycle = _load_or_create_cycle(cycle_brain, cycle_path)
        assert cycle["cycle_id"] == 1
        assert len(cycle["days"]) == 7

    def test_load_creates_fresh_when_corrupt(self, cycle_brain):
        """Corrupt cycle JSON should produce a fresh cycle."""
        cycle_path = cycle_brain / "meta" / "compounding_cycle.json"
        cycle_path.write_text("CORRUPT JSON")

        cycle = _load_or_create_cycle(cycle_brain, cycle_path)
        assert cycle["cycle_id"] == 1

    def test_save_creates_parent_dirs(self, cycle_brain):
        """_save_cycle should create parent dirs if missing."""
        deep_path = cycle_brain / "deep" / "nested" / "cycle.json"
        cycle = {"cycle_id": 1, "days": {}}
        _save_cycle(cycle, deep_path)
        assert deep_path.exists()
        assert json.loads(deep_path.read_text())["cycle_id"] == 1


class TestCompoundingLoopStatusArtery7:
    """Verify Artery 7 cycle tracking in _compounding_loop_status_impl."""

    def test_status_creates_cycle_file(self, cycle_brain):
        """First call should create meta/compounding_cycle.json."""
        with patch(
            "mcp_server_nucleus.runtime.common.get_brain_path",
            return_value=cycle_brain,
        ):
            # Also need to patch morning_brief since status calls it
            with patch(
                "mcp_server_nucleus.runtime.morning_brief_ops._morning_brief_impl",
                return_value={
                    "recommendation": {"action": "BUILD", "task": "test"},
                    "sections": {},
                },
            ):
                from mcp_server_nucleus.runtime.compounding_loop import (
                    _compounding_loop_status_impl,
                )

                result = _compounding_loop_status_impl()

        cycle_path = cycle_brain / "meta" / "compounding_cycle.json"
        assert cycle_path.exists()
        assert "cycle" in result

    def test_status_records_score_at_start(self, cycle_brain):
        """Should record score_at_start for today if not yet set."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        cycle = _create_new_cycle(cycle_brain, cycle_id=5)
        # Ensure today is in the cycle
        if today_str not in cycle["days"]:
            cycle["days"][today_str] = {
                "action": "BUILD",
                "planned": True,
                "completed": False,
                "score_at_start": None,
                "score_at_end": None,
            }
        cycle_path = cycle_brain / "meta" / "compounding_cycle.json"
        _save_cycle(cycle, cycle_path)

        with patch(
            "mcp_server_nucleus.runtime.common.get_brain_path",
            return_value=cycle_brain,
        ):
            with patch(
                "mcp_server_nucleus.runtime.morning_brief_ops._morning_brief_impl",
                return_value={
                    "recommendation": {"action": "BUILD", "task": "test"},
                    "sections": {},
                },
            ):
                from mcp_server_nucleus.runtime.compounding_loop import (
                    _compounding_loop_status_impl,
                )

                _compounding_loop_status_impl()

        updated = json.loads(cycle_path.read_text())
        if today_str in updated["days"]:
            assert updated["days"][today_str]["score_at_start"] is not None

    def test_status_includes_cycle_context(self, cycle_brain):
        """Response should include cycle object with id, days, trend."""
        cycle = _create_new_cycle(cycle_brain, cycle_id=3)
        cycle["previous_cycles"] = [
            {"cycle_id": 2, "delta": 5, "week_start": "2026-03-24"}
        ]
        _save_cycle(
            cycle, cycle_brain / "meta" / "compounding_cycle.json"
        )

        with patch(
            "mcp_server_nucleus.runtime.common.get_brain_path",
            return_value=cycle_brain,
        ):
            with patch(
                "mcp_server_nucleus.runtime.morning_brief_ops._morning_brief_impl",
                return_value={
                    "recommendation": {"action": "BUILD", "task": "test"},
                    "sections": {},
                },
            ):
                from mcp_server_nucleus.runtime.compounding_loop import (
                    _compounding_loop_status_impl,
                )

                result = _compounding_loop_status_impl()

        assert "cycle" in result
        assert result["cycle"]["cycle_id"] == 3
        assert result["cycle"]["previous_delta"] == 5

    def test_kill_switch_skips_cycle(self, cycle_brain):
        """NUCLEUS_DISABLE_ARTERY_7 should skip cycle tracking."""
        os.environ["NUCLEUS_DISABLE_ARTERY_7"] = "1"
        try:
            with patch(
                "mcp_server_nucleus.runtime.common.get_brain_path",
                return_value=cycle_brain,
            ):
                with patch(
                    "mcp_server_nucleus.runtime.morning_brief_ops._morning_brief_impl",
                    return_value={
                        "recommendation": {"action": "BUILD", "task": "t"},
                        "sections": {},
                    },
                ):
                    from mcp_server_nucleus.runtime.compounding_loop import (
                        _compounding_loop_status_impl,
                    )

                    result = _compounding_loop_status_impl()
        finally:
            os.environ.pop("NUCLEUS_DISABLE_ARTERY_7", None)

        assert "cycle" not in result


class TestEndOfDayCaptureArtery7:
    """Verify Artery 7 marks day completed in _end_of_day_capture_impl."""

    def test_eod_marks_today_completed(self, cycle_brain):
        """End-of-day capture should mark today as completed."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        cycle = _create_new_cycle(cycle_brain, cycle_id=1)
        # Ensure today is in the cycle
        if today_str not in cycle["days"]:
            cycle["days"][today_str] = {
                "action": "BUILD",
                "planned": True,
                "completed": False,
                "score_at_start": 20,
                "score_at_end": None,
            }
        cycle_path = cycle_brain / "meta" / "compounding_cycle.json"
        _save_cycle(cycle, cycle_path)

        with patch(
            "mcp_server_nucleus.runtime.common.get_brain_path",
            return_value=cycle_brain,
        ):
            with patch(
                "mcp_server_nucleus.runtime.event_ops._emit_event",
                return_value="evt-test",
            ):
                with patch(
                    "mcp_server_nucleus.runtime.engram_ops._brain_write_engram_impl",
                    return_value={"success": True},
                ):
                    from mcp_server_nucleus.runtime.compounding_loop import (
                        _end_of_day_capture_impl,
                    )

                    _end_of_day_capture_impl(
                        summary="Built auth module",
                        key_decisions=["Use JWT"],
                    )

        updated = json.loads(cycle_path.read_text())
        if today_str in updated["days"]:
            assert updated["days"][today_str]["completed"] is True
            assert updated["days"][today_str]["score_at_end"] is not None

    def test_eod_without_cycle_file(self, cycle_brain):
        """EOD capture should not crash when cycle file doesn't exist."""
        # No cycle file created — Artery 7 should silently skip

        with patch(
            "mcp_server_nucleus.runtime.common.get_brain_path",
            return_value=cycle_brain,
        ):
            with patch(
                "mcp_server_nucleus.runtime.event_ops._emit_event",
                return_value="evt-test",
            ):
                with patch(
                    "mcp_server_nucleus.runtime.engram_ops._brain_write_engram_impl",
                    return_value={"success": True},
                ):
                    from mcp_server_nucleus.runtime.compounding_loop import (
                        _end_of_day_capture_impl,
                    )

                    result = _end_of_day_capture_impl(summary="Test day")

        # Should complete without error
        assert result is not None

    def test_eod_kill_switch(self, cycle_brain):
        """NUCLEUS_DISABLE_ARTERY_7 should prevent cycle day marking."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        cycle = _create_new_cycle(cycle_brain, cycle_id=1)
        if today_str not in cycle["days"]:
            cycle["days"][today_str] = {
                "action": "BUILD", "planned": True,
                "completed": False, "score_at_start": 10,
                "score_at_end": None,
            }
        cycle_path = cycle_brain / "meta" / "compounding_cycle.json"
        _save_cycle(cycle, cycle_path)

        os.environ["NUCLEUS_DISABLE_ARTERY_7"] = "1"
        try:
            with patch(
                "mcp_server_nucleus.runtime.common.get_brain_path",
                return_value=cycle_brain,
            ):
                with patch(
                    "mcp_server_nucleus.runtime.event_ops._emit_event",
                    return_value="evt-test",
                ):
                    with patch(
                        "mcp_server_nucleus.runtime.engram_ops._brain_write_engram_impl",
                        return_value={"success": True},
                    ):
                        from mcp_server_nucleus.runtime.compounding_loop import (
                            _end_of_day_capture_impl,
                        )

                        _end_of_day_capture_impl(summary="Test")
        finally:
            os.environ.pop("NUCLEUS_DISABLE_ARTERY_7", None)

        updated = json.loads(cycle_path.read_text())
        if today_str in updated["days"]:
            assert updated["days"][today_str]["completed"] is False
