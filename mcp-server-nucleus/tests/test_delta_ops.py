"""Phase 2: Delta operations — measures gaps between intent and reality.

Verifies measure_delta, record_delta, _reinvest, query_deltas,
extract_patterns, and delta_event_hook.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server_nucleus.runtime.delta_ops import (
    measure_delta,
    record_delta,
    query_deltas,
    extract_patterns,
    delta_event_hook,
    _tokenize,
    VALID_FRONTIERS,
)


@pytest.fixture
def delta_brain(tmp_path):
    """Brain with minimal infrastructure for delta tests."""
    brain = tmp_path / ".brain"
    for d in ["deltas", "engrams", "ledger", "training", "meta"]:
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


# ── Measurement Tests ─────────────────────────────────────────────────────


class TestMeasureDelta:
    """Verify Jaccard-based gap measurement between intent and reality."""

    def test_identical_strings_positive(self):
        """Identical intent and outcome → positive, magnitude 0."""
        result = measure_delta("deploy auth fix", "deploy auth fix")
        assert result["direction"] == "positive"
        assert result["magnitude"] == 0.0
        assert result["similarity"] == 1.0

    def test_completely_different_negative(self):
        """Totally different strings → negative, high magnitude."""
        result = measure_delta(
            "deploy authentication service",
            "refactor database migration scripts",
        )
        assert result["direction"] == "negative"
        assert result["magnitude"] > 0.6

    def test_partial_overlap_lateral(self):
        """Some word overlap → lateral direction."""
        result = measure_delta(
            "deploy auth fix verify tokens",
            "deploy auth fix check tokens",
        )
        assert result["direction"] in ("lateral", "positive")
        assert 0.0 < result["magnitude"] < 1.0

    def test_stop_words_removed(self):
        """Stop words should not affect similarity."""
        # "the auth is on the server" vs "auth server" — same after stop words
        result = measure_delta(
            "the auth is on the server",
            "auth server",
        )
        assert result["similarity"] >= 0.8

    def test_empty_strings_positive(self):
        """Both empty → positive (no gap, identical emptiness)."""
        result = measure_delta("", "")
        assert result["direction"] == "positive"
        assert result["magnitude"] == 0.0

    def test_one_empty_negative(self):
        """One empty, one not → negative (complete divergence)."""
        result = measure_delta("deploy auth fix", "")
        assert result["direction"] == "negative"
        assert result["magnitude"] == 1.0

    def test_returns_unique_words(self):
        """Should return words unique to each side."""
        result = measure_delta("deploy auth fix", "deploy database migration")
        assert "auth" in result["expected_unique"]
        assert "database" in result["actual_unique"] or "migration" in result["actual_unique"]

    def test_unique_words_capped_at_5(self):
        """Unique words list should be capped at 5."""
        result = measure_delta(
            "alpha bravo charlie delta echo foxtrot golf hotel india",
            "one two three four five six seven eight nine",
        )
        assert len(result["expected_unique"]) <= 5
        assert len(result["actual_unique"]) <= 5


# ── Recording Tests ───────────────────────────────────────────────────────


class TestRecordDelta:
    """Verify delta recording writes to JSONL and emits events."""

    def test_record_writes_to_jsonl(self, delta_brain):
        """Recording a delta should append to deltas.jsonl."""
        delta_id = record_delta(
            frontier="GROUND",
            expected_source="task_auth_fix",
            expected_intent="Deploy auth fix by EOD",
            actual_source="event_task_completed",
            actual_outcome="Auth fix deployed, session tokens broke",
            insight="Auth changes need session token regression test",
            brain=delta_brain,
        )

        assert delta_id is not None
        assert delta_id.startswith("d_")

        deltas_file = delta_brain / "deltas" / "deltas.jsonl"
        assert deltas_file.exists()

        lines = deltas_file.read_text().strip().splitlines()
        assert len(lines) == 1

        record = json.loads(lines[0])
        assert record["delta_id"] == delta_id
        assert record["frontier"] == "GROUND"
        assert record["expected"]["intent"] == "Deploy auth fix by EOD"
        assert record["actual"]["outcome"] == "Auth fix deployed, session tokens broke"
        assert record["delta"]["insight"] == "Auth changes need session token regression test"

    def test_record_invalid_frontier_returns_none(self, delta_brain):
        """Invalid frontier should return None without writing."""
        delta_id = record_delta(
            frontier="INVALID",
            expected_source="test",
            expected_intent="test",
            actual_source="test",
            actual_outcome="test",
            brain=delta_brain,
        )
        assert delta_id is None

        deltas_file = delta_brain / "deltas" / "deltas.jsonl"
        assert not deltas_file.exists()

    def test_record_all_valid_frontiers(self, delta_brain):
        """All three frontiers should be accepted."""
        for frontier in VALID_FRONTIERS:
            delta_id = record_delta(
                frontier=frontier,
                expected_source="test",
                expected_intent="test intent",
                actual_source="test",
                actual_outcome="test outcome",
                brain=delta_brain,
            )
            assert delta_id is not None

    def test_record_emits_event(self, delta_brain):
        """Recording should emit a delta_recorded event."""
        with patch(
            "mcp_server_nucleus.runtime.event_ops._emit_event"
        ) as mock_emit:
            record_delta(
                frontier="ALIGN",
                expected_source="brief_rec_20260401",
                expected_intent="CONTINUE auth fix",
                actual_source="session_end",
                actual_outcome="Worked on landing page instead",
                brain=delta_brain,
            )

            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == "delta_recorded"
            assert call_args[0][1] == "delta_pipeline"
            assert call_args[0][2]["frontier"] == "ALIGN"

    def test_record_computes_direction(self, delta_brain):
        """Recorded delta should have correct direction based on gap."""
        record_delta(
            frontier="GROUND",
            expected_source="test",
            expected_intent="deploy auth fix",
            actual_source="test",
            actual_outcome="deploy auth fix completed successfully",
            brain=delta_brain,
        )

        deltas_file = delta_brain / "deltas" / "deltas.jsonl"
        record = json.loads(deltas_file.read_text().strip())
        # High overlap → should be positive or lateral
        assert record["delta"]["direction"] in ("positive", "lateral")

    def test_record_creates_deltas_directory(self, tmp_path):
        """Should create .brain/deltas/ if missing."""
        brain = tmp_path / ".brain"
        brain.mkdir()
        # Minimal dirs needed for event emission
        for d in ["ledger", "engrams"]:
            (brain / d).mkdir()
        (brain / "ledger" / "events.jsonl").touch()
        (brain / "ledger" / "interaction_log.jsonl").touch()
        (brain / "ledger" / "activity_summary.json").write_text("{}")
        (brain / "ledger" / "triggers.json").write_text('{"triggers":[]}')
        (brain / "engrams" / "ledger.jsonl").touch()

        delta_id = record_delta(
            frontier="COMPOUND",
            expected_source="test",
            expected_intent="test",
            actual_source="test",
            actual_outcome="test",
            brain=brain,
        )

        assert delta_id is not None
        assert (brain / "deltas" / "deltas.jsonl").exists()

    def test_record_without_brain_returns_none(self):
        """No brain path available → return None gracefully."""
        with patch(
            "mcp_server_nucleus.runtime.delta_ops.get_brain_path",
            side_effect=ValueError("no brain"),
        ):
            delta_id = record_delta(
                frontier="GROUND",
                expected_source="test",
                expected_intent="test",
                actual_source="test",
                actual_outcome="test",
            )
            assert delta_id is None

    def test_record_with_corrections(self, delta_brain):
        """Corrections list should be stored in the delta."""
        record_delta(
            frontier="ALIGN",
            expected_source="test",
            expected_intent="use hardcoded paths",
            actual_source="human_review",
            actual_outcome="use environment variables instead",
            insight="Never hardcode paths",
            corrections=["Switched to env vars", "Added .env.example"],
            brain=delta_brain,
        )

        deltas_file = delta_brain / "deltas" / "deltas.jsonl"
        record = json.loads(deltas_file.read_text().strip())
        assert len(record["delta"]["corrections"]) == 2
        assert "env vars" in record["delta"]["corrections"][0]


# ── Reinvestment Tests ────────────────────────────────────────────────────


class TestReinvestment:
    """Verify recurring patterns create engrams and negatives create DPO."""

    def test_negative_delta_creates_dpo(self, delta_brain):
        """Negative direction should produce a DPO preference pair."""
        with patch(
            "mcp_server_nucleus.runtime.archive_pipeline.ArchivePipeline"
        ) as MockArchive:
            mock_instance = MagicMock()
            MockArchive.return_value = mock_instance

            record_delta(
                frontier="GROUND",
                expected_source="task_123",
                expected_intent="deploy microservice alpha",
                actual_source="event_failure",
                actual_outcome="refactored database completely different",
                insight="Scope creep on deploy tasks",
                brain=delta_brain,
            )

            mock_instance.record_outcome_preference.assert_called_once()
            call_kwargs = mock_instance.record_outcome_preference.call_args[1]
            assert "delta_ground_negative" in call_kwargs["event_type"]
            assert call_kwargs["success"] is False

    def test_positive_delta_no_dpo(self, delta_brain):
        """Positive direction should NOT produce a DPO pair."""
        with patch(
            "mcp_server_nucleus.runtime.archive_pipeline.ArchivePipeline"
        ) as MockArchive:
            mock_instance = MagicMock()
            MockArchive.return_value = mock_instance

            record_delta(
                frontier="GROUND",
                expected_source="test",
                expected_intent="deploy auth fix",
                actual_source="test",
                actual_outcome="deploy auth fix completed",
                insight="On track",
                brain=delta_brain,
            )

            mock_instance.record_outcome_preference.assert_not_called()

    def test_recurring_pattern_creates_engram(self, delta_brain):
        """3+ similar insights should create a Strategy engram at intensity 9."""
        # Pre-populate 3 deltas with similar insight
        deltas_path = delta_brain / "deltas" / "deltas.jsonl"
        for i in range(3):
            delta = {
                "delta_id": f"d_test_{i}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "frontier": "GROUND",
                "expected": {"source_type": "t", "source_id": "t", "intent": "t"},
                "actual": {"source_type": "t", "source_id": "t", "outcome": "t"},
                "delta": {
                    "magnitude": 0.7,
                    "direction": "negative",
                    "insight": "Auth tasks consistently underestimated by 3x",
                    "corrections": [],
                },
                "reinvestment": {},
            }
            with open(deltas_path, "a") as f:
                f.write(json.dumps(delta) + "\n")

        with patch(
            "mcp_server_nucleus.runtime.memory_pipeline.MemoryPipeline"
        ) as MockPipeline:
            mock_instance = MagicMock()
            MockPipeline.return_value = mock_instance

            record_delta(
                frontier="GROUND",
                expected_source="task_auth_4",
                expected_intent="auth deploy in 2 hours",
                actual_source="event_completed",
                actual_outcome="took 6 hours again",
                insight="Auth tasks consistently underestimated by 3x",
                brain=delta_brain,
            )

            mock_instance.process.assert_called_once()
            call_kwargs = mock_instance.process.call_args[1]
            assert call_kwargs["intensity"] == 9
            assert call_kwargs["context"] == "Strategy"
            assert "recurring_" in call_kwargs["key"]
            assert "RECURRING PATTERN" in call_kwargs["text"]


# ── Query Tests ───────────────────────────────────────────────────────────


class TestQueryDeltas:
    """Verify delta querying with filters."""

    def _write_deltas(self, brain, deltas):
        """Helper to write test deltas."""
        path = brain / "deltas" / "deltas.jsonl"
        with open(path, "w") as f:
            for d in deltas:
                f.write(json.dumps(d) + "\n")

    def test_query_returns_all(self, delta_brain):
        """Query without filters returns all deltas."""
        deltas = [
            {
                "delta_id": f"d_{i}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "frontier": "GROUND",
                "delta": {"direction": "positive"},
            }
            for i in range(5)
        ]
        self._write_deltas(delta_brain, deltas)

        result = query_deltas(brain=delta_brain)
        assert len(result) == 5

    def test_query_filter_by_frontier(self, delta_brain):
        """Should filter by frontier."""
        deltas = [
            {"delta_id": "d_1", "timestamp": datetime.now(timezone.utc).isoformat(),
             "frontier": "GROUND", "delta": {"direction": "positive"}},
            {"delta_id": "d_2", "timestamp": datetime.now(timezone.utc).isoformat(),
             "frontier": "ALIGN", "delta": {"direction": "negative"}},
            {"delta_id": "d_3", "timestamp": datetime.now(timezone.utc).isoformat(),
             "frontier": "GROUND", "delta": {"direction": "lateral"}},
        ]
        self._write_deltas(delta_brain, deltas)

        result = query_deltas(brain=delta_brain, frontier="GROUND")
        assert len(result) == 2
        assert all(d["frontier"] == "GROUND" for d in result)

    def test_query_filter_by_direction(self, delta_brain):
        """Should filter by direction."""
        deltas = [
            {"delta_id": "d_1", "timestamp": datetime.now(timezone.utc).isoformat(),
             "frontier": "GROUND", "delta": {"direction": "positive"}},
            {"delta_id": "d_2", "timestamp": datetime.now(timezone.utc).isoformat(),
             "frontier": "GROUND", "delta": {"direction": "negative"}},
        ]
        self._write_deltas(delta_brain, deltas)

        result = query_deltas(brain=delta_brain, direction="negative")
        assert len(result) == 1
        assert result[0]["delta"]["direction"] == "negative"

    def test_query_filter_by_time(self, delta_brain):
        """Should filter by time window."""
        old_ts = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        recent_ts = datetime.now(timezone.utc).isoformat()

        deltas = [
            {"delta_id": "d_old", "timestamp": old_ts,
             "frontier": "GROUND", "delta": {"direction": "positive"}},
            {"delta_id": "d_recent", "timestamp": recent_ts,
             "frontier": "GROUND", "delta": {"direction": "positive"}},
        ]
        self._write_deltas(delta_brain, deltas)

        result = query_deltas(brain=delta_brain, since="7d")
        assert len(result) == 1
        assert result[0]["delta_id"] == "d_recent"

    def test_query_respects_limit(self, delta_brain):
        """Should respect limit parameter."""
        deltas = [
            {"delta_id": f"d_{i}", "timestamp": datetime.now(timezone.utc).isoformat(),
             "frontier": "GROUND", "delta": {"direction": "positive"}}
            for i in range(10)
        ]
        self._write_deltas(delta_brain, deltas)

        result = query_deltas(brain=delta_brain, limit=3)
        assert len(result) == 3

    def test_query_most_recent_first(self, delta_brain):
        """Results should be sorted most recent first."""
        ts1 = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        ts2 = datetime.now(timezone.utc).isoformat()

        deltas = [
            {"delta_id": "d_older", "timestamp": ts1,
             "frontier": "GROUND", "delta": {"direction": "positive"}},
            {"delta_id": "d_newer", "timestamp": ts2,
             "frontier": "GROUND", "delta": {"direction": "positive"}},
        ]
        self._write_deltas(delta_brain, deltas)

        result = query_deltas(brain=delta_brain)
        assert result[0]["delta_id"] == "d_newer"

    def test_query_empty_brain(self, delta_brain):
        """Query on empty deltas should return empty list."""
        result = query_deltas(brain=delta_brain)
        assert result == []

    def test_query_missing_deltas_file(self, tmp_path):
        """Query when deltas.jsonl doesn't exist should return empty."""
        brain = tmp_path / ".brain"
        brain.mkdir()
        result = query_deltas(brain=brain)
        assert result == []


# ── Pattern Extraction Tests ──────────────────────────────────────────────


class TestExtractPatterns:
    """Verify pattern extraction from accumulated deltas."""

    def _write_deltas(self, brain, deltas):
        path = brain / "deltas" / "deltas.jsonl"
        with open(path, "w") as f:
            for d in deltas:
                f.write(json.dumps(d) + "\n")

    def test_empty_brain_returns_zeros(self, delta_brain):
        """No deltas → empty patterns."""
        result = extract_patterns(brain=delta_brain)
        assert result["compound_rate"] == 0.0
        assert result["total_deltas"] == 0
        assert result["recurring_negatives"] == []

    def test_compound_rate_calculation(self, delta_brain):
        """Compound rate = positive / total."""
        deltas = [
            {"delta_id": f"d_{i}", "timestamp": datetime.now(timezone.utc).isoformat(),
             "frontier": "GROUND",
             "delta": {"direction": "positive" if i < 3 else "negative", "insight": f"insight_{i}"}}
            for i in range(5)
        ]
        self._write_deltas(delta_brain, deltas)

        result = extract_patterns(brain=delta_brain)
        assert result["compound_rate"] == 0.6  # 3/5

    def test_frontier_health_breakdown(self, delta_brain):
        """Should compute per-frontier health metrics."""
        deltas = [
            {"delta_id": "d_1", "timestamp": datetime.now(timezone.utc).isoformat(),
             "frontier": "GROUND", "delta": {"direction": "positive", "insight": ""}},
            {"delta_id": "d_2", "timestamp": datetime.now(timezone.utc).isoformat(),
             "frontier": "GROUND", "delta": {"direction": "negative", "insight": ""}},
            {"delta_id": "d_3", "timestamp": datetime.now(timezone.utc).isoformat(),
             "frontier": "ALIGN", "delta": {"direction": "positive", "insight": ""}},
        ]
        self._write_deltas(delta_brain, deltas)

        result = extract_patterns(brain=delta_brain)
        assert result["frontier_health"]["GROUND"]["total"] == 2
        assert result["frontier_health"]["GROUND"]["positive"] == 1
        assert result["frontier_health"]["GROUND"]["rate"] == 0.5
        assert result["frontier_health"]["ALIGN"]["total"] == 1
        assert result["frontier_health"]["ALIGN"]["rate"] == 1.0

    def test_recurring_negatives_detected(self, delta_brain):
        """3+ negative deltas with similar insight → recurring pattern."""
        ts = datetime.now(timezone.utc).isoformat()
        deltas = [
            {"delta_id": f"d_{i}", "timestamp": ts,
             "frontier": "GROUND",
             "delta": {"direction": "negative",
                       "insight": "auth tasks consistently underestimated"}}
            for i in range(4)
        ]
        self._write_deltas(delta_brain, deltas)

        result = extract_patterns(brain=delta_brain)
        assert len(result["recurring_negatives"]) >= 1
        assert result["recurring_negatives"][0]["count"] >= 3

    def test_fewer_than_3_not_recurring(self, delta_brain):
        """2 similar insights should NOT be flagged as recurring."""
        ts = datetime.now(timezone.utc).isoformat()
        deltas = [
            {"delta_id": f"d_{i}", "timestamp": ts,
             "frontier": "GROUND",
             "delta": {"direction": "negative",
                       "insight": "auth tasks consistently underestimated"}}
            for i in range(2)
        ]
        self._write_deltas(delta_brain, deltas)

        result = extract_patterns(brain=delta_brain)
        assert len(result["recurring_negatives"]) == 0

    def test_filter_by_frontier(self, delta_brain):
        """Pattern extraction should respect frontier filter."""
        ts = datetime.now(timezone.utc).isoformat()
        deltas = [
            {"delta_id": "d_1", "timestamp": ts,
             "frontier": "GROUND", "delta": {"direction": "positive", "insight": ""}},
            {"delta_id": "d_2", "timestamp": ts,
             "frontier": "ALIGN", "delta": {"direction": "negative", "insight": ""}},
        ]
        self._write_deltas(delta_brain, deltas)

        result = extract_patterns(brain=delta_brain, frontier="GROUND")
        assert result["total_deltas"] == 1
        assert "GROUND" in result["frontier_health"]
        assert "ALIGN" not in result["frontier_health"]


# ── Event Hook Tests ──────────────────────────────────────────────────────


class TestDeltaEventHook:
    """Verify auto-delta creation from event hooks."""

    def test_task_completed_creates_ground_delta(self, delta_brain):
        """task_completed_with_fence should produce a GROUND delta."""
        with patch(
            "mcp_server_nucleus.runtime.delta_ops.record_delta"
        ) as mock_record:
            mock_record.return_value = "d_test"

            delta_event_hook(
                "task_completed_with_fence",
                "builder",
                {"task": "Deploy auth fix", "task_id": "t-123"},
            )

            mock_record.assert_called_once()
            call_kwargs = mock_record.call_args[1]
            assert call_kwargs["frontier"] == "GROUND"
            assert "auth fix" in call_kwargs["expected_intent"].lower()

    def test_session_ended_creates_compound_delta(self, delta_brain):
        """session_ended should produce a COMPOUND delta if brief rec exists."""
        # Write today's brief rec
        today_key = f"brief_rec_{datetime.now().strftime('%Y%m%d')}"
        with open(delta_brain / "engrams" / "ledger.jsonl", "w") as f:
            f.write(json.dumps({
                "key": today_key,
                "value": "[CONTINUE] Deploy auth fix",
                "context": "Strategy",
                "intensity": 7,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }) + "\n")

        with patch(
            "mcp_server_nucleus.runtime.delta_ops.get_brain_path",
            return_value=delta_brain,
        ):
            with patch(
                "mcp_server_nucleus.runtime.delta_ops.record_delta"
            ) as mock_record:
                mock_record.return_value = "d_test"

                delta_event_hook(
                    "session_ended",
                    "session_ops",
                    {"summary": "Worked on landing page instead"},
                )

                mock_record.assert_called_once()
                call_kwargs = mock_record.call_args[1]
                assert call_kwargs["frontier"] == "COMPOUND"

    def test_unmatched_event_ignored(self, delta_brain):
        """Events we don't track should not create deltas."""
        with patch(
            "mcp_server_nucleus.runtime.delta_ops.record_delta"
        ) as mock_record:
            delta_event_hook("engram_written", "hooks", {"key": "test"})
            mock_record.assert_not_called()

    def test_kill_switch_disables_hooks(self, delta_brain):
        """NUCLEUS_DISABLE_DELTA_HOOKS should skip all hook processing."""
        os.environ["NUCLEUS_DISABLE_DELTA_HOOKS"] = "1"
        try:
            with patch(
                "mcp_server_nucleus.runtime.delta_ops.record_delta"
            ) as mock_record:
                delta_event_hook(
                    "task_completed_with_fence",
                    "builder",
                    {"task": "test"},
                )
                mock_record.assert_not_called()
        finally:
            os.environ.pop("NUCLEUS_DISABLE_DELTA_HOOKS", None)

    def test_hook_exception_swallowed(self, delta_brain):
        """Hook should never raise — exceptions are swallowed."""
        with patch(
            "mcp_server_nucleus.runtime.delta_ops.record_delta",
            side_effect=RuntimeError("boom"),
        ):
            # Should not raise
            delta_event_hook(
                "task_completed_with_fence",
                "builder",
                {"task": "test"},
            )


# ── Tokenization Tests ────────────────────────────────────────────────────


class TestTokenize:
    """Verify word tokenization with stop word removal."""

    def test_removes_stop_words(self):
        words = _tokenize("the auth is on the server")
        assert "the" not in words
        assert "is" not in words
        assert "auth" in words
        assert "server" in words

    def test_lowercase(self):
        words = _tokenize("Deploy AUTH Fix")
        assert "deploy" in words
        assert "auth" in words
        assert "fix" in words

    def test_empty_string(self):
        words = _tokenize("")
        assert words == set()

    def test_only_stop_words(self):
        words = _tokenize("the a an is are was")
        assert words == set()


# ── Resilience Tests ──────────────────────────────────────────────────────


class TestDeltaResilience:
    """Verify graceful handling of corrupt data and edge cases."""

    def test_corrupt_deltas_file_handled(self, delta_brain):
        """Corrupt JSONL lines should be skipped."""
        path = delta_brain / "deltas" / "deltas.jsonl"
        with open(path, "w") as f:
            f.write("CORRUPT LINE\n")
            f.write(json.dumps({
                "delta_id": "d_valid",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "frontier": "GROUND",
                "delta": {"direction": "positive"},
            }) + "\n")

        result = query_deltas(brain=delta_brain)
        # Should get at least the valid record (corrupt skipped)
        assert len(result) >= 1

    def test_record_resilient_to_event_failure(self, delta_brain):
        """Delta should still be recorded even if event emission fails."""
        with patch(
            "mcp_server_nucleus.runtime.event_ops._emit_event",
            side_effect=RuntimeError("event system down"),
        ):
            delta_id = record_delta(
                frontier="GROUND",
                expected_source="test",
                expected_intent="test intent",
                actual_source="test",
                actual_outcome="test outcome",
                brain=delta_brain,
            )

            assert delta_id is not None
            assert (delta_brain / "deltas" / "deltas.jsonl").read_text().strip() != ""

    def test_record_resilient_to_reinvestment_failure(self, delta_brain):
        """Delta should still be recorded even if reinvestment fails."""
        with patch(
            "mcp_server_nucleus.runtime.delta_ops._reinvest",
            side_effect=RuntimeError("reinvestment broke"),
        ):
            delta_id = record_delta(
                frontier="GROUND",
                expected_source="test",
                expected_intent="test intent",
                actual_source="test",
                actual_outcome="test outcome",
                insight="some insight",
                brain=delta_brain,
            )

            assert delta_id is not None
