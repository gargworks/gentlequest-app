"""Tests for scripts/export_raft_training.py multi-source pipeline."""

import json
import pytest
from pathlib import Path

# Adjust sys.path so we can import from scripts/
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from export_raft_training import (
    build_sft_examples,
    build_dpo_pairs,
    sft_from_loop_turns,
    dpo_from_preference_pairs,
    build_combined,
    compute_stats,
    export,
    export_combined,
    load_shadow_log,
    load_jsonl,
)


# ── Fixtures: raw entry factories ────────────────────────────────────────

def _shadow_entry(task_id="t1", outcome="completed", query="fix bug", response="done",
                  oracle_chunks=None, ts="2026-03-01T00:00:00", **extra):
    e = {"task_id": task_id, "outcome": outcome, "query": query, "response": response,
         "ts": ts, "session_id": "s1", "total_turns": 3, "latency_ms": 500,
         "rag_context_words": 120, "format": "raft_v2"}
    if oracle_chunks is not None:
        e["oracle_chunks"] = oracle_chunks
    e.update(extra)
    return e


def _loop_turn(intent="deploy service", brother="code", outcome="success",
               actions=None, decisions=None, tools_used=None, confidence=0.9, **extra):
    e = {"turn_id": "lt1", "intent": intent, "brother": brother, "outcome": outcome,
         "actions": actions or ["ran tests"], "decisions": decisions or ["chose fast path"],
         "tools_used": tools_used or ["bash", "read"], "confidence": confidence,
         "context": "sprint 42", "timestamp": "2026-03-02T00:00:00"}
    e.update(extra)
    return e


def _pref_pair(prompt="how to deploy?", chosen="use CI", rejected="yolo push",
               pref_id="pp1", **extra):
    e = {"prompt": prompt, "chosen": chosen, "rejected": rejected,
         "pref_id": pref_id, "timestamp": "2026-03-03T00:00:00",
         "metadata": {"mined_from": "shadow_log"}}
    e.update(extra)
    return e


def _write_jsonl(path: Path, entries: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


# ── build_sft_examples ──────────────────────────────────────────────────

class TestBuildSftExamples:
    def test_filters_only_completed(self):
        entries = [
            _shadow_entry(outcome="completed", query="q1", response="r1"),
            _shadow_entry(outcome="blocked", query="q2", response="r2"),
            _shadow_entry(outcome="error", query="q3", response="r3"),
            _shadow_entry(outcome="timeout", query="q4", response="r4"),
        ]
        sft = build_sft_examples(entries)
        assert len(sft) == 1
        assert sft[0]["messages"][1]["content"] == "q1"

    def test_skips_empty_query_or_response(self):
        entries = [
            _shadow_entry(outcome="completed", query="", response="r"),
            _shadow_entry(outcome="completed", query="q", response=""),
        ]
        assert build_sft_examples(entries) == []

    def test_chat_format_structure(self):
        entries = [_shadow_entry(oracle_chunks=["chunk A", "chunk B"])]
        sft = build_sft_examples(entries)
        assert len(sft) == 1
        msgs = sft[0]["messages"]
        assert len(msgs) == 3
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"
        assert msgs[2]["role"] == "assistant"
        assert "chunk A" in msgs[0]["content"]
        assert "chunk B" in msgs[0]["content"]

    def test_metadata_fields_present(self):
        entries = [_shadow_entry(task_id="t99", session_id="s5")]
        sft = build_sft_examples(entries)
        meta = sft[0]["metadata"]
        assert meta["task_id"] == "t99"
        assert meta["session_id"] == "s5"
        assert "turns" in meta
        assert "format" in meta

    def test_system_context_without_oracle(self):
        entries = [_shadow_entry()]
        sft = build_sft_examples(entries)
        system = sft[0]["messages"][0]["content"]
        assert "expert software engineer" in system
        assert "Relevant context" not in system

    def test_empty_input(self):
        assert build_sft_examples([]) == []


# ── build_dpo_pairs ─────────────────────────────────────────────────────

class TestBuildDpoPairs:
    def test_pairs_failed_and_succeeded_on_same_task(self):
        entries = [
            _shadow_entry(task_id="t1", outcome="blocked", query="fix X", response="bad",
                          ts="2026-03-01T01:00:00"),
            _shadow_entry(task_id="t1", outcome="completed", query="fix X", response="good",
                          ts="2026-03-01T02:00:00"),
        ]
        pairs = build_dpo_pairs(entries)
        assert len(pairs) == 1
        assert pairs[0]["chosen"] == "good"
        assert pairs[0]["rejected"] == "bad"
        assert pairs[0]["metadata"]["task_id"] == "t1"

    def test_no_pair_when_failure_comes_after_success(self):
        entries = [
            _shadow_entry(task_id="t1", outcome="completed", query="q", response="good",
                          ts="2026-03-01T01:00:00"),
            _shadow_entry(task_id="t1", outcome="error", query="q", response="bad",
                          ts="2026-03-01T02:00:00"),
        ]
        pairs = build_dpo_pairs(entries)
        assert len(pairs) == 0

    def test_no_pair_across_different_tasks(self):
        entries = [
            _shadow_entry(task_id="t1", outcome="blocked", response="bad",
                          ts="2026-03-01T01:00:00"),
            _shadow_entry(task_id="t2", outcome="completed", response="good",
                          ts="2026-03-01T02:00:00"),
        ]
        pairs = build_dpo_pairs(entries)
        assert len(pairs) == 0

    def test_multiple_failures_one_success(self):
        entries = [
            _shadow_entry(task_id="t1", outcome="blocked", response="bad1",
                          ts="2026-03-01T01:00:00"),
            _shadow_entry(task_id="t1", outcome="error", response="bad2",
                          ts="2026-03-01T02:00:00"),
            _shadow_entry(task_id="t1", outcome="completed", response="good",
                          ts="2026-03-01T03:00:00"),
        ]
        pairs = build_dpo_pairs(entries)
        assert len(pairs) == 2
        assert all(p["chosen"] == "good" for p in pairs)

    def test_entries_without_task_id_ignored(self):
        entries = [
            _shadow_entry(task_id="", outcome="blocked", response="bad"),
            _shadow_entry(task_id="", outcome="completed", response="good"),
        ]
        assert build_dpo_pairs(entries) == []

    def test_empty_input(self):
        assert build_dpo_pairs([]) == []


# ── sft_from_loop_turns ─────────────────────────────────────────────────

class TestSftFromLoopTurns:
    def test_produces_valid_chat_format(self):
        entries = [_loop_turn()]
        sft = sft_from_loop_turns(entries)
        assert len(sft) == 1
        msgs = sft[0]["messages"]
        assert len(msgs) == 3
        roles = [m["role"] for m in msgs]
        assert roles == ["system", "user", "assistant"]

    def test_system_includes_brother_and_tools(self):
        entries = [_loop_turn(brother="planner", tools_used=["grep", "write"])]
        sft = sft_from_loop_turns(entries)
        system = sft[0]["messages"][0]["content"]
        assert "planner" in system
        assert "grep" in system

    def test_skips_error_and_exhausted_outcomes(self):
        entries = [
            _loop_turn(outcome="error: something failed"),
            _loop_turn(outcome="exhausted retries"),
            _loop_turn(outcome="success"),
        ]
        sft = sft_from_loop_turns(entries)
        assert len(sft) == 1

    def test_skips_empty_intent(self):
        entries = [_loop_turn(intent="")]
        assert sft_from_loop_turns(entries) == []

    def test_skips_empty_response_body(self):
        # Construct directly — factory `or` defaults replace empty lists
        entry = {"turn_id": "lt1", "intent": "do thing", "brother": "code",
                 "outcome": "", "actions": [], "decisions": [], "tools_used": [],
                 "confidence": 0.5, "context": "", "timestamp": "2026-03-02T00:00:00"}
        assert sft_from_loop_turns([entry]) == []

    def test_metadata_source_and_weight(self):
        entries = [_loop_turn(confidence=0.8)]
        meta = sft_from_loop_turns(entries)[0]["metadata"]
        assert meta["source"] == "loop_turns"
        assert meta["sampling_weight"] == 0.8

    def test_low_confidence_gets_min_weight(self):
        entries = [_loop_turn(confidence=0.02)]
        meta = sft_from_loop_turns(entries)[0]["metadata"]
        assert meta["sampling_weight"] == 0.1


# ── dpo_from_preference_pairs ───────────────────────────────────────────

class TestDpoFromPreferencePairs:
    def test_normalizes_to_dpo_format(self):
        entries = [_pref_pair()]
        pairs = dpo_from_preference_pairs(entries)
        assert len(pairs) == 1
        p = pairs[0]
        assert p["prompt"] == "how to deploy?"
        assert p["chosen"] == "use CI"
        assert p["rejected"] == "yolo push"

    def test_skips_incomplete_entries(self):
        entries = [
            _pref_pair(prompt=""),
            _pref_pair(chosen=""),
            _pref_pair(rejected=""),
        ]
        assert dpo_from_preference_pairs(entries) == []

    def test_metadata_carries_source(self):
        pairs = dpo_from_preference_pairs([_pref_pair(pref_id="pp42")])
        assert pairs[0]["metadata"]["source"] == "preference_pairs"
        assert pairs[0]["metadata"]["pref_id"] == "pp42"


# ── compute_stats ────────────────────────────────────────────────────────

class TestComputeStats:
    def test_correct_counts(self):
        entries = [
            _shadow_entry(outcome="completed", total_turns=4, latency_ms=100,
                          rag_context_words=50, task_id="t1", session_id="s1"),
            _shadow_entry(outcome="blocked", total_turns=2, latency_ms=200,
                          rag_context_words=30, task_id="t2", session_id="s1"),
            _shadow_entry(outcome="completed", total_turns=6, latency_ms=300,
                          rag_context_words=80, task_id="t1", session_id="s2"),
        ]
        sft = build_sft_examples(entries)
        dpo = build_dpo_pairs(entries)
        stats = compute_stats(entries, sft, dpo)

        assert stats["total_entries"] == 3
        assert stats["outcomes"] == {"completed": 2, "blocked": 1}
        assert stats["sft_examples"] == len(sft)
        assert stats["dpo_pairs"] == len(dpo)
        assert stats["avg_turns"] == 4.0  # (4+2+6)/3
        assert stats["avg_latency_ms"] == 200  # (100+200+300)/3
        assert stats["avg_context_words"] == 53  # round(160/3)
        assert stats["unique_tasks"] == 2
        assert stats["unique_sessions"] == 2

    def test_empty_entries_no_division_error(self):
        stats = compute_stats([], [], [])
        assert stats["total_entries"] == 0
        assert stats["avg_turns"] == 0.0


# ── build_combined ──────────────────────────────────────────────────────

class TestBuildCombined:
    def test_merges_all_sources(self):
        data = {
            "loop_turns": [_loop_turn()],
            "driver_shadow": [_shadow_entry(task_id="t1")],
            "training_shadow": [_shadow_entry(task_id="t2")],
            "preference_pairs": [_pref_pair()],
        }
        sft, dpo = build_combined(data)
        # 1 from loop_turns + 1 from driver_shadow + 1 from training_shadow
        assert len(sft) == 3
        # 0 DPO from shadow (no failures) + 1 from preference_pairs
        assert len(dpo) == 1

    def test_empty_sources(self):
        sft, dpo = build_combined({})
        assert sft == []
        assert dpo == []


# ── export & export_combined (file I/O) ─────────────────────────────────

class TestExport:
    def test_writes_valid_jsonl(self, tmp_path):
        sft = build_sft_examples([_shadow_entry()])
        dpo = build_dpo_pairs([
            _shadow_entry(task_id="t1", outcome="error", response="bad",
                          ts="2026-03-01T01:00:00"),
            _shadow_entry(task_id="t1", outcome="completed", response="good",
                          ts="2026-03-01T02:00:00"),
        ])
        stats = compute_stats([], sft, dpo)
        sft_path, dpo_path, stats_path = export(tmp_path, sft, dpo, stats)

        # Validate SFT JSONL
        lines = sft_path.read_text().strip().split("\n")
        assert len(lines) == len(sft)
        for line in lines:
            obj = json.loads(line)
            assert "messages" in obj

        # Validate DPO JSONL
        lines = dpo_path.read_text().strip().split("\n")
        assert len(lines) == len(dpo)
        for line in lines:
            obj = json.loads(line)
            assert "chosen" in obj
            assert "rejected" in obj

        # Validate stats JSON
        s = json.loads(stats_path.read_text())
        assert "exported_at" in s

    def test_export_combined_writes_files(self, tmp_path):
        sft = [{"messages": [{"role": "user", "content": "hi"}]}]
        dpo = [{"prompt": "p", "chosen": "c", "rejected": "r"}]
        sft_path, dpo_path, stats_path = export_combined(
            tmp_path, sft, dpo, {"loop_turns": 1})

        assert sft_path.exists()
        assert dpo_path.exists()
        s = json.loads(stats_path.read_text())
        assert s["sft_total"] == 1
        assert s["dpo_total"] == 1


# ── load_shadow_log / load_jsonl (file loading) ─────────────────────────

class TestLoadFiles:
    def test_load_shadow_log(self, tmp_path):
        p = tmp_path / "shadow.jsonl"
        _write_jsonl(p, [_shadow_entry(), _shadow_entry(task_id="t2")])
        entries = load_shadow_log(p)
        assert len(entries) == 2

    def test_load_shadow_log_missing(self, tmp_path):
        assert load_shadow_log(tmp_path / "nope.jsonl") == []

    def test_load_shadow_log_skips_bad_json(self, tmp_path):
        p = tmp_path / "bad.jsonl"
        p.write_text('{"ok":1}\nnot json\n{"ok":2}\n')
        entries = load_shadow_log(p)
        assert len(entries) == 2

    def test_load_jsonl(self, tmp_path):
        p = tmp_path / "data.jsonl"
        _write_jsonl(p, [{"a": 1}, {"b": 2}])
        assert len(load_jsonl(p)) == 2

    def test_load_jsonl_missing(self, tmp_path):
        assert load_jsonl(tmp_path / "nope.jsonl") == []


# ── Deduplication (same task_id, same response = one SFT example) ───────

class TestDeduplication:
    """build_sft_examples doesn't deduplicate internally, but combined
    pipeline should not produce exact duplicates when same shadow entry
    appears in both driver_shadow and training_shadow."""

    def test_identical_entries_produce_identical_output(self):
        entry = _shadow_entry(task_id="t1", query="q", response="r")
        sft1 = build_sft_examples([entry])
        sft2 = build_sft_examples([entry])
        # Same input → same content (messages + hash are deterministic;
        # processing_timestamp varies by call time, so compare by hash)
        assert sft1[0]["provenance"]["hash"] == sft2[0]["provenance"]["hash"]
        assert sft1[0]["messages"] == sft2[0]["messages"]

    def test_combined_dedup_by_content(self):
        """Verify that consumer can deduplicate by serialized messages."""
        same = _shadow_entry(task_id="t1", query="q", response="r")
        data = {
            "loop_turns": [],
            "driver_shadow": [same],
            "training_shadow": [same],
            "preference_pairs": [],
        }
        sft, _ = build_combined(data)
        # Two copies exist (one per shadow source) — consumer deduplicates
        assert len(sft) == 2
        # But they are content-identical, so set-based dedup works
        serialized = [json.dumps(s["messages"]) for s in sft]
        assert len(set(serialized)) == 1
