"""Tests for the lever substrate contract.

Levers are modular operators that compound through the .brain/ ledger.
These tests exercise:
  - the Lever contract (ruff_chain concrete impl)
  - the manifest loader + dispatcher
  - the ledger-append contract (observation → events.jsonl)

The pattern here is the template for the other 30 shippable levers from
the 71-item blitz — if this contract is right, they all slot in the same way.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.levers import run_lever
from scripts.levers.ruff_chain import RuffChainLever
from scripts.levers.todo_chain import TodoChainLever


class TestRuffChainLever:
    def test_reports_clean_when_no_py_files_changed(self, tmp_path):
        lever = RuffChainLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            obs = lever.run({"inputs": {"diff_spec": "HEAD~1..HEAD"}}, tmp_path)
        assert obs["outcome"] == "clean"
        assert obs["detail"]["files_checked"] == 0

    def test_reports_clean_when_ruff_passes(self, tmp_path):
        lever = RuffChainLever()
        files_result = MagicMock(returncode=0, stdout="a.py\nb.py\n")
        ruff_result = MagicMock(returncode=0, stdout="")
        with patch("subprocess.run", side_effect=[files_result, ruff_result]):
            obs = lever.run({"inputs": {"diff_spec": "HEAD~1..HEAD"}}, tmp_path)
        assert obs["outcome"] == "clean"
        assert obs["detail"]["files_checked"] == 2

    def test_reports_findings_when_ruff_fails(self, tmp_path):
        lever = RuffChainLever()
        files_result = MagicMock(returncode=0, stdout="a.py\n")
        ruff_result = MagicMock(
            returncode=1,
            stdout="a.py:3:1: F401 [*] `os` imported but unused\n",
        )
        with patch("subprocess.run", side_effect=[files_result, ruff_result]):
            obs = lever.run({"inputs": {"diff_spec": "HEAD~1..HEAD"}}, tmp_path)
        assert obs["outcome"] == "found"
        assert obs["detail"]["files_checked"] == 1
        assert any("F401" in f for f in obs["detail"]["findings"])

    def test_reports_error_when_ruff_missing(self, tmp_path):
        lever = RuffChainLever()
        files_result = MagicMock(returncode=0, stdout="a.py\n")
        with patch("subprocess.run", side_effect=[files_result, FileNotFoundError()]):
            obs = lever.run({"inputs": {"diff_spec": "HEAD~1..HEAD"}}, tmp_path)
        assert obs["outcome"] == "error"
        assert "ruff" in obs["detail"]["error"].lower()


class TestTodoChainLever:
    def test_reports_clean_when_no_markers_in_diff(self, tmp_path):
        lever = TodoChainLever()
        diff_output = (
            "diff --git a/a.py b/a.py\n"
            "--- a/a.py\n+++ b/a.py\n"
            "@@ -1 +1 @@\n+def foo(): pass\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff_output)
            obs = lever.run({"inputs": {}}, tmp_path)
        assert obs["outcome"] == "clean"

    def test_detects_todo_and_fixme_in_added_lines(self, tmp_path):
        lever = TodoChainLever()
        diff_output = (
            "diff --git a/a.py b/a.py\n"
            "--- a/a.py\n+++ b/a.py\n"
            "@@ -1 +1,3 @@\n"
            "+def foo():\n"
            "+    # TODO: implement\n"
            "+    pass  # FIXME later\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff_output)
            obs = lever.run({"inputs": {}}, tmp_path)
        assert obs["outcome"] == "found"
        findings = obs["detail"]["findings"]
        assert len(findings) == 2
        assert any("TODO" in f for f in findings)
        assert any("FIXME" in f for f in findings)
        assert all(f.startswith("a.py:") for f in findings)

    def test_ignores_markers_already_in_code_not_added(self, tmp_path):
        """Only '+' lines count — existing markers in unchanged code are skipped."""
        lever = TodoChainLever()
        diff_output = (
            "diff --git a/a.py b/a.py\n"
            "--- a/a.py\n+++ b/a.py\n"
            "@@ -1,3 +1,3 @@\n"
            " # TODO: pre-existing\n"
            "-def old(): pass\n"
            "+def new(): pass\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff_output)
            obs = lever.run({"inputs": {}}, tmp_path)
        assert obs["outcome"] == "clean"

    def test_respects_max_findings_cap(self, tmp_path):
        lever = TodoChainLever()
        lines = ["diff --git a/a.py b/a.py", "--- a/a.py", "+++ b/a.py", "@@ -1 +1,6 @@"]
        lines.extend(f"+    # TODO: item {i}" for i in range(10))
        diff_output = "\n".join(lines) + "\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff_output)
            obs = lever.run({"inputs": {"max_findings": 3}}, tmp_path)
        assert obs["outcome"] == "found"
        assert len(obs["detail"]["findings"]) == 3

    def test_reports_error_when_git_fails(self, tmp_path):
        lever = TodoChainLever()
        with patch("subprocess.run", side_effect=FileNotFoundError("git missing")):
            obs = lever.run({"inputs": {}}, tmp_path)
        assert obs["outcome"] == "error"


class TestDispatcherAndLedgerContract:
    def test_append_observation_writes_valid_entry(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        entry = run_lever.append_observation(
            "ruff_chain",
            {"outcome": "clean", "detail": {"files_checked": 5}},
            ledger_path=ledger,
        )
        lines = ledger.read_text().strip().splitlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["type"] == "lever.ruff_chain.observation"
        assert parsed["lever"] == "ruff_chain"
        assert parsed["outcome"] == "clean"
        assert parsed["detail"]["files_checked"] == 5
        assert entry == parsed

    def test_disabled_manifest_skips_execution(self, tmp_path):
        manifests = tmp_path / "manifests"
        manifests.mkdir()
        (manifests / "ruff_chain.yaml").write_text(
            "name: ruff_chain\nenabled: false\n"
        )
        ledger = tmp_path / "events.jsonl"
        obs = run_lever.run("ruff_chain", manifests_dir=manifests, ledger_path=ledger)
        assert obs["outcome"] == "skipped"
        assert ledger.exists()
        parsed = json.loads(ledger.read_text().strip())
        assert parsed["outcome"] == "skipped"

    def test_missing_manifest_raises(self, tmp_path):
        manifests = tmp_path / "manifests"
        manifests.mkdir()
        with pytest.raises(FileNotFoundError):
            run_lever.run("nonexistent", manifests_dir=manifests)


class TestRunTrigger:
    """The post-executor auto-fire is what actually makes the gate fire.

    These tests cover manifest filtering by trigger, non-fatal lever
    failures, and missing directory handling.
    """

    def test_returns_empty_when_manifests_dir_missing(self, tmp_path):
        missing = tmp_path / "nope"
        assert run_lever.run_trigger("post_executor", manifests_dir=missing) == []

    def test_only_fires_levers_matching_trigger(self, tmp_path):
        manifests = tmp_path / "manifests"
        manifests.mkdir()
        # Match: post_executor trigger, enabled
        (manifests / "ruff_chain.yaml").write_text(
            "name: ruff_chain\nenabled: true\n"
            "triggers:\n  - post_executor\n  - manual\n"
        )
        # Mismatch: different trigger
        (manifests / "cron_lever.yaml").write_text(
            "name: cron_lever\nenabled: true\n"
            "triggers:\n  - cron\n"
        )
        # Mismatch: disabled
        (manifests / "off_lever.yaml").write_text(
            "name: off_lever\nenabled: false\n"
            "triggers:\n  - post_executor\n"
        )
        ledger = tmp_path / "events.jsonl"

        # Patch load_lever to return a lever that succeeds cheaply.
        class _FakeLever:
            name = "ruff_chain"

            def run(self, manifest, brain_path):
                return {"outcome": "clean", "detail": {"files_checked": 0}}

        with patch("scripts.levers.run_lever.load_lever", return_value=_FakeLever()):
            results = run_lever.run_trigger(
                "post_executor", manifests_dir=manifests, ledger_path=ledger
            )

        names = [r["lever"] for r in results]
        assert names == ["ruff_chain"]

    def test_lever_failure_is_non_fatal(self, tmp_path):
        manifests = tmp_path / "manifests"
        manifests.mkdir()
        (manifests / "broken.yaml").write_text(
            "name: broken\nenabled: true\n"
            "triggers:\n  - post_executor\n"
        )
        (manifests / "ruff_chain.yaml").write_text(
            "name: ruff_chain\nenabled: true\n"
            "triggers:\n  - post_executor\n"
        )
        ledger = tmp_path / "events.jsonl"

        class _FakeLever:
            name = "ruff_chain"

            def run(self, manifest, brain_path):
                return {"outcome": "clean", "detail": {}}

        def _loader(name):
            if name == "broken":
                raise RuntimeError("boom")
            return _FakeLever()

        with patch("scripts.levers.run_lever.load_lever", side_effect=_loader):
            results = run_lever.run_trigger(
                "post_executor", manifests_dir=manifests, ledger_path=ledger
            )

        # ruff_chain still ran, broken was caught.
        names = [r["lever"] for r in results]
        assert "ruff_chain" in names
        assert "broken" not in names

    def test_no_matching_trigger_returns_empty(self, tmp_path):
        manifests = tmp_path / "manifests"
        manifests.mkdir()
        (manifests / "only_cron.yaml").write_text(
            "name: only_cron\nenabled: true\n"
            "triggers:\n  - cron\n"
        )
        ledger = tmp_path / "events.jsonl"
        assert run_lever.run_trigger(
            "post_executor", manifests_dir=manifests, ledger_path=ledger
        ) == []
