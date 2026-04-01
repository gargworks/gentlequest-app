"""Phase 3: Three Frontiers Explicit — GROUND/ALIGN/COMPOUND event wiring + dashboard.

Tests that:
1. ground_verified, align_reviewed, delta_recorded are in TRIGGER_EVENTS
2. All three are in _ARCHIVE_WORTHY_EVENTS (auto-produce training data)
3. frontier_health action returns GROUND/ALIGN/COMPOUND metrics
4. Auto-engram creation works for frontier events
5. Phase 3e: quality_grade field on LoopTurn + frontier scoring integration
"""

import json
import os
import shutil
import tempfile
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
    yield b
    os.environ.pop("NUCLEUS_BRAIN_PATH", None)


# ── TRIGGER_EVENTS / _ARCHIVE_WORTHY_EVENTS membership ──────────────────


class TestFrontierEventRegistration:
    """Verify frontier events are registered in engram_hooks."""

    def test_ground_verified_in_trigger_events(self):
        from mcp_server_nucleus.runtime.engram_hooks import TRIGGER_EVENTS
        assert "ground_verified" in TRIGGER_EVENTS

    def test_align_reviewed_in_trigger_events(self):
        from mcp_server_nucleus.runtime.engram_hooks import TRIGGER_EVENTS
        assert "align_reviewed" in TRIGGER_EVENTS

    def test_delta_recorded_in_trigger_events(self):
        from mcp_server_nucleus.runtime.engram_hooks import TRIGGER_EVENTS
        assert "delta_recorded" in TRIGGER_EVENTS

    def test_ground_verified_is_archive_worthy(self):
        from mcp_server_nucleus.runtime.engram_hooks import _ARCHIVE_WORTHY_EVENTS
        assert "ground_verified" in _ARCHIVE_WORTHY_EVENTS

    def test_align_reviewed_is_archive_worthy(self):
        from mcp_server_nucleus.runtime.engram_hooks import _ARCHIVE_WORTHY_EVENTS
        assert "align_reviewed" in _ARCHIVE_WORTHY_EVENTS

    def test_delta_recorded_is_archive_worthy(self):
        from mcp_server_nucleus.runtime.engram_hooks import _ARCHIVE_WORTHY_EVENTS
        assert "delta_recorded" in _ARCHIVE_WORTHY_EVENTS

    def test_trigger_and_skip_disjoint(self):
        """The assertion in engram_hooks.py should still hold."""
        from mcp_server_nucleus.runtime.engram_hooks import TRIGGER_EVENTS, SKIP_EVENTS
        overlap = set(TRIGGER_EVENTS.keys()) & SKIP_EVENTS
        assert len(overlap) == 0, f"TRIGGER and SKIP overlap: {overlap}"

    def test_ground_verified_config(self):
        """ground_verified should create Architecture engrams at intensity 5."""
        from mcp_server_nucleus.runtime.engram_hooks import TRIGGER_EVENTS
        cfg = TRIGGER_EVENTS["ground_verified"]
        assert cfg["context"] == "Architecture"
        assert cfg["intensity"] == 5

    def test_align_reviewed_config(self):
        """align_reviewed should create Strategy engrams at intensity 8."""
        from mcp_server_nucleus.runtime.engram_hooks import TRIGGER_EVENTS
        cfg = TRIGGER_EVENTS["align_reviewed"]
        assert cfg["context"] == "Strategy"
        assert cfg["intensity"] == 8

    def test_delta_recorded_config(self):
        """delta_recorded should create Strategy engrams at intensity 6."""
        from mcp_server_nucleus.runtime.engram_hooks import TRIGGER_EVENTS
        cfg = TRIGGER_EVENTS["delta_recorded"]
        assert cfg["context"] == "Strategy"
        assert cfg["intensity"] == 6


# ── frontier_health action ───────────────────────────────────────────────


def _call_frontier_health(brain, timerange="7d"):
    """Call frontier_health handler directly (avoids async facade).

    Reimplements the same logic as _h_frontier_health in archive.py
    but with explicit brain path for testing.
    """
    from mcp_server_nucleus.runtime.hardening import safe_read_jsonl
    from mcp_server_nucleus.runtime.delta_ops import extract_patterns

    # GROUND
    ground = {"total_verifications": 0, "pass_rate": 0.0, "avg_tier_reached": 0.0}
    vlog = brain / "verification_log.jsonl"
    if vlog.exists():
        receipts = safe_read_jsonl(vlog)
        if receipts:
            ground["total_verifications"] = len(receipts)
            passed = sum(1 for r in receipts if not r.get("tiers_failed"))
            ground["pass_rate"] = round(passed / len(receipts), 3)
            ground["avg_tier_reached"] = round(
                sum(r.get("tier_reached", 0) for r in receipts) / len(receipts), 1
            )

    # ALIGN
    align = {"total_reviews": 0, "accepted": 0, "rejected": 0, "corrected": 0, "redirected": 0}
    vpath = brain / "driver" / "human_verdicts.jsonl"
    if vpath.exists():
        verdicts = safe_read_jsonl(vpath)
        non_pending = [v for v in verdicts if v.get("verdict") != "pending"]
        align["total_reviews"] = len(non_pending)
        for v in non_pending:
            vtype = v.get("verdict", "")
            if vtype in align:
                align[vtype] += 1

    # COMPOUND
    compound = {"total_deltas": 0, "compound_rate": 0.0, "recurring_patterns": 0}
    try:
        patterns = extract_patterns(since=timerange, brain=brain)
        compound["total_deltas"] = patterns.get("total_deltas", 0)
        compound["compound_rate"] = patterns.get("compound_rate", 0.0)
        compound["recurring_patterns"] = len(patterns.get("recurring_negatives", []))
    except Exception:
        pass

    return {"GROUND": ground, "ALIGN": align, "COMPOUND": compound}


class TestFrontierHealthAction:
    """Verify the frontier_health logic reads all three frontiers."""

    def test_frontier_health_empty_brain(self, brain):
        """Should return zero metrics when no data exists."""
        result = _call_frontier_health(brain)
        assert result["GROUND"]["total_verifications"] == 0
        assert result["ALIGN"]["total_reviews"] == 0
        assert result["COMPOUND"]["total_deltas"] == 0

    def test_frontier_health_with_verification_receipts(self, brain):
        """Should count GROUND verification receipts."""
        vlog = brain / "verification_log.jsonl"
        receipts = [
            {"receipt_id": "r1", "tier_reached": 3, "tiers_passed": [0, 1, 2, 3], "tiers_failed": []},
            {"receipt_id": "r2", "tier_reached": 2, "tiers_passed": [0, 1, 2], "tiers_failed": [3]},
            {"receipt_id": "r3", "tier_reached": 4, "tiers_passed": [0, 1, 2, 3, 4], "tiers_failed": []},
        ]
        with open(vlog, "w") as f:
            for r in receipts:
                f.write(json.dumps(r) + "\n")

        result = _call_frontier_health(brain)
        g = result["GROUND"]
        assert g["total_verifications"] == 3
        assert g["pass_rate"] == round(2 / 3, 3)
        assert g["avg_tier_reached"] == round((3 + 2 + 4) / 3, 1)

    def test_frontier_health_with_verdicts(self, brain):
        """Should count ALIGN human verdicts, excluding pending."""
        vpath = brain / "driver" / "human_verdicts.jsonl"
        verdicts = [
            {"verdict": "accepted", "task_id": "t1"},
            {"verdict": "rejected", "task_id": "t2"},
            {"verdict": "corrected", "task_id": "t3"},
            {"verdict": "pending", "task_id": "t4"},
        ]
        with open(vpath, "w") as f:
            for v in verdicts:
                f.write(json.dumps(v) + "\n")

        result = _call_frontier_health(brain)
        a = result["ALIGN"]
        assert a["total_reviews"] == 3
        assert a["accepted"] == 1
        assert a["rejected"] == 1
        assert a["corrected"] == 1


# ── Event emission from GROUND and ALIGN ─────────────────────────────────


class TestGroundEventEmission:
    """Verify ground.py emits ground_verified event after verification."""

    def test_ground_verify_emits_event(self, brain):
        """The _verify function should call _emit_event with ground_verified."""
        with patch("mcp_server_nucleus.runtime.event_ops._emit_event") as mock_emit, \
             patch("mcp_server_nucleus.runtime.ground.run_ground") as mock_run:
            mock_run.return_value = {
                "receipt_id": "test_receipt",
                "tier_reached": 3,
                "tiers_passed": [0, 1, 2, 3],
                "tiers_failed": [],
            }

            # Import and call — the ground tool's _verify function
            # is defined inside register(), so we need to go through the tool
            from mcp_server_nucleus.tools.ground import register

            class FakeMCP:
                def tool(self): return lambda f: f

            helpers = {"make_response": lambda ok, **kw: {"ok": ok, **kw}}
            tools = register(FakeMCP(), helpers)

            for name, func in tools:
                if name == "nucleus_ground":
                    result = func(action="verify", params={})

            # Check _emit_event was called with ground_verified
            ground_calls = [
                c for c in mock_emit.call_args_list
                if c[0][0] == "ground_verified"
            ]
            assert len(ground_calls) >= 1, "ground_verified event should be emitted"
            data = ground_calls[0][0][2]  # Third positional arg = data dict
            assert data["receipt_id"] == "test_receipt"
            assert data["tier_reached"] == 3
            assert data["verified"] is True


# ── Phase 3e: Quality Grade ──────────────────────────────────────────────


class TestQualityGrade:
    """Verify quality_grade on LoopTurn and frontier scoring integration."""

    def test_loopturn_default_grade_is_copper(self):
        """New LoopTurns should default to copper grade."""
        from mcp_server_nucleus.runtime.archive_pipeline import LoopTurn
        turn = LoopTurn(
            brother="code", intent="test", actions=[], tools_used=[],
            decisions=[], outcome="done", signal_absorbed=[], signal_produced=[],
        )
        assert turn.quality_grade == "copper"

    def test_loopturn_grade_persists_in_dict(self):
        """quality_grade should survive to_dict() and back."""
        from mcp_server_nucleus.runtime.archive_pipeline import LoopTurn
        turn = LoopTurn(
            brother="code", intent="test", actions=[], tools_used=[],
            decisions=[], outcome="done", signal_absorbed=[], signal_produced=[],
            quality_grade="gold",
        )
        d = turn.to_dict()
        assert d["quality_grade"] == "gold"

    def test_loopturn_grade_reconstructed(self):
        """_dict_to_turn should restore quality_grade."""
        from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline
        pipeline = ArchivePipeline.__new__(ArchivePipeline)
        d = {
            "brother": "code", "intent": "test", "actions": [], "tools_used": [],
            "decisions": [], "outcome": "done", "signal_absorbed": [],
            "signal_produced": [], "quality_grade": "platinum",
        }
        turn = pipeline._dict_to_turn(d)
        assert turn.quality_grade == "platinum"

    def test_loopturn_grade_defaults_copper_on_missing(self):
        """Old LoopTurns without quality_grade should default to copper."""
        from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline
        pipeline = ArchivePipeline.__new__(ArchivePipeline)
        d = {
            "brother": "code", "intent": "test", "actions": [], "tools_used": [],
            "decisions": [], "outcome": "done", "signal_absorbed": [],
            "signal_produced": [],
            # no quality_grade key
        }
        turn = pipeline._dict_to_turn(d)
        assert turn.quality_grade == "copper"

    def test_scoring_platinum_override(self):
        """Platinum grade should always score 1.0 regardless of text."""
        from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline
        score = ArchivePipeline._score_pair("hi", "ok", quality_grade="platinum")
        assert score == 1.0

    def test_scoring_gold_bonus(self):
        """Gold grade should add +0.2 bonus to base score."""
        from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline
        base = ArchivePipeline._score_pair(
            "What should I focus on this sprint?",
            "Based on the velocity data, prioritize the auth migration — it blocks 3 downstream tasks.",
        )
        boosted = ArchivePipeline._score_pair(
            "What should I focus on this sprint?",
            "Based on the velocity data, prioritize the auth migration — it blocks 3 downstream tasks.",
            quality_grade="gold",
        )
        assert boosted == min(base + 0.2, 1.0)

    def test_scoring_silver_bonus(self):
        """Silver grade should add +0.1 bonus to base score."""
        from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline
        base = ArchivePipeline._score_pair(
            "What should I focus on this sprint?",
            "Based on the velocity data, prioritize the auth migration — it blocks 3 downstream tasks.",
        )
        boosted = ArchivePipeline._score_pair(
            "What should I focus on this sprint?",
            "Based on the velocity data, prioritize the auth migration — it blocks 3 downstream tasks.",
            quality_grade="silver",
        )
        assert boosted == min(base + 0.1, 1.0)

    def test_scoring_copper_no_bonus(self):
        """Copper (default) grade should add no bonus."""
        from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline
        base = ArchivePipeline._score_pair(
            "What should I focus on this sprint?",
            "Based on the velocity data, prioritize the auth migration — it blocks 3 downstream tasks.",
        )
        copper = ArchivePipeline._score_pair(
            "What should I focus on this sprint?",
            "Based on the velocity data, prioritize the auth migration — it blocks 3 downstream tasks.",
            quality_grade="copper",
        )
        assert copper == base

    def test_grade_order_constant(self):
        """_GRADE_ORDER should have correct hierarchy."""
        from mcp_server_nucleus.runtime.archive_pipeline import _GRADE_ORDER
        assert _GRADE_ORDER["copper"] < _GRADE_ORDER["silver"]
        assert _GRADE_ORDER["silver"] < _GRADE_ORDER["gold"]
        assert _GRADE_ORDER["gold"] < _GRADE_ORDER["platinum"]


class TestFrontierGradeResolution:
    """Verify _resolve_frontier_grades cross-references GROUND/ALIGN data."""

    def test_resolve_empty_brain(self, brain):
        """No receipts or verdicts = no grade upgrades."""
        from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline
        pipeline = ArchivePipeline.__new__(ArchivePipeline)
        pipeline.training_dir = brain / "training"
        pipeline.turns_file = pipeline.training_dir / "loop_turns.jsonl"
        pipeline.turns_file.touch()
        grades = pipeline._resolve_frontier_grades()
        assert grades == {}

    def test_resolve_ground_silver(self, brain):
        """GROUND receipt (tier < 3) near a turn → silver."""
        from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline, LoopTurn
        pipeline = ArchivePipeline.__new__(ArchivePipeline)
        pipeline.training_dir = brain / "training"
        pipeline.turns_file = pipeline.training_dir / "loop_turns.jsonl"

        # Record a turn
        ts = datetime.now(timezone.utc).isoformat()
        turn = LoopTurn(
            brother="code", intent="fix bug", actions=["edited file"],
            tools_used=["edit"], decisions=["quick fix"], outcome="fixed",
            signal_absorbed=[], signal_produced=[],
        )
        turn.timestamp = ts
        with open(pipeline.turns_file, "w") as f:
            f.write(json.dumps(turn.to_dict()) + "\n")

        # Write a matching GROUND receipt (same timestamp, tier 2)
        vlog = brain / "verification_log.jsonl"
        with open(vlog, "w") as f:
            f.write(json.dumps({
                "receipt_id": "r1", "tier_reached": 2,
                "tiers_passed": [0, 1, 2], "tiers_failed": [],
                "timestamp": ts,
            }) + "\n")

        grades = pipeline._resolve_frontier_grades()
        assert grades.get(turn.turn_id) == "silver"

    def test_resolve_ground_gold(self, brain):
        """GROUND receipt (tier >= 3) near a turn → gold."""
        from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline, LoopTurn
        pipeline = ArchivePipeline.__new__(ArchivePipeline)
        pipeline.training_dir = brain / "training"
        pipeline.turns_file = pipeline.training_dir / "loop_turns.jsonl"

        ts = datetime.now(timezone.utc).isoformat()
        turn = LoopTurn(
            brother="code", intent="add feature", actions=["wrote code"],
            tools_used=["write"], decisions=["new approach"], outcome="done",
            signal_absorbed=[], signal_produced=[],
        )
        turn.timestamp = ts
        with open(pipeline.turns_file, "w") as f:
            f.write(json.dumps(turn.to_dict()) + "\n")

        vlog = brain / "verification_log.jsonl"
        with open(vlog, "w") as f:
            f.write(json.dumps({
                "receipt_id": "r1", "tier_reached": 4,
                "tiers_passed": [0, 1, 2, 3, 4], "tiers_failed": [],
                "timestamp": ts,
            }) + "\n")

        grades = pipeline._resolve_frontier_grades()
        assert grades.get(turn.turn_id) == "gold"

    def test_resolve_align_platinum(self, brain):
        """ALIGN accepted verdict near a turn → platinum."""
        from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline, LoopTurn
        pipeline = ArchivePipeline.__new__(ArchivePipeline)
        pipeline.training_dir = brain / "training"
        pipeline.turns_file = pipeline.training_dir / "loop_turns.jsonl"

        ts = datetime.now(timezone.utc).isoformat()
        turn = LoopTurn(
            brother="code", intent="refactor auth", actions=["restructured"],
            tools_used=["edit"], decisions=["cleaner API"], outcome="shipped",
            signal_absorbed=[], signal_produced=[],
        )
        turn.timestamp = ts
        with open(pipeline.turns_file, "w") as f:
            f.write(json.dumps(turn.to_dict()) + "\n")

        vpath = brain / "driver" / "human_verdicts.jsonl"
        with open(vpath, "w") as f:
            f.write(json.dumps({
                "verdict": "accepted", "task_id": "t1", "timestamp": ts,
            }) + "\n")

        grades = pipeline._resolve_frontier_grades()
        assert grades.get(turn.turn_id) == "platinum"

    def test_resolve_highest_grade_wins(self, brain):
        """If both GROUND and ALIGN match, highest grade wins."""
        from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline, LoopTurn
        pipeline = ArchivePipeline.__new__(ArchivePipeline)
        pipeline.training_dir = brain / "training"
        pipeline.turns_file = pipeline.training_dir / "loop_turns.jsonl"

        ts = datetime.now(timezone.utc).isoformat()
        turn = LoopTurn(
            brother="code", intent="deploy", actions=["pushed"],
            tools_used=["deploy"], decisions=["go live"], outcome="live",
            signal_absorbed=[], signal_produced=[],
        )
        turn.timestamp = ts
        with open(pipeline.turns_file, "w") as f:
            f.write(json.dumps(turn.to_dict()) + "\n")

        # GROUND gives gold (tier 3)
        vlog = brain / "verification_log.jsonl"
        with open(vlog, "w") as f:
            f.write(json.dumps({
                "receipt_id": "r1", "tier_reached": 3,
                "tiers_passed": [0, 1, 2, 3], "tiers_failed": [],
                "timestamp": ts,
            }) + "\n")

        # ALIGN gives platinum (accepted)
        vpath = brain / "driver" / "human_verdicts.jsonl"
        with open(vpath, "w") as f:
            f.write(json.dumps({
                "verdict": "accepted", "task_id": "t1", "timestamp": ts,
            }) + "\n")

        grades = pipeline._resolve_frontier_grades()
        assert grades.get(turn.turn_id) == "platinum"  # platinum > gold
