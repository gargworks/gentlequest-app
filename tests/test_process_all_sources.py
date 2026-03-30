"""Tests for .brain/training/process_all_sources.py pipeline steps."""

import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pytest

# ── Make the module importable ──────────────────────────────────────
PIPELINE_DIR = Path(__file__).resolve().parent.parent / ".brain" / "training"
sys.path.insert(0, str(PIPELINE_DIR))

import process_all_sources as P


# ═══════════════════════════════════════════════════════════════════════
# 1. Deduplication — SHA-256 content_hash
# ═══════════════════════════════════════════════════════════════════════


class TestDeduplication:
    """content_hash produces stable 16-char hex, whitespace is normalised."""

    def test_same_text_same_hash(self):
        assert P.content_hash("hello world") == P.content_hash("hello world")

    def test_whitespace_normalised(self):
        """Tabs, newlines, and multi-space collapse to single space."""
        assert P.content_hash("a   b\tc\nd") == P.content_hash("a b c d")

    def test_hash_length_is_16(self):
        assert len(P.content_hash("anything")) == 16

    def test_different_text_different_hash(self):
        assert P.content_hash("alpha") != P.content_hash("bravo")

    def test_truncation_at_length(self):
        """Only first `length` chars matter."""
        base = "x" * 200
        assert P.content_hash(base + "A", length=200) == P.content_hash(base + "B", length=200)

    def test_truncation_differs_when_within_length(self):
        assert P.content_hash("AB", length=200) != P.content_hash("AC", length=200)

    def test_global_hash_dedup_in_shadow_log(self, tmp_path):
        """Duplicate entries in shadow_log are skipped via global_hashes."""
        shadow = tmp_path / "shadow_log.jsonl"
        entry = {
            "query": "Explain the nucleus architecture design",
            "response": "The nucleus architecture is a layered design with " + "x" * 60,
            "ts": "2026-03-10",
            "outcome": "completed",
            "task_title": "explain arch",
        }
        shadow.write_text(json.dumps(entry) + "\n" + json.dumps(entry) + "\n")

        orig_file = P.SHADOW_LOG_FILE
        orig_dir = P.DRIVER_DIR
        P.SHADOW_LOG_FILE = shadow
        P.DRIVER_DIR = tmp_path  # isolate from real runs.jsonl
        try:
            stats = P.Stats()
            sft, _ = P.process_shadow_log(set(), set(), stats)
            assert len(sft) == 1
            assert stats.skipped_dedup == 1
        finally:
            P.SHADOW_LOG_FILE = orig_file
            P.DRIVER_DIR = orig_dir


# ═══════════════════════════════════════════════════════════════════════
# 2. Quality tagging — gold / silver / copper
# ═══════════════════════════════════════════════════════════════════════


class TestQualityScoring:
    """score_quality assigns gold/silver/copper based on turns, length, provenance."""

    def _msgs(self, pairs, system="sys"):
        """Build messages list from (role, content) pairs."""
        msgs = [{"role": "system", "content": system}]
        for role, content in pairs:
            msgs.append({"role": role, "content": content})
        return msgs

    def test_gold_human_multi_turn_domain(self):
        """Human, 3+ non-system turns, avg_len >= 200, domain-relevant."""
        long_text = "The nucleus MCP tool architecture " + "a " * 150
        msgs = self._msgs([
            ("user", long_text),
            ("assistant", long_text),
            ("user", long_text),
            ("assistant", long_text),
        ])
        assert P.score_quality(msgs, "human_initiated", "test") == "gold"

    def test_silver_human_short(self):
        """Human-initiated but average length < 200 → silver."""
        medium = "This is a moderately sized message about topics " + "w " * 40
        msgs = self._msgs([("user", medium), ("assistant", medium)])
        assert P.score_quality(msgs, "human_initiated", "test") == "silver"

    def test_copper_trivial(self):
        """Very short or single-turn → copper."""
        msgs = self._msgs([("user", "ok")])
        assert P.score_quality(msgs, "human_initiated", "test") == "copper"

    def test_silver_ai_high_quality_domain(self):
        """AI-generated but long + domain-relevant → silver."""
        long_text = "The nucleus brain heartbeat design " + "a " * 150
        msgs = self._msgs([
            ("user", long_text),
            ("assistant", long_text),
            ("user", long_text),
        ])
        assert P.score_quality(msgs, "ai_generated", "test") == "silver"

    def test_copper_very_short_avg(self):
        """avg_len < 30 → copper regardless of provenance."""
        msgs = self._msgs([("user", "hi"), ("assistant", "yo")])
        assert P.score_quality(msgs, "human_initiated", "test") == "copper"


# ═══════════════════════════════════════════════════════════════════════
# 3. Temporal decay weighting
# ═══════════════════════════════════════════════════════════════════════


class TestTemporalWeight:
    """Exponential decay relative to REFERENCE_DATE (2026-03-18)."""

    def test_same_day_weight_is_one(self):
        w = P.temporal_weight("2026-03-18")
        assert w == pytest.approx(1.0, abs=0.01)

    def test_30_days_old_weight_is_03(self):
        """Config says 0.3 at 30 days old."""
        w = P.temporal_weight("2026-02-16")
        assert w == pytest.approx(0.3, abs=0.02)

    def test_recent_beats_old(self):
        recent = P.temporal_weight("2026-03-15")
        old = P.temporal_weight("2025-12-01")
        assert recent > old

    def test_future_date_clamped_to_one(self):
        """days_old clamped to 0 via max(0, ...) → weight = 1.0."""
        w = P.temporal_weight("2027-01-01")
        assert w == pytest.approx(1.0, abs=0.01)

    def test_iso_format_with_T(self):
        w = P.temporal_weight("2026-03-18T12:00:00Z")
        assert w == pytest.approx(1.0, abs=0.01)

    def test_invalid_date_returns_fallback(self):
        assert P.temporal_weight("not-a-date") == 0.5

    def test_floor_is_001(self):
        """Very old dates floor at 0.01."""
        w = P.temporal_weight("2020-01-01")
        assert w == pytest.approx(0.01, abs=0.005)


# ═══════════════════════════════════════════════════════════════════════
# 4. Shadow log processing
# ═══════════════════════════════════════════════════════════════════════


class TestShadowLog:
    """process_shadow_log reads JSONL, dedup/filters, tags quality."""

    def _write_shadow(self, tmp_path, entries):
        f = tmp_path / "shadow_log.jsonl"
        f.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
        return f

    def _isolate_shadow(self, tmp_path, entries):
        """Patch both SHADOW_LOG_FILE and DRIVER_DIR to isolate from real data."""
        shadow_file = self._write_shadow(tmp_path, entries)
        orig_file = P.SHADOW_LOG_FILE
        orig_dir = P.DRIVER_DIR
        P.SHADOW_LOG_FILE = shadow_file
        P.DRIVER_DIR = tmp_path  # backfill_shadow_entries won't find runs.jsonl here
        return orig_file, orig_dir

    def _restore(self, orig_file, orig_dir):
        P.SHADOW_LOG_FILE = orig_file
        P.DRIVER_DIR = orig_dir

    def test_basic_extraction(self, tmp_path):
        entry = {
            "query": "Refactor the MCP handler to support streaming",
            "response": "I refactored the MCP handler with streaming support, details: " + "z" * 200,
            "ts": "2026-03-10",
            "outcome": "completed",
            "task_title": "refactor mcp",
        }
        orig_file, orig_dir = self._isolate_shadow(tmp_path, [entry])
        try:
            stats = P.Stats()
            sft, dpo = P.process_shadow_log(set(), set(), stats)
            assert len(sft) == 1
            assert sft[0]["source"] == "shadow_driver"
            assert sft[0]["quality"] == "gold"
            assert sft[0]["temporal_weight"] > 0
            assert len(sft[0]["messages"]) == 3  # system + user + assistant
        finally:
            self._restore(orig_file, orig_dir)

    def test_short_response_skipped(self, tmp_path):
        entry = {
            "query": "Do something with the build system configuration",
            "response": "ok",
            "ts": "2026-03-10",
            "outcome": "completed",
            "task_title": "task",
        }
        orig_file, orig_dir = self._isolate_shadow(tmp_path, [entry])
        try:
            stats = P.Stats()
            sft, _ = P.process_shadow_log(set(), set(), stats)
            assert len(sft) == 0
            assert stats.skipped_empty >= 1
        finally:
            self._restore(orig_file, orig_dir)

    def test_credential_stripped(self, tmp_path):
        entry = {
            "query": "Set api_key=sk-abcdefghijklmnopqrstuvwxyz1234567890ABCD",
            "response": "Done, I configured the key in the settings file " + "z" * 60,
            "ts": "2026-03-10",
            "outcome": "completed",
            "task_title": "creds",
        }
        orig_file, orig_dir = self._isolate_shadow(tmp_path, [entry])
        try:
            stats = P.Stats()
            sft, _ = P.process_shadow_log(set(), set(), stats)
            assert len(sft) == 0
        finally:
            self._restore(orig_file, orig_dir)

    def test_contamination_firewall(self, tmp_path):
        query = "What is the capital of France"
        entry = {
            "query": query,
            "response": "The capital of France is Paris and more details " + "z" * 60,
            "ts": "2026-03-10",
            "outcome": "completed",
            "task_title": "geo",
        }
        orig_file, orig_dir = self._isolate_shadow(tmp_path, [entry])
        eval_hashes = {P.prompt_hash_16(query)}
        try:
            stats = P.Stats()
            sft, _ = P.process_shadow_log(set(), eval_hashes, stats)
            assert len(sft) == 0
            assert stats.skipped_contaminated == 1
        finally:
            self._restore(orig_file, orig_dir)

    def test_completed_long_is_gold(self, tmp_path):
        entry = {
            "query": "Implement the full nucleus brain pipeline handler",
            "response": "Implemented the full pipeline: " + "w" * 250,
            "ts": "2026-03-10",
            "outcome": "completed",
            "task_title": "pipeline",
        }
        orig_file, orig_dir = self._isolate_shadow(tmp_path, [entry])
        try:
            sft, _ = P.process_shadow_log(set(), set(), P.Stats())
            assert sft[0]["quality"] == "gold"
        finally:
            self._restore(orig_file, orig_dir)

    def test_completed_short_is_silver(self, tmp_path):
        entry = {
            "query": "Update the heartbeat config for the brain agent",
            "response": "Updated the heartbeat config as requested " + "w" * 20,
            "ts": "2026-03-10",
            "outcome": "completed",
            "task_title": "heartbeat",
        }
        orig_file, orig_dir = self._isolate_shadow(tmp_path, [entry])
        try:
            sft, _ = P.process_shadow_log(set(), set(), P.Stats())
            assert sft[0]["quality"] == "silver"
        finally:
            self._restore(orig_file, orig_dir)

    def test_missing_file_returns_empty(self, tmp_path):
        orig_file = P.SHADOW_LOG_FILE
        orig_dir = P.DRIVER_DIR
        P.SHADOW_LOG_FILE = tmp_path / "nonexistent.jsonl"
        P.DRIVER_DIR = tmp_path
        try:
            sft, dpo = P.process_shadow_log(set(), set(), P.Stats())
            assert sft == []
            assert dpo == []
        finally:
            P.SHADOW_LOG_FILE = orig_file
            P.DRIVER_DIR = orig_dir


# ═══════════════════════════════════════════════════════════════════════
# 5. Session filtering (skipped sessions in claude_code_transcripts)
# ═══════════════════════════════════════════════════════════════════════


class TestSessionFiltering:
    """process_claude_code_transcripts skips noise, short, and credential turns."""

    def _write_session(self, session_dir, name, lines):
        """Write a session JSONL file with the given JSON objects."""
        f = session_dir / f"{name}.jsonl"
        f.write_text("\n".join(json.dumps(l) for l in lines) + "\n")
        return f

    def test_skip_noise_user_messages(self, tmp_path):
        """'Continue', 'ok', empty strings are filtered from turns."""
        project = tmp_path / "proj"
        project.mkdir()
        ts = int(datetime(2026, 3, 15, tzinfo=timezone.utc).timestamp() * 1000)
        lines = [
            {"type": "user", "timestamp": ts, "promptId": "p1",
             "message": {"content": "Continue"}},
            {"type": "assistant", "timestamp": ts,
             "message": {"content": [{"type": "text", "text": "Some long assistant response with enough chars " + "w" * 100}]}},
            {"type": "user", "timestamp": ts, "promptId": "p2",
             "message": {"content": "Refactor the nucleus MCP tool handler for better streaming"}},
            {"type": "assistant", "timestamp": ts,
             "message": {"content": [{"type": "text", "text": "I refactored the handler for streaming with these changes " + "w" * 100}]}},
        ]
        self._write_session(project, "sess1", lines)

        orig = P.CLAUDE_CODE_SESSIONS_DIR
        P.CLAUDE_CODE_SESSIONS_DIR = tmp_path
        try:
            stats = P.Stats()
            sft, _ = P.process_claude_code_transcripts(set(), set(), stats)
            # "Continue" is skipped — only the real user turn remains as a pair
            assert len(sft) == 1
            user_msgs = [m for m in sft[0]["messages"] if m["role"] == "user"]
            for m in user_msgs:
                assert m["content"] != "Continue"
        finally:
            P.CLAUDE_CODE_SESSIONS_DIR = orig

    def test_short_pair_skipped(self, tmp_path):
        """User text < 15 chars or assistant text < 30 chars → skipped."""
        project = tmp_path / "proj"
        project.mkdir()
        ts = int(datetime(2026, 3, 15, tzinfo=timezone.utc).timestamp() * 1000)
        lines = [
            {"type": "user", "timestamp": ts, "promptId": "p1",
             "message": {"content": "hi"}},
            {"type": "assistant", "timestamp": ts,
             "message": {"content": [{"type": "text", "text": "hey"}]}},
        ]
        self._write_session(project, "sess2", lines)

        orig = P.CLAUDE_CODE_SESSIONS_DIR
        P.CLAUDE_CODE_SESSIONS_DIR = tmp_path
        try:
            sft, _ = P.process_claude_code_transcripts(set(), set(), P.Stats())
            assert len(sft) == 0
        finally:
            P.CLAUDE_CODE_SESSIONS_DIR = orig

    def test_credential_turn_skipped(self, tmp_path):
        """Turns containing API keys are dropped."""
        project = tmp_path / "proj"
        project.mkdir()
        ts = int(datetime(2026, 3, 15, tzinfo=timezone.utc).timestamp() * 1000)
        lines = [
            {"type": "user", "timestamp": ts, "promptId": "p1",
             "message": {"content": "Set the secret_key=supersecretvalue123 in the config"}},
            {"type": "assistant", "timestamp": ts,
             "message": {"content": [{"type": "text", "text": "Done, I set the key in your config file as requested " + "w" * 50}]}},
        ]
        self._write_session(project, "sess3", lines)

        orig = P.CLAUDE_CODE_SESSIONS_DIR
        P.CLAUDE_CODE_SESSIONS_DIR = tmp_path
        try:
            sft, _ = P.process_claude_code_transcripts(set(), set(), P.Stats())
            assert len(sft) == 0
        finally:
            P.CLAUDE_CODE_SESSIONS_DIR = orig

    def test_backup_file_skipped(self, tmp_path):
        """Files ending in .backup.jsonl are ignored."""
        project = tmp_path / "proj"
        project.mkdir()
        ts = int(datetime(2026, 3, 15, tzinfo=timezone.utc).timestamp() * 1000)
        lines = [
            {"type": "user", "timestamp": ts, "promptId": "p1",
             "message": {"content": "Implement the full nucleus brain architecture for MCP tools"}},
            {"type": "assistant", "timestamp": ts,
             "message": {"content": [{"type": "text", "text": "Implemented the brain architecture " + "w" * 100}]}},
        ]
        # Filename pattern: foo.backup.jsonl — stem is "foo.backup"
        self._write_session(project, "sess4.backup", lines)

        orig = P.CLAUDE_CODE_SESSIONS_DIR
        P.CLAUDE_CODE_SESSIONS_DIR = tmp_path
        try:
            sft, _ = P.process_claude_code_transcripts(set(), set(), P.Stats())
            assert len(sft) == 0
        finally:
            P.CLAUDE_CODE_SESSIONS_DIR = orig


# ═══════════════════════════════════════════════════════════════════════
# 6. Pipeline output count after dedup + filtering
# ═══════════════════════════════════════════════════════════════════════


class TestPipelineOutputCount:
    """End-to-end: shadow_log entries → SFT count matches after dedup + filter."""

    def test_mixed_entries_count(self, tmp_path):
        """3 entries: 1 valid, 1 duplicate, 1 too-short → output = 1."""
        good = {
            "query": "Explain the nucleus MCP tool architecture in detail",
            "response": "The nucleus MCP tool architecture consists of " + "x" * 80,
            "ts": "2026-03-10",
            "outcome": "completed",
            "task_title": "arch",
        }
        dupe = dict(good)  # exact duplicate
        short = {
            "query": "What is the current deployment status check",
            "response": "fine",
            "ts": "2026-03-10",
            "outcome": "completed",
            "task_title": "status",
        }
        f = tmp_path / "shadow_log.jsonl"
        f.write_text("\n".join(json.dumps(e) for e in [good, dupe, short]) + "\n")

        orig_file = P.SHADOW_LOG_FILE
        orig_dir = P.DRIVER_DIR
        P.SHADOW_LOG_FILE = f
        P.DRIVER_DIR = tmp_path
        try:
            stats = P.Stats()
            sft, _ = P.process_shadow_log(set(), set(), stats)
            assert len(sft) == 1
            assert stats.skipped_dedup == 1
            assert stats.skipped_empty >= 1
        finally:
            P.SHADOW_LOG_FILE = orig_file
            P.DRIVER_DIR = orig_dir

    def test_pre_seeded_hash_deduplicates(self, tmp_path):
        """Entry whose hash is already in global_hashes is skipped."""
        entry = {
            "query": "Describe the brain heartbeat monitoring system setup",
            "response": "The heartbeat monitoring system is configured " + "x" * 80,
            "ts": "2026-03-10",
            "outcome": "completed",
            "task_title": "heartbeat",
        }
        f = tmp_path / "shadow_log.jsonl"
        f.write_text(json.dumps(entry) + "\n")

        pre_hash = P.content_hash(entry["query"] + entry["response"])
        orig_file = P.SHADOW_LOG_FILE
        orig_dir = P.DRIVER_DIR
        P.SHADOW_LOG_FILE = f
        P.DRIVER_DIR = tmp_path
        try:
            stats = P.Stats()
            sft, _ = P.process_shadow_log({pre_hash}, set(), stats)
            assert len(sft) == 0
            assert stats.skipped_dedup == 1
        finally:
            P.SHADOW_LOG_FILE = orig_file
            P.DRIVER_DIR = orig_dir

    def test_multi_session_transcript_count(self, tmp_path):
        """Two sessions, each with one valid pair → 2 SFT examples."""
        ts = int(datetime(2026, 3, 15, tzinfo=timezone.utc).timestamp() * 1000)
        for i in range(2):
            project = tmp_path / f"proj{i}"
            project.mkdir()
            # Content must be long enough that serialised JSONL > 500 bytes
            lines = [
                {"type": "user", "timestamp": ts, "promptId": f"p{i}",
                 "message": {"content": f"Implement feature {i} for the nucleus brain agent system " + "x" * 200}},
                {"type": "assistant", "timestamp": ts,
                 "message": {"content": [{"type": "text", "text": f"Implemented feature {i} with full test coverage and docs " + "w" * 200}]}},
            ]
            (project / f"sess{i}.jsonl").write_text(
                "\n".join(json.dumps(l) for l in lines) + "\n"
            )

        orig = P.CLAUDE_CODE_SESSIONS_DIR
        P.CLAUDE_CODE_SESSIONS_DIR = tmp_path
        try:
            sft, _ = P.process_claude_code_transcripts(set(), set(), P.Stats())
            assert len(sft) == 2
        finally:
            P.CLAUDE_CODE_SESSIONS_DIR = orig


# ═══════════════════════════════════════════════════════════════════════
# 7. Helpers
# ═══════════════════════════════════════════════════════════════════════


class TestHelpers:
    def test_make_id_format(self):
        mid = P.make_id("shadow_driver", "some text")
        assert mid.startswith("shadow_driver_")
        assert len(mid.split("_", 2)[-1]) == 8

    def test_detect_category_nucleus(self):
        assert P.detect_category("the nucleus brain heartbeat fired") == "nucleus"

    def test_detect_category_general_fallback(self):
        assert P.detect_category("random unrelated content xyz") == "general"

    def test_is_contaminated_true(self):
        text = "eval prompt 42"
        h = P.prompt_hash_16(text)
        assert P.is_contaminated(text, {h}) is True

    def test_is_contaminated_false(self):
        assert P.is_contaminated("safe prompt", set()) is False

    def test_prompt_hash_16_case_insensitive(self):
        assert P.prompt_hash_16("Hello World") == P.prompt_hash_16("hello world")


# ═══════════════════════════════════════════════════════════════════════
# 8. Siphon noise cleaning — clean_siphon_text + is_siphon_noise
# ═══════════════════════════════════════════════════════════════════════


class TestCleanSiphonText:
    """clean_siphon_text strips editor/view/URI noise, preserves content."""

    def test_strips_edited_relevant_file(self):
        text = "Some intro\n*Edited relevant file*\nMeaningful content here"
        cleaned = P.clean_siphon_text(text)
        assert "*Edited relevant file*" not in cleaned
        assert "Meaningful content here" in cleaned

    def test_strips_edited_n_files(self):
        text = "*Edited 3 files*\nActual work done here"
        cleaned = P.clean_siphon_text(text)
        assert "*Edited 3 files*" not in cleaned
        assert "Actual work done here" in cleaned

    def test_strips_viewed_lines(self):
        text = "*Viewed [some_file.py](http://example.com/some_file.py) *\nReal text follows"
        cleaned = P.clean_siphon_text(text)
        assert "*Viewed" not in cleaned
        assert "Real text follows" in cleaned

    def test_strips_viewed_without_trailing_space(self):
        text = "*Viewed [config.json](http://host/config.json)*\nContent"
        cleaned = P.clean_siphon_text(text)
        assert "*Viewed" not in cleaned
        assert "Content" in cleaned

    def test_strips_file_uri_inline(self):
        text = "Check file:///Users/lokesh/app/main.py for details"
        cleaned = P.clean_siphon_text(text)
        assert "file:///" not in cleaned
        assert "Check" in cleaned
        assert "for details" in cleaned

    def test_strips_file_uri_parenthesized(self):
        text = "See (file:///tmp/output.log) for results"
        cleaned = P.clean_siphon_text(text)
        assert "file:///" not in cleaned
        assert "See" in cleaned

    def test_preserves_meaningful_content(self):
        text = "The nucleus brain architecture consists of layered components.\nEach layer handles specific concerns."
        cleaned = P.clean_siphon_text(text)
        assert cleaned == text

    def test_collapses_excessive_blank_lines(self):
        text = "Line one\n\n\n\n\nLine two"
        cleaned = P.clean_siphon_text(text)
        assert "\n\n\n" not in cleaned
        assert "Line one" in cleaned
        assert "Line two" in cleaned


class TestIsSiphonNoise:
    """is_siphon_noise returns True for predominantly noisy text."""

    def test_true_for_high_hard_noise_density(self):
        """More than 30% hard noise lines → True."""
        lines = [
            "<tool_use>invoke something</tool_use>",
            "<tool_result>result</tool_result>",
            "<tool_use>another call</tool_use>",
            "one real line of content",
        ]
        text = "\n".join(lines)
        assert P.is_siphon_noise(text) is True

    def test_true_for_text_cleaning_to_short(self):
        """After cleaning, text < 60 chars → True."""
        text = "*Edited relevant file*\n*Edited 2 files*\nok"
        assert P.is_siphon_noise(text) is True

    def test_false_for_meaningful_content(self):
        """Text with real content survives cleaning → False."""
        text = "The nucleus brain architecture handles task routing, heartbeat monitoring, and multi-agent coordination."
        assert P.is_siphon_noise(text) is False

    def test_true_for_empty_text(self):
        assert P.is_siphon_noise("") is True

    def test_false_for_long_clean_text(self):
        text = "This is a detailed explanation of the MCP tool pipeline. " * 3
        assert P.is_siphon_noise(text) is False

    def test_ansi_codes_count_as_hard_noise(self):
        lines = [
            "\x1b[31mred text\x1b[0m",
            "\x1b[32mgreen text\x1b[0m",
            "\x1b[33myellow text\x1b[0m",
            "one clean line",
        ]
        text = "\n".join(lines)
        # 3/4 lines have hard noise → >30%
        assert P.is_siphon_noise(text) is True


# ═══════════════════════════════════════════════════════════════════════
# 9. generate_natural_prompt — deterministic prompt from title
# ═══════════════════════════════════════════════════════════════════════


class TestGenerateNaturalPrompt:
    """generate_natural_prompt produces deterministic, natural prompts."""

    def test_deterministic_same_title(self):
        """Same title always produces the same prompt."""
        a = P.generate_natural_prompt("nucleus_chat_setup")
        b = P.generate_natural_prompt("nucleus_chat_setup")
        assert a == b

    def test_deterministic_across_calls(self):
        """Determinism via SHA-256, not Python hash()."""
        results = {P.generate_natural_prompt("test_title") for _ in range(10)}
        assert len(results) == 1

    def test_camelcase_splitting(self):
        """CamelCase titles are split into words."""
        prompt = P.generate_natural_prompt("NucleusChatSetup")
        assert "Nucleus Chat Setup" in prompt

    def test_underscore_replacement(self):
        """Underscores become spaces."""
        prompt = P.generate_natural_prompt("brain_heartbeat_config")
        assert "_" not in prompt
        assert "brain heartbeat config" in prompt

    def test_hyphen_replacement(self):
        """Hyphens become spaces."""
        prompt = P.generate_natural_prompt("mcp-tool-handler")
        assert "-" not in prompt
        assert "mcp tool handler" in prompt

    def test_dot_replacement(self):
        """Dots become spaces."""
        prompt = P.generate_natural_prompt("process.all.sources")
        assert "process all sources" in prompt

    def test_no_part_suffix_for_single_chunk(self):
        """When total_chunks == 1, no part suffix is added."""
        prompt = P.generate_natural_prompt("some_topic", chunk_idx=0, total_chunks=1)
        assert "Part" not in prompt

    def test_part_suffix_when_multi_chunk(self):
        """When total_chunks > 1, part suffix is appended."""
        prompt = P.generate_natural_prompt("some_topic", chunk_idx=2, total_chunks=5)
        assert "(Part 3 of 5)" in prompt

    def test_part_suffix_first_chunk(self):
        prompt = P.generate_natural_prompt("doc", chunk_idx=0, total_chunks=3)
        assert "(Part 1 of 3)" in prompt

    def test_output_is_from_templates(self):
        """Output matches one of NATURAL_PROMPT_TEMPLATES (with topic substituted)."""
        prompt = P.generate_natural_prompt("test_topic")
        topic = "test topic"
        matched = any(
            prompt == tmpl.format(topic=topic)
            for tmpl in P.NATURAL_PROMPT_TEMPLATES
        )
        assert matched, f"Prompt {prompt!r} does not match any template"


# ═══════════════════════════════════════════════════════════════════════
# 10. semantic_dedup — MinHash + LSH near-duplicate removal
# ═══════════════════════════════════════════════════════════════════════


class TestSemanticDedup:
    """semantic_dedup removes near-duplicate entries using MinHash + LSH."""

    def _make_entry(self, text, quality="silver"):
        return {
            "messages": [
                {"role": "system", "content": "system"},
                {"role": "user", "content": "question"},
                {"role": "assistant", "content": text},
            ],
            "quality": quality,
        }

    def test_removes_near_duplicates(self):
        """Paraphrased entries with high overlap are removed."""
        base = "the nucleus brain architecture handles task routing and heartbeat monitoring across multiple agents in the system"
        entry1 = self._make_entry(base)
        # Near-duplicate: same words, slightly reordered suffix
        entry2 = self._make_entry(base + " for production workloads")
        result = P.semantic_dedup([entry1, entry2], jaccard_threshold=0.5)
        assert len(result) == 1

    def test_keeps_higher_quality_on_duplicate(self):
        """When duplicates found, gold beats silver."""
        base = "the nucleus brain architecture handles task routing and heartbeat monitoring across multiple agents in the system"
        silver = self._make_entry(base, quality="silver")
        gold = self._make_entry(base + " for production", quality="gold")
        result = P.semantic_dedup([silver, gold], jaccard_threshold=0.5)
        assert len(result) == 1
        assert result[0]["quality"] == "gold"

    def test_preserves_distinct_entries(self):
        """Non-duplicate entries are all preserved."""
        e1 = self._make_entry("the nucleus brain architecture handles task routing and heartbeat monitoring across agents")
        e2 = self._make_entry("python flask web application deployment requires gunicorn nginx and ssl certificate setup")
        e3 = self._make_entry("machine learning model training uses gradient descent with backpropagation through neural network layers")
        result = P.semantic_dedup([e1, e2, e3], jaccard_threshold=0.5)
        assert len(result) == 3

    def test_empty_list_input(self):
        """Empty list returns empty list."""
        assert P.semantic_dedup([]) == []

    def test_handles_empty_assistant_content(self):
        """Entries with empty assistant messages don't crash."""
        e1 = self._make_entry("")
        e2 = self._make_entry("the nucleus brain architecture handles task routing and monitoring across multiple agents")
        result = P.semantic_dedup([e1, e2], jaccard_threshold=0.5)
        # Both survive since empty text can't be a duplicate of real content
        assert len(result) >= 1

    def test_graceful_without_numpy(self, monkeypatch):
        """Returns input unchanged if numpy is unavailable."""
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "numpy":
                raise ImportError("mocked")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        entries = [self._make_entry("some text about the nucleus architecture")]
        result = P.semantic_dedup(entries, jaccard_threshold=0.5)
        assert result is entries  # exact same list returned

    def test_single_entry_unchanged(self):
        """Single entry list returns as-is."""
        entry = self._make_entry("the nucleus brain handles routing and monitoring")
        result = P.semantic_dedup([entry], jaccard_threshold=0.5)
        assert len(result) == 1
        assert result[0] is entry


# ═══════════════════════════════════════════════════════════════════════
# 11. backfill_shadow_entries — synthesise SFT from runs.jsonl
# ═══════════════════════════════════════════════════════════════════════


class TestBackfillShadowEntries:
    """backfill_shadow_entries creates SFT from completed driver runs."""

    def _setup_driver_dir(self, tmp_path, tasks, runs):
        """Write tasks.json and runs.jsonl to tmp_path."""
        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text(json.dumps({"tasks": tasks}))
        runs_file = tmp_path / "runs.jsonl"
        runs_file.write_text("\n".join(json.dumps(r) for r in runs) + "\n")
        return tmp_path

    def test_backfills_completed_run(self, tmp_path):
        tasks = [{"id": "t-001", "title": "Add streaming", "description": "Add SSE streaming", "scope": ["backend"]}]
        runs = [{"task_id": "t-001", "outcome": "completed", "turns": 5, "duration_seconds": 120, "ts": "2026-03-10"}]
        driver_dir = self._setup_driver_dir(tmp_path, tasks, runs)

        orig = P.DRIVER_DIR
        P.DRIVER_DIR = driver_dir
        try:
            stats = P.Stats()
            result = P.backfill_shadow_entries([], set(), set(), stats)
            assert len(result) == 1
            assert result[0]["source"] == "shadow_driver"
            assert result[0]["quality"] == "silver"
            assert result[0]["meta"]["backfilled"] is True
            assert result[0]["meta"]["task_id"] == "t-001"
        finally:
            P.DRIVER_DIR = orig

    def test_skips_non_completed_run(self, tmp_path):
        tasks = [{"id": "t-002", "title": "Fix bug", "description": "Fix timeout bug", "scope": []}]
        runs = [{"task_id": "t-002", "outcome": "failed", "turns": 2, "duration_seconds": 30, "ts": "2026-03-10"}]
        driver_dir = self._setup_driver_dir(tmp_path, tasks, runs)

        orig = P.DRIVER_DIR
        P.DRIVER_DIR = driver_dir
        try:
            result = P.backfill_shadow_entries([], set(), set(), P.Stats())
            assert len(result) == 0
        finally:
            P.DRIVER_DIR = orig

    def test_skips_already_existing_task(self, tmp_path):
        tasks = [{"id": "t-003", "title": "Deploy app", "description": "Deploy to prod", "scope": []}]
        runs = [{"task_id": "t-003", "outcome": "completed", "turns": 3, "duration_seconds": 60, "ts": "2026-03-10"}]
        driver_dir = self._setup_driver_dir(tmp_path, tasks, runs)

        # Simulate existing SFT that already covers this task
        existing = [{
            "messages": [
                {"role": "system", "content": "[2026-03-10] You are an autonomous coding agent executing a task: Deploy app"},
                {"role": "user", "content": "deploy"},
                {"role": "assistant", "content": "done"},
            ],
            "meta": {"task_id": "t-003"},
        }]

        orig = P.DRIVER_DIR
        P.DRIVER_DIR = driver_dir
        try:
            result = P.backfill_shadow_entries(existing, set(), set(), P.Stats())
            assert len(result) == 0
        finally:
            P.DRIVER_DIR = orig

    def test_missing_files_returns_empty(self, tmp_path):
        orig = P.DRIVER_DIR
        P.DRIVER_DIR = tmp_path  # no runs.jsonl or tasks.json here
        try:
            result = P.backfill_shadow_entries([], set(), set(), P.Stats())
            assert result == []
        finally:
            P.DRIVER_DIR = orig

    def test_dedup_via_global_hashes(self, tmp_path):
        tasks = [{"id": "t-004", "title": "Refactor handler", "description": "Clean up", "scope": ["backend"]}]
        runs = [{"task_id": "t-004", "outcome": "completed", "turns": 4, "duration_seconds": 90, "ts": "2026-03-10"}]
        driver_dir = self._setup_driver_dir(tmp_path, tasks, runs)

        orig = P.DRIVER_DIR
        P.DRIVER_DIR = driver_dir
        try:
            # Pre-compute what the hash would be
            query = "Execute task: Refactor handler\n\nDescription: Clean up\n\nScope: backend"
            response = "Task completed successfully.\n- Turns used: 4\n- Duration: 90s\n\nTask 'Refactor handler' has been implemented and verified."
            pre_hash = P.content_hash(query + response)
            result = P.backfill_shadow_entries([], {pre_hash}, set(), P.Stats())
            assert len(result) == 0
        finally:
            P.DRIVER_DIR = orig
