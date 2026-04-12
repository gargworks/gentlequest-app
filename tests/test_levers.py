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
from scripts.levers.base import (
    OUTCOMES,
    LedgerEvent,
    LedgerSchemaError,
    Lever,
    SubprocessFailure,
    iter_events,
)
import subprocess

from scripts.levers.golden_benchmark_check import GoldenBenchmarkCheckLever
from scripts.levers.gt40_lint import Gt40LintLever
from scripts.levers.gt40_test_smoke import Gt40TestSmokeLever
from scripts.levers.gt40_typecheck import Gt40TypecheckLever
from scripts.levers.narrow_task_filter import NarrowTaskFilterLever
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


class TestNarrowTaskFilterLever:
    """Broad task scope is the #1 predictor of Phase-D ACCEPT failures.

    The lever reads the active task (via ``NUCLEUS_TASK_ID``) from a tasks
    file and flags scope/description/title breaches against manifest
    thresholds so session_start can catch over-broad tasks early.
    """

    def _manifest(self, tasks_path, **overrides):
        inputs = {
            "tasks_path": str(tasks_path),
            "task_id_env": "NUCLEUS_TASK_ID",
            "max_scope_items": 5,
            "max_description_chars": 500,
            "max_title_chars": 120,
        }
        inputs.update(overrides)
        return {"inputs": inputs}

    def test_skipped_when_task_id_env_missing(self, tmp_path):
        lever = NarrowTaskFilterLever()
        with patch.dict("os.environ", {}, clear=True):
            obs = lever.run(self._manifest(tmp_path / "tasks.json"), tmp_path)
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "no_task_id"
        assert obs["detail"]["env_var"] == "NUCLEUS_TASK_ID"

    def test_clean_when_all_within_threshold(self, tmp_path):
        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text(json.dumps({
            "tasks": [{
                "id": "t-1",
                "title": "small title",
                "description": "short description",
                "scope": ["scripts/a.py", "scripts/b.py"],
            }]
        }))
        lever = NarrowTaskFilterLever()
        with patch.dict("os.environ", {"NUCLEUS_TASK_ID": "t-1"}, clear=True):
            obs = lever.run(self._manifest(tasks_file), tmp_path)
        assert obs["outcome"] == "clean"
        assert obs["detail"]["task_id"] == "t-1"
        assert obs["detail"]["scope_items"] == 2

    def test_found_when_scope_too_wide(self, tmp_path):
        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text(json.dumps({
            "tasks": [{
                "id": "t-1",
                "title": "ok",
                "description": "ok",
                "scope": [f"scripts/f{i}.py" for i in range(8)],
            }]
        }))
        lever = NarrowTaskFilterLever()
        with patch.dict("os.environ", {"NUCLEUS_TASK_ID": "t-1"}, clear=True):
            obs = lever.run(self._manifest(tasks_file), tmp_path)
        assert obs["outcome"] == "found"
        assert any("scope=8" in f for f in obs["detail"]["findings"])
        assert obs["detail"]["scope_items"] == 8

    def test_found_when_description_too_long(self, tmp_path):
        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text(json.dumps({
            "tasks": [{
                "id": "t-1",
                "title": "ok",
                "description": "x" * 600,
                "scope": ["scripts/a.py"],
            }]
        }))
        lever = NarrowTaskFilterLever()
        with patch.dict("os.environ", {"NUCLEUS_TASK_ID": "t-1"}, clear=True):
            obs = lever.run(self._manifest(tasks_file), tmp_path)
        assert obs["outcome"] == "found"
        assert any("description=600" in f for f in obs["detail"]["findings"])

    def test_error_when_tasks_file_missing(self, tmp_path):
        lever = NarrowTaskFilterLever()
        missing = tmp_path / "does_not_exist.json"
        with patch.dict("os.environ", {"NUCLEUS_TASK_ID": "t-1"}, clear=True):
            obs = lever.run(self._manifest(missing), tmp_path)
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "task_load"


class TestGoldenBenchmarkCheckLever:
    """CSR < baseline is the flywheel breaking claims faster than recovering."""

    def _manifest(self, csr_path, **overrides):
        inputs = {
            "csr_path": str(csr_path),
            "baseline_csr": 0.90,
            "window_hours": 24,
        }
        inputs.update(overrides)
        return {"inputs": inputs}

    def test_skipped_when_csr_file_missing(self, tmp_path):
        lever = GoldenBenchmarkCheckLever()
        obs = lever.run(self._manifest(tmp_path / "missing.json"), tmp_path)
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "no_csr_snapshot"

    def test_clean_when_csr_at_baseline(self, tmp_path):
        csr_file = tmp_path / "csr.json"
        csr_file.write_text(json.dumps({"ratio": 0.90}))
        lever = GoldenBenchmarkCheckLever()
        obs = lever.run(self._manifest(csr_file), tmp_path)
        assert obs["outcome"] == "clean"
        assert obs["detail"]["csr"] == 0.90

    def test_clean_when_csr_above_baseline(self, tmp_path):
        """Accepts legacy `csr` key as a fallback for forward-compat."""
        csr_file = tmp_path / "csr.json"
        csr_file.write_text(json.dumps({"csr": 0.97}))
        lever = GoldenBenchmarkCheckLever()
        obs = lever.run(self._manifest(csr_file), tmp_path)
        assert obs["outcome"] == "clean"
        assert obs["detail"]["csr"] == 0.97

    def test_found_when_csr_below_baseline_reports_delta(self, tmp_path):
        csr_file = tmp_path / "csr.json"
        csr_file.write_text(json.dumps({"ratio": 0.75}))
        lever = GoldenBenchmarkCheckLever()
        obs = lever.run(self._manifest(csr_file), tmp_path)
        assert obs["outcome"] == "found"
        assert obs["detail"]["csr"] == 0.75
        assert obs["detail"]["baseline_csr"] == 0.90
        assert obs["detail"]["delta"] == pytest.approx(-0.15)
        assert obs["detail"]["window_hours"] == 24

    def test_error_when_csr_file_is_malformed_json(self, tmp_path):
        csr_file = tmp_path / "csr.json"
        csr_file.write_text("{not json")
        lever = GoldenBenchmarkCheckLever()
        obs = lever.run(self._manifest(csr_file), tmp_path)
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "parse_csr"


class TestGt40LintLever:
    """Wraps nucleus verify --tiers 1. Exit + tail land on the ledger."""

    def _manifest(self, **overrides):
        inputs = {"nucleus_bin": "nucleus", "timeout_seconds": 15, "tier": 1}
        inputs.update(overrides)
        return {"inputs": inputs}

    def test_error_when_nucleus_not_installed(self, tmp_path):
        lever = Gt40LintLever()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "nucleus_missing"

    def test_clean_when_nucleus_exits_zero(self, tmp_path):
        lever = Gt40LintLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "clean"
        assert obs["detail"]["tier"] == 1

    def test_found_when_nucleus_exits_nonzero_carries_findings(self, tmp_path):
        lever = Gt40LintLever()
        stderr = "\n".join(f"err line {i}" for i in range(30))
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=2, stdout="summary: 3 issues", stderr=stderr
            )
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "found"
        assert obs["detail"]["returncode"] == 2
        findings = obs["detail"]["findings"]
        assert len(findings) == 20
        assert findings[-1] == "err line 29"

    def test_error_when_timeout_exceeded(self, tmp_path):
        lever = Gt40LintLever()
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="nucleus", timeout=15),
        ):
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "timeout"

    def test_respects_tier_input_in_argv(self, tmp_path):
        lever = Gt40LintLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            lever.run(self._manifest(tier=7), tmp_path)
        argv = mock_run.call_args[0][0]
        assert "--tiers" in argv
        assert argv[argv.index("--tiers") + 1] == "7"


class TestGt40TypecheckLever:
    """Same contract as gt40_lint but tier=2 (import resolution)."""

    def _manifest(self, **overrides):
        inputs = {"nucleus_bin": "nucleus", "timeout_seconds": 30, "tier": 2}
        inputs.update(overrides)
        return {"inputs": inputs}

    def test_error_when_nucleus_not_installed(self, tmp_path):
        lever = Gt40TypecheckLever()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "nucleus_missing"

    def test_clean_when_nucleus_exits_zero(self, tmp_path):
        lever = Gt40TypecheckLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "clean"
        assert obs["detail"]["tier"] == 2

    def test_found_when_nucleus_exits_nonzero_carries_findings(self, tmp_path):
        lever = Gt40TypecheckLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="missing import: foo", stderr=""
            )
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "found"
        assert obs["detail"]["returncode"] == 1
        assert any("missing import" in f for f in obs["detail"]["findings"])

    def test_error_when_timeout_exceeded(self, tmp_path):
        lever = Gt40TypecheckLever()
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="nucleus", timeout=30),
        ):
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "timeout"

    def test_respects_tier_input_in_argv(self, tmp_path):
        lever = Gt40TypecheckLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            lever.run(self._manifest(), tmp_path)
        argv = mock_run.call_args[0][0]
        assert argv[argv.index("--tiers") + 1] == "2"


class TestGt40TestSmokeLever:
    """Smoke-tier wrapper. Exercises the --smoke flag path explicitly."""

    def _manifest(self, **overrides):
        inputs = {
            "nucleus_bin": "nucleus",
            "timeout_seconds": 60,
            "tier": 3,
            "smoke_flag": "--smoke",
        }
        inputs.update(overrides)
        return {"inputs": inputs}

    def test_error_when_nucleus_not_installed(self, tmp_path):
        lever = Gt40TestSmokeLever()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "nucleus_missing"

    def test_clean_on_exit_zero(self, tmp_path):
        lever = Gt40TestSmokeLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "clean"
        assert obs["detail"]["ran"] == "smoke"

    def test_found_when_smoke_fails(self, tmp_path):
        lever = Gt40TestSmokeLever()
        stderr = "\n".join(f"fail {i}" for i in range(50))
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr=stderr)
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "found"
        assert obs["detail"]["ran"] == "smoke"
        # last 30 non-empty lines
        assert len(obs["detail"]["findings"]) == 30
        assert obs["detail"]["findings"][-1] == "fail 49"

    def test_argv_includes_smoke_flag(self, tmp_path):
        lever = Gt40TestSmokeLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            lever.run(self._manifest(), tmp_path)
        argv = mock_run.call_args[0][0]
        assert "--smoke" in argv
        assert argv[argv.index("--tiers") + 1] == "3"

    def test_error_when_timeout_exceeded(self, tmp_path):
        lever = Gt40TestSmokeLever()
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="nucleus", timeout=60),
        ):
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "timeout"


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


class TestLedgerEventSchema:
    """LedgerEvent is the typed contract. Schema errors must surface loudly."""

    def test_from_jsonl_accepts_valid_lever_observation(self):
        line = (
            '{"ts": "2026-04-12T00:00:00+00:00", "type": "lever.x.observation",'
            ' "lever": "x", "outcome": "clean", "detail": {"n": 0}}'
        )
        event = LedgerEvent.from_jsonl(line)
        assert event.type == "lever.x.observation"
        assert event.outcome == "clean"
        assert event.detail == {"n": 0}

    def test_from_jsonl_rejects_missing_ts(self):
        line = '{"type": "lever.x.observation", "outcome": "clean"}'
        with pytest.raises(LedgerSchemaError, match="ts"):
            LedgerEvent.from_jsonl(line)

    def test_from_jsonl_rejects_missing_type(self):
        line = '{"ts": "2026-04-12T00:00:00+00:00"}'
        with pytest.raises(LedgerSchemaError, match="type"):
            LedgerEvent.from_jsonl(line)

    def test_from_jsonl_rejects_invalid_outcome(self):
        line = (
            '{"ts": "2026-04-12T00:00:00+00:00", "type": "lever.x.observation",'
            ' "outcome": "whatever"}'
        )
        with pytest.raises(LedgerSchemaError, match="outcome"):
            LedgerEvent.from_jsonl(line)

    def test_from_jsonl_rejects_corrupt_json(self):
        with pytest.raises(LedgerSchemaError, match="JSON"):
            LedgerEvent.from_jsonl("{not json")

    def test_to_jsonl_round_trip(self):
        event = LedgerEvent(
            ts="2026-04-12T00:00:00+00:00",
            type="tb.review.decided",
            extra={"task_id": "t-1", "verdict": "ACCEPT"},
        )
        line = event.to_jsonl()
        parsed = LedgerEvent.from_jsonl(line)
        assert parsed.type == "tb.review.decided"
        assert parsed.extra["task_id"] == "t-1"

    def test_outcomes_frozenset_contents(self):
        assert OUTCOMES == frozenset({"clean", "found", "error", "skipped", "unknown"})

    def test_for_lever_observation_strips_control_chars(self):
        event = LedgerEvent.for_lever_observation(
            "my_lever",
            {"outcome": "found", "detail": {"msg": "bad\x00evil"}},
        )
        assert event.detail["msg"] == "badevil"


class TestAppendObservationContract:
    """append_observation validates + writes exactly one LedgerEvent line."""

    def test_append_observation_rejects_invalid_outcome(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        with pytest.raises(LedgerSchemaError, match="outcome"):
            run_lever.append_observation(
                "my_lever",
                {"outcome": "bogus", "detail": {}},
                ledger_path=ledger,
            )
        # Schema violation itself is recorded so the substrate sees the bug.
        assert ledger.exists()
        lines = ledger.read_text().strip().splitlines()
        assert any("lever.schema.violation" in line for line in lines)

    def test_append_observation_writes_valid_event(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        entry = run_lever.append_observation(
            "my_lever",
            {"outcome": "found", "detail": {"findings": ["x"]}},
            ledger_path=ledger,
        )
        assert entry["outcome"] == "found"
        line = ledger.read_text().strip().splitlines()[0]
        parsed = LedgerEvent.from_jsonl(line)
        assert parsed.lever == "my_lever"
        assert parsed.outcome == "found"


class TestDispatcherFailureEvents:
    """Dispatcher failures emit lever.dispatcher.failure — never silent swallow."""

    def test_failing_lever_emits_dispatcher_failure_event(self, tmp_path):
        manifests = tmp_path / "manifests"
        manifests.mkdir()
        (manifests / "explode.yaml").write_text(
            "name: explode\nenabled: true\ntriggers:\n  - post_executor\n"
        )
        ledger = tmp_path / "events.jsonl"

        def _loader(name):
            raise RuntimeError("boom")

        with patch("scripts.levers.run_lever.load_lever", side_effect=_loader):
            run_lever.run_trigger(
                "post_executor", manifests_dir=manifests, ledger_path=ledger
            )

        lines = ledger.read_text().strip().splitlines()
        assert any("lever.dispatcher.failure" in line for line in lines)
        # Failure event carries error_class for forensics.
        failure_event = next(
            json.loads(line) for line in lines
            if "lever.dispatcher.failure" in line
        )
        assert failure_event["detail"]["lever"] == "explode"
        assert failure_event["detail"]["error_class"] == "RuntimeError"

    def test_manifest_parse_error_writes_manifest_error_event(self, tmp_path):
        manifests = tmp_path / "manifests"
        manifests.mkdir()
        # Force a YAML parse error with an explicit syntax violation.
        (manifests / "bad.yaml").write_text("name: bad\n  - : : : [\n")
        ledger = tmp_path / "events.jsonl"

        run_lever.run_trigger(
            "post_executor", manifests_dir=manifests, ledger_path=ledger
        )

        lines = ledger.read_text().strip().splitlines() if ledger.exists() else []
        assert any("lever.manifest.error" in line for line in lines)


class TestIterEvents:
    """iter_events is the canonical reader path."""

    def test_iter_events_skips_corrupt_lines_by_default(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        ledger.write_text(
            '{"ts": "2026-04-12T00:00:00+00:00", "type": "a"}\n'
            '{not json\n'
            '{"ts": "2026-04-12T00:00:01+00:00", "type": "b"}\n'
        )
        events = list(iter_events(ledger))
        assert [e.type for e in events] == ["a", "b"]

    def test_iter_events_raises_on_corrupt_when_strict(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        ledger.write_text('{not json\n')
        with pytest.raises(LedgerSchemaError):
            list(iter_events(ledger, skip_invalid=False))

    def test_iter_events_returns_nothing_for_missing_ledger(self, tmp_path):
        assert list(iter_events(tmp_path / "nope.jsonl")) == []


class TestLeverBaseHelpers:
    """_run_subprocess contract: argv-only, named exceptions."""

    def test_run_subprocess_rejects_non_list_argv(self):
        with pytest.raises(TypeError):
            Lever._run_subprocess("git status", timeout=1, stage="test")

    def test_run_subprocess_throws_named_exception_on_nonzero(self):
        with pytest.raises(SubprocessFailure) as exc_info:
            Lever._run_subprocess(
                ["false"], timeout=2, stage="fail_test", check=True
            )
        assert exc_info.value.stage == "fail_test"
        assert exc_info.value.returncode != 0
