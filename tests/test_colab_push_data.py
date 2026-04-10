"""Tests for .brain/training/colab_push_data.py

Covers: sha256_file, sha256_content, check_contamination,
        determine_version, count_completed_tasks.
All Drive/filesystem paths are mocked via tmp_path for CI safety.
"""

import hashlib
import json

import pytest

# Import the module under test
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".brain" / "training"))
# Skip the entire file if the pipeline script is not on disk. Tracked as a
# follow-up — the .brain/training/ scripts are Drive-synced and may not exist
# on every checkout; skipping keeps CI green without masking real regressions
# in tests that don't depend on this pipeline.
cpd = pytest.importorskip("colab_push_data")


# ── sha256_file ──────────────────────────────────────────────


class TestSha256File:
    def test_known_hash(self, tmp_path):
        p = tmp_path / "hello.txt"
        p.write_bytes(b"hello world")
        expected = hashlib.sha256(b"hello world").hexdigest()
        assert cpd.sha256_file(p) == expected

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty"
        p.write_bytes(b"")
        expected = hashlib.sha256(b"").hexdigest()
        assert cpd.sha256_file(p) == expected

    def test_large_file_chunked(self, tmp_path):
        """Verify chunked reading produces correct hash for >8192 byte file."""
        data = b"x" * 20_000
        p = tmp_path / "large"
        p.write_bytes(data)
        expected = hashlib.sha256(data).hexdigest()
        assert cpd.sha256_file(p) == expected


# ── sha256_content ───────────────────────────────────────────


class TestSha256Content:
    def test_matches_hashlib(self):
        text = "some prompt text"
        expected = hashlib.sha256(text.encode()).hexdigest()
        assert cpd.sha256_content(text) == expected

    def test_empty_string(self):
        assert cpd.sha256_content("") == hashlib.sha256(b"").hexdigest()


# ── count_completed_tasks ────────────────────────────────────


class TestCountCompletedTasks:
    def test_no_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cpd, "DRIVER_DIR", tmp_path)
        assert cpd.count_completed_tasks() == 0

    def test_counts_only_completed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cpd, "DRIVER_DIR", tmp_path)
        tasks = {
            "tasks": [
                {"id": 1, "status": "completed"},
                {"id": 2, "status": "in_progress"},
                {"id": 3, "status": "completed"},
                {"id": 4, "status": "blocked"},
            ]
        }
        (tmp_path / "tasks.json").write_text(json.dumps(tasks))
        assert cpd.count_completed_tasks() == 2

    def test_empty_tasks_list(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cpd, "DRIVER_DIR", tmp_path)
        (tmp_path / "tasks.json").write_text(json.dumps({"tasks": []}))
        assert cpd.count_completed_tasks() == 0

    def test_malformed_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cpd, "DRIVER_DIR", tmp_path)
        (tmp_path / "tasks.json").write_text("{bad json")
        assert cpd.count_completed_tasks() == 0

    def test_missing_tasks_key(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cpd, "DRIVER_DIR", tmp_path)
        (tmp_path / "tasks.json").write_text(json.dumps({"other": "stuff"}))
        assert cpd.count_completed_tasks() == 0


# ── determine_version ────────────────────────────────────────


class TestDetermineVersion:
    def test_no_adapters_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cpd, "DRIVE_ADAPTERS", tmp_path / "nonexistent")
        assert cpd.determine_version() == "v1"

    def test_empty_adapters_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cpd, "DRIVE_ADAPTERS", tmp_path)
        assert cpd.determine_version() == "v1"

    def test_increments_max(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cpd, "DRIVE_ADAPTERS", tmp_path)
        (tmp_path / "v1").mkdir()
        (tmp_path / "v3").mkdir()
        (tmp_path / "v2").mkdir()
        assert cpd.determine_version() == "v4"

    def test_ignores_non_version_dirs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cpd, "DRIVE_ADAPTERS", tmp_path)
        (tmp_path / "v2").mkdir()
        (tmp_path / "logs").mkdir()
        (tmp_path / "readme.txt").touch()
        assert cpd.determine_version() == "v3"

    def test_single_version(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cpd, "DRIVE_ADAPTERS", tmp_path)
        (tmp_path / "v5").mkdir()
        assert cpd.determine_version() == "v6"


# ── check_contamination ─────────────────────────────────────


class TestCheckContamination:
    def _write_train(self, path, messages_list):
        """Write training JSONL. Each entry is a list of (role, content) tuples."""
        with open(path, "w") as f:
            for msgs in messages_list:
                item = {"messages": [{"role": r, "content": c} for r, c in msgs]}
                f.write(json.dumps(item) + "\n")

    def test_no_contamination(self, tmp_path):
        train = tmp_path / "train.jsonl"
        self._write_train(train, [
            [("user", "how to sort a list"), ("assistant", "use sorted()")],
        ])
        eval_prompts = [{"prompt": "explain recursion"}]
        assert cpd.check_contamination(train, eval_prompts) == 0

    def test_detects_exact_match(self, tmp_path):
        train = tmp_path / "train.jsonl"
        self._write_train(train, [
            [("user", "explain recursion"), ("assistant", "it calls itself")],
        ])
        eval_prompts = [{"prompt": "explain recursion"}]
        assert cpd.check_contamination(train, eval_prompts) == 1

    def test_case_insensitive_match(self, tmp_path):
        train = tmp_path / "train.jsonl"
        self._write_train(train, [
            [("user", "EXPLAIN RECURSION"), ("assistant", "...")],
        ])
        eval_prompts = [{"prompt": "explain recursion"}]
        assert cpd.check_contamination(train, eval_prompts) == 1

    def test_strips_whitespace(self, tmp_path):
        train = tmp_path / "train.jsonl"
        self._write_train(train, [
            [("user", "  explain recursion  "), ("assistant", "...")],
        ])
        eval_prompts = [{"prompt": "explain recursion"}]
        assert cpd.check_contamination(train, eval_prompts) == 1

    def test_no_train_file(self, tmp_path):
        assert cpd.check_contamination(tmp_path / "nope.jsonl", [{"prompt": "x"}]) == 0

    def test_empty_eval_list(self, tmp_path):
        train = tmp_path / "train.jsonl"
        self._write_train(train, [[("user", "hello"), ("assistant", "hi")]])
        assert cpd.check_contamination(train, []) == 0

    def test_multiple_contaminated(self, tmp_path):
        train = tmp_path / "train.jsonl"
        self._write_train(train, [
            [("user", "prompt a"), ("assistant", "...")],
            [("user", "prompt b"), ("assistant", "...")],
            [("user", "clean"), ("assistant", "...")],
        ])
        eval_prompts = [{"prompt": "prompt a"}, {"prompt": "prompt b"}]
        assert cpd.check_contamination(train, eval_prompts) == 2

    def test_skips_assistant_messages(self, tmp_path):
        """Only user messages should be checked, not assistant ones."""
        train = tmp_path / "train.jsonl"
        self._write_train(train, [
            [("user", "different"), ("assistant", "explain recursion")],
        ])
        eval_prompts = [{"prompt": "explain recursion"}]
        assert cpd.check_contamination(train, eval_prompts) == 0
