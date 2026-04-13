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
import os
import sys
from datetime import datetime, timezone
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

from scripts.levers.a11y_smoke import A11ySmokeLever
from scripts.levers.api_contract_check import ApiContractCheckLever
from scripts.levers.bull_audit import BullAuditLever
from scripts.levers.bundle_size_check import BundleSizeCheckLever
from scripts.levers.config_schema_check import ConfigSchemaCheckLever
from scripts.levers.coverage_delta import CoverageDeltaLever
from scripts.levers.dead_code_scan import DeadCodeScanLever
from scripts.levers.dead_link_check import DeadLinkCheckLever
from scripts.levers.dep_vulnerability_check import DepVulnerabilityCheckLever
from scripts.levers.diff_size_check import DiffSizeCheckLever
from scripts.levers.env_var_drift import EnvVarDriftLever
from scripts.levers.flaky_test_detector import FlakyTestDetectorLever
from scripts.levers.golden_benchmark_check import GoldenBenchmarkCheckLever
from scripts.levers.gt40_lint import Gt40LintLever
from scripts.levers.i18n_key_check import I18nKeyCheckLever
from scripts.levers.import_cycle_check import ImportCycleCheckLever
from scripts.levers.license_header_check import LicenseHeaderCheckLever
from scripts.levers.gt40_test_smoke import Gt40TestSmokeLever
from scripts.levers.gt40_typecheck import Gt40TypecheckLever
from scripts.levers.migration_lint import MigrationLintLever
from scripts.levers.narrow_task_filter import NarrowTaskFilterLever
from scripts.levers.perf_regression_spotter import PerfRegressionSpotterLever
from scripts.levers.plan_audit import PlanAuditLever
from scripts.levers.ruff_chain import RuffChainLever
from scripts.levers.schema_drift_check import SchemaDriftCheckLever
from scripts.levers.scope_pre_enforce import ScopePreEnforceLever
from scripts.levers.secret_scan import SecretScanLever
from scripts.levers.runtime_regression import RuntimeRegressionLever
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


def _receipt_json(verified, tier_reached, tiers_passed, tiers_failed=None,
                  tiers_skipped=None, signals=None, duration_s=0.05):
    """Build a nucleus verify --json receipt as a stdout string."""
    receipt = {
        "verified": verified,
        "tier_reached": tier_reached,
        "tiers_passed": tiers_passed,
        "tiers_failed": tiers_failed or [],
        "tiers_skipped": tiers_skipped or [],
        "signals": signals or [],
        "duration_s": duration_s,
        "receipt_id": "test1234",
        "commit_sha": "abc123",
    }
    return json.dumps(receipt, indent=2)


def _polluted_stdout(receipt_json):
    """Wrap a receipt in the noise nucleus actually emits."""
    return (
        "/path/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL\n"
        "  warnings.warn(\n"
        "[Nucleus] INSECURE MODE: Running unprivileged.\n"
        f"{receipt_json}\n"
    )


class TestGt40TypecheckLever:
    """Tier 2 (import resolution). Uses --json receipt parsing — no
    stdout scraping. Behavior matrix covers all 4 receipt outcomes
    plus the 3 subprocess error paths."""

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

    def test_clean_when_target_tier_reached(self, tmp_path):
        lever = Gt40TypecheckLever()
        receipt = _receipt_json(
            verified=True, tier_reached=2,
            tiers_passed=[0, 1, 2], tiers_skipped=[3, 4, 5],
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=_polluted_stdout(receipt), stderr="",
            )
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "clean"
        assert obs["detail"]["tier"] == 2
        assert obs["detail"]["tier_reached"] == 2

    def test_found_when_tiers_failed_nonempty(self, tmp_path):
        lever = Gt40TypecheckLever()
        receipt = _receipt_json(
            verified=False, tier_reached=2,
            tiers_passed=[0, 1], tiers_failed=[2],
            signals=[
                {"tier": 2, "check": "import_resolve", "passed": False,
                 "file": "scripts/foo.py", "error": "no module named bar"},
            ],
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout=_polluted_stdout(receipt), stderr="",
            )
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "found"
        assert obs["detail"]["tiers_failed"] == [2]
        assert any("import_resolve" in f for f in obs["detail"]["findings"])
        assert any("no module named bar" in f for f in obs["detail"]["findings"])

    def test_skipped_when_target_tier_not_reached(self, tmp_path):
        """Pre-fix bug: argparse error / silent-skip exited nonzero with no
        failure signals, lever falsely reported `found`. Now it must be
        `skipped` so bull_audit's no_repeated_lever_errors isn't tripped."""
        lever = Gt40TypecheckLever()
        receipt = _receipt_json(
            verified=True, tier_reached=1,
            tiers_passed=[0, 1], tiers_skipped=[2, 3, 4, 5],
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=_polluted_stdout(receipt), stderr="",
            )
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "skipped"
        assert "tier 2 not reached" in obs["detail"]["reason"]
        assert obs["detail"]["tier_reached"] == 1

    def test_error_when_timeout_exceeded(self, tmp_path):
        lever = Gt40TypecheckLever()
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="nucleus", timeout=30),
        ):
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "timeout"

    def test_error_when_no_json_in_stdout(self, tmp_path):
        """argparse error / nucleus crash → no JSON receipt → error
        (not found, not skipped) so the gap is visible."""
        lever = Gt40TypecheckLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=2, stdout="usage: nucleus verify [-h]...\n",
                stderr="error: unrecognized arguments\n",
            )
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "parse_receipt"

    def test_argv_uses_chain_and_json(self, tmp_path):
        """Default chain is 0..target_tier; --json is always passed."""
        lever = Gt40TypecheckLever()
        receipt = _receipt_json(verified=True, tier_reached=2, tiers_passed=[0, 1, 2])
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=receipt, stderr="",
            )
            lever.run(self._manifest(), tmp_path)
        argv = mock_run.call_args[0][0]
        assert argv[argv.index("--tiers") + 1] == "0,1,2"
        assert "--json" in argv


class TestGt40TestSmokeLever:
    """Tier 3 wrapper. The bogus --smoke flag is gone (nucleus argparse
    rejects it; pre-fix this caused exit 2 + usage-as-findings noise)."""

    def _manifest(self, **overrides):
        inputs = {"nucleus_bin": "nucleus", "timeout_seconds": 60, "tier": 3}
        inputs.update(overrides)
        return {"inputs": inputs}

    def test_error_when_nucleus_not_installed(self, tmp_path):
        lever = Gt40TestSmokeLever()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "nucleus_missing"

    def test_clean_when_target_tier_reached(self, tmp_path):
        lever = Gt40TestSmokeLever()
        receipt = _receipt_json(
            verified=True, tier_reached=3,
            tiers_passed=[0, 1, 2, 3], tiers_skipped=[4, 5],
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=_polluted_stdout(receipt), stderr="",
            )
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "clean"
        assert obs["detail"]["tier"] == 3

    def test_found_when_tests_fail(self, tmp_path):
        lever = Gt40TestSmokeLever()
        signals = [
            {"tier": 3, "check": "pytest", "passed": False,
             "file": f"tests/test_x.py::test_y_{i}", "error": f"AssertionError: {i}"}
            for i in range(40)
        ]
        receipt = _receipt_json(
            verified=False, tier_reached=3,
            tiers_passed=[0, 1, 2], tiers_failed=[3], signals=signals,
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout=_polluted_stdout(receipt), stderr="",
            )
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "found"
        assert obs["detail"]["tiers_failed"] == [3]
        assert len(obs["detail"]["findings"]) == 30  # findings_limit=30

    def test_skipped_when_target_tier_not_reached(self, tmp_path):
        lever = Gt40TestSmokeLever()
        receipt = _receipt_json(
            verified=True, tier_reached=2,
            tiers_passed=[0, 1, 2], tiers_skipped=[3, 4, 5],
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=_polluted_stdout(receipt), stderr="",
            )
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "skipped"
        assert "tier 3 not reached" in obs["detail"]["reason"]

    def test_argv_uses_chain_and_json_no_smoke(self, tmp_path):
        """The bogus --smoke flag is gone — nucleus never accepted it."""
        lever = Gt40TestSmokeLever()
        receipt = _receipt_json(verified=True, tier_reached=3, tiers_passed=[0, 1, 2, 3])
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=receipt, stderr="")
            lever.run(self._manifest(), tmp_path)
        argv = mock_run.call_args[0][0]
        assert "--smoke" not in argv
        assert "--json" in argv
        assert argv[argv.index("--tiers") + 1] == "0,1,2,3"

    def test_error_when_timeout_exceeded(self, tmp_path):
        lever = Gt40TestSmokeLever()
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="nucleus", timeout=60),
        ):
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "timeout"


class TestSecretScanLever:
    """Findings must never carry the matched secret body — anti-leak invariant.

    Pattern prefixes (AIzaSy, ghp_, AKIA, ...) identify what kind of
    secret was matched without publishing the secret itself into the
    ledger.
    """

    PATTERNS = [
        'AIzaSy[A-Za-z0-9_-]{33}',
        'ghp_[A-Za-z0-9]{36}',
        'AKIA[0-9A-Z]{16}',
    ]

    def _manifest(self, **overrides):
        inputs = {
            "diff_spec": "HEAD~1..HEAD",
            "max_findings": 25,
            "patterns": list(self.PATTERNS),
        }
        inputs.update(overrides)
        return {"inputs": inputs}

    def test_clean_when_no_patterns_match(self, tmp_path):
        lever = SecretScanLever()
        diff_output = (
            "diff --git a/a.py b/a.py\n"
            "--- a/a.py\n+++ b/a.py\n"
            "@@ -1 +1 @@\n+def foo(): pass\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff_output)
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "clean"
        assert obs["detail"]["patterns_checked"] == 3

    def test_found_when_api_key_in_added_line(self, tmp_path):
        lever = SecretScanLever()
        fake_key = "AIzaSy" + "A" * 33
        diff_output = (
            "diff --git a/cfg.py b/cfg.py\n"
            "--- a/cfg.py\n+++ b/cfg.py\n"
            "@@ -1 +1 @@\n"
            f'+GOOGLE_KEY = "{fake_key}"\n'
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff_output)
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "found"
        assert any("AIzaSy" in f for f in obs["detail"]["findings"])
        assert any("cfg.py" in f for f in obs["detail"]["findings"])

    def test_finding_never_contains_the_secret_body(self, tmp_path):
        """ANTI-LEAK: the matched secret body must never appear in the finding."""
        lever = SecretScanLever()
        unique_body = "XY9zPQwertY12345678901234567890123456A"
        fake_key = "AIzaSy" + unique_body
        diff_output = (
            "diff --git a/cfg.py b/cfg.py\n"
            "--- a/cfg.py\n+++ b/cfg.py\n"
            "@@ -1 +1 @@\n"
            f'+GOOGLE_KEY = "{fake_key}"\n'
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff_output)
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "found"
        for finding in obs["detail"]["findings"]:
            assert unique_body not in finding, f"secret body leaked: {finding}"
            assert fake_key not in finding, f"full key leaked: {finding}"

    def test_respects_max_findings_cap(self, tmp_path):
        lever = SecretScanLever()
        lines = ["diff --git a/k.py b/k.py", "--- a/k.py", "+++ b/k.py", "@@ -1 +1,10 @@"]
        for i in range(10):
            # 10 distinct AWS-key-shaped secrets
            lines.append(f"+KEY_{i} = \"AKIA{i:016d}\"")
        diff_output = "\n".join(lines) + "\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff_output)
            obs = lever.run(self._manifest(max_findings=3), tmp_path)
        assert obs["outcome"] == "found"
        assert len(obs["detail"]["findings"]) == 3

    def test_error_when_git_missing(self, tmp_path):
        lever = SecretScanLever()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "git_diff"


class TestDiffSizeCheckLever:
    """Large diffs get rubber-stamped — flag them before ACCEPT."""

    def _manifest(self, **overrides):
        inputs = {
            "diff_spec": "HEAD~1..HEAD",
            "max_files": 20,
            "max_added_lines": 500,
        }
        inputs.update(overrides)
        return {"inputs": inputs}

    def test_clean_when_within_both_thresholds(self, tmp_path):
        lever = DiffSizeCheckLever()
        numstat = "10\t0\ta.py\n20\t5\tb.py\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=numstat, stderr="")
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "clean"
        assert obs["detail"]["files"] == 2
        assert obs["detail"]["added_lines"] == 30

    def test_found_when_file_count_exceeds(self, tmp_path):
        lever = DiffSizeCheckLever()
        numstat = "".join(f"1\t0\tf{i}.py\n" for i in range(25))
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=numstat, stderr="")
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "found"
        assert any("files=25 > 20" in f for f in obs["detail"]["findings"])

    def test_found_when_added_lines_exceed(self, tmp_path):
        lever = DiffSizeCheckLever()
        numstat = "600\t10\tbig.py\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=numstat, stderr="")
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "found"
        assert any("added=600 > 500" in f for f in obs["detail"]["findings"])

    def test_handles_binary_entries_with_dash(self, tmp_path):
        lever = DiffSizeCheckLever()
        numstat = "-\t-\timg.png\n10\t0\ta.py\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=numstat, stderr="")
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "clean"
        # Binary counts toward file count (2) but contributes 0 added lines.
        assert obs["detail"]["files"] == 2
        assert obs["detail"]["added_lines"] == 10

    def test_error_when_git_missing(self, tmp_path):
        lever = DiffSizeCheckLever()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path)
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "git_numstat"


class TestImportCycleCheckLever:
    """Direct A<->B cycles. Long cycles out of scope (80% rule)."""

    def _manifest(self, **overrides):
        inputs = {
            "diff_spec": "HEAD~1..HEAD",
            "roots": ["scripts"],
        }
        inputs.update(overrides)
        return {"inputs": inputs}

    def _mk_project(self, tmp_path: Path):
        """Project layout: tmp_path/scripts/pkg/<files>."""
        pkg = tmp_path / "scripts" / "pkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        return pkg

    def test_clean_when_no_imports_added(self, tmp_path):
        lever = ImportCycleCheckLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["files_checked"] == 0

    def test_clean_when_linear_imports(self, tmp_path):
        pkg = self._mk_project(tmp_path)
        (pkg / "a.py").write_text("from scripts.pkg import b\n")
        (pkg / "b.py").write_text("x = 1\n")
        lever = ImportCycleCheckLever()
        stdout = "scripts/pkg/a.py\nscripts/pkg/b.py\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=stdout, stderr="")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["files_checked"] == 2

    def test_found_direct_cycle(self, tmp_path):
        pkg = self._mk_project(tmp_path)
        (pkg / "a.py").write_text("from scripts.pkg import b\n")
        (pkg / "b.py").write_text("from scripts.pkg import a\n")
        lever = ImportCycleCheckLever()
        stdout = "scripts/pkg/a.py\nscripts/pkg/b.py\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=stdout, stderr="")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        findings = obs["detail"]["findings"]
        assert len(findings) == 1
        assert "<->" in findings[0]
        assert "scripts/pkg/a.py" in findings[0]
        assert "scripts/pkg/b.py" in findings[0]

    def test_ignores_non_project_imports(self, tmp_path):
        pkg = self._mk_project(tmp_path)
        # Both files import stdlib only — no cycle.
        (pkg / "a.py").write_text("import os\nimport json\n")
        (pkg / "b.py").write_text("import sys\nimport json\n")
        lever = ImportCycleCheckLever()
        stdout = "scripts/pkg/a.py\nscripts/pkg/b.py\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=stdout, stderr="")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_error_when_git_missing(self, tmp_path):
        lever = ImportCycleCheckLever()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "git_diff"


class TestLicenseHeaderCheckLever:
    """New source files must declare Copyright / SPDX-License-Identifier."""

    HEADER_PATTERNS = [
        r'^#\s*Copyright',
        r'^//\s*Copyright',
        r'^#\s*SPDX-License-Identifier',
        r'^//\s*SPDX-License-Identifier',
    ]

    def _manifest(self, **overrides):
        inputs = {
            "diff_spec": "HEAD~1..HEAD",
            "extensions": [".py", ".js", ".ts", ".tsx"],
            "header_patterns": list(self.HEADER_PATTERNS),
            "lines_to_check": 10,
        }
        inputs.update(overrides)
        return {"inputs": inputs}

    def test_clean_when_no_new_files(self, tmp_path):
        lever = LicenseHeaderCheckLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["files_checked"] == 0

    def test_clean_when_new_file_has_header(self, tmp_path):
        src = tmp_path / "new.py"
        src.write_text("# Copyright 2026 eidetic-works\n\ndef foo(): pass\n")
        lever = LicenseHeaderCheckLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="new.py\n", stderr="")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["files_checked"] == 1

    def test_found_when_new_file_missing_header(self, tmp_path):
        src = tmp_path / "naked.py"
        src.write_text("def foo(): pass\n")
        lever = LicenseHeaderCheckLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="naked.py\n", stderr="")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert "naked.py" in obs["detail"]["findings"]

    def test_ignores_non_source_extensions(self, tmp_path):
        (tmp_path / "readme.md").write_text("no header here\n")
        (tmp_path / "data.json").write_text("{}\n")
        lever = LicenseHeaderCheckLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="readme.md\ndata.json\n", stderr=""
            )
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["files_checked"] == 0

    def test_error_when_git_missing(self, tmp_path):
        lever = LicenseHeaderCheckLever()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "git_diff"


class TestScopePreEnforceLever:
    """Complements TB's post-review gate by catching scope drift early."""

    def _manifest(self, tasks_path, **overrides):
        inputs = {
            "tasks_path": str(tasks_path),
            "task_id_env": "NUCLEUS_TASK_ID",
            "diff_spec": "HEAD~1..HEAD",
        }
        inputs.update(overrides)
        return {"inputs": inputs}

    def _tasks(self, tmp_path, task_id="t-1", scope=None):
        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text(json.dumps({
            "tasks": [{"id": task_id, "scope": scope or []}]
        }))
        return tasks_file

    def test_skipped_when_no_task_context(self, tmp_path):
        lever = ScopePreEnforceLever()
        with patch.dict("os.environ", {}, clear=True):
            obs = lever.run(self._manifest(tmp_path / "tasks.json"), tmp_path)
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "no_task_context"

    def test_skipped_when_task_scope_empty(self, tmp_path):
        tasks_file = self._tasks(tmp_path, scope=[])
        lever = ScopePreEnforceLever()
        with patch.dict("os.environ", {"NUCLEUS_TASK_ID": "t-1"}, clear=True):
            obs = lever.run(self._manifest(tasks_file), tmp_path)
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "empty_scope"

    def test_clean_when_all_files_in_scope(self, tmp_path):
        tasks_file = self._tasks(tmp_path, scope=["scripts/levers/*.py"])
        lever = ScopePreEnforceLever()
        stdout = "scripts/levers/a.py\nscripts/levers/b.py\n"
        with patch.dict("os.environ", {"NUCLEUS_TASK_ID": "t-1"}, clear=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout=stdout, stderr="")
                obs = lever.run(self._manifest(tasks_file), tmp_path)
        assert obs["outcome"] == "clean"
        assert obs["detail"]["files_checked"] == 2

    def test_found_when_file_outside_scope(self, tmp_path):
        tasks_file = self._tasks(tmp_path, scope=["scripts/levers/*.py"])
        lever = ScopePreEnforceLever()
        stdout = "scripts/levers/a.py\nbackend/app/chat.py\n"
        with patch.dict("os.environ", {"NUCLEUS_TASK_ID": "t-1"}, clear=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout=stdout, stderr="")
                obs = lever.run(self._manifest(tasks_file), tmp_path)
        assert obs["outcome"] == "found"
        findings = obs["detail"]["findings"]
        assert any("OUT_OF_SCOPE: backend/app/chat.py" in f for f in findings)
        # in-scope file must not appear as a finding
        assert not any("scripts/levers/a.py" in f for f in findings)

    def test_error_when_tasks_file_corrupt(self, tmp_path):
        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text("{not json")
        lever = ScopePreEnforceLever()
        with patch.dict("os.environ", {"NUCLEUS_TASK_ID": "t-1"}, clear=True):
            obs = lever.run(self._manifest(tasks_file), tmp_path)
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "task_load"


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


class TestDeadCodeScanLever:
    def _manifest(self, **kw):
        inputs = {"diff_spec": "HEAD~1..HEAD", "ignore_patterns": [], "max_findings": 25}
        inputs.update(kw)
        return {"inputs": inputs}

    def test_clean_when_no_py_files_in_diff(self, tmp_path):
        lever = DeadCodeScanLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["files_checked"] == 0

    def test_found_when_symbol_only_in_defining_file(self, tmp_path):
        lever = DeadCodeScanLever()
        (tmp_path / "mod.py").write_text("def orphan():\n    return 1\n")
        (tmp_path / ".brain").mkdir()
        diff_result = MagicMock(returncode=0, stdout="mod.py\n")
        grep_result = MagicMock(returncode=0, stdout="mod.py\n")
        with patch("subprocess.run", side_effect=[diff_result, grep_result]):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert any("orphan" in f for f in obs["detail"]["findings"])

    def test_skips_underscore_and_test_names(self, tmp_path):
        lever = DeadCodeScanLever()
        (tmp_path / "mod.py").write_text(
            "def _private():\n    pass\n"
            "def test_something():\n    pass\n"
        )
        (tmp_path / ".brain").mkdir()
        diff_result = MagicMock(returncode=0, stdout="mod.py\n")
        with patch("subprocess.run", return_value=diff_result):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_error_when_git_missing(self, tmp_path):
        lever = DeadCodeScanLever()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "git_diff"

    def test_respects_max_findings(self, tmp_path):
        lever = DeadCodeScanLever()
        src = "\n".join(f"def orphan_{i}():\n    pass" for i in range(10))
        (tmp_path / "m.py").write_text(src + "\n")
        (tmp_path / ".brain").mkdir()
        diff_result = MagicMock(returncode=0, stdout="m.py\n")
        grep_result = MagicMock(returncode=0, stdout="m.py\n")
        # 1 diff call + 10 grep calls possible, capped by max_findings=3
        side_effects = [diff_result] + [grep_result] * 10
        with patch("subprocess.run", side_effect=side_effects):
            obs = lever.run(self._manifest(max_findings=3), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert len(obs["detail"]["findings"]) == 3


class TestRuntimeRegressionLever:
    def _manifest(self, path, **kw):
        inputs = {
            "runtimes_path": str(path),
            "window_size": 5,
            "regression_threshold_pct": 25.0,
        }
        inputs.update(kw)
        return {"inputs": inputs}

    def test_skipped_when_file_missing(self, tmp_path):
        lever = RuntimeRegressionLever()
        obs = lever.run(
            self._manifest(tmp_path / "nope.jsonl"),
            tmp_path / ".brain",
        )
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "no_runtime_history"

    def test_skipped_when_insufficient_history(self, tmp_path):
        lever = RuntimeRegressionLever()
        p = tmp_path / "rt.jsonl"
        p.write_text('{"duration_seconds": 1.0}\n')
        obs = lever.run(self._manifest(p), tmp_path / ".brain")
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "insufficient_history"

    def test_clean_when_within_threshold(self, tmp_path):
        lever = RuntimeRegressionLever()
        p = tmp_path / "rt.jsonl"
        p.write_text("\n".join(
            json.dumps({"duration_seconds": d})
            for d in [10.0, 10.5, 11.0, 10.0, 11.0, 12.0]
        ) + "\n")
        obs = lever.run(self._manifest(p), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_found_when_regression_exceeds_threshold(self, tmp_path):
        lever = RuntimeRegressionLever()
        p = tmp_path / "rt.jsonl"
        p.write_text("\n".join(
            json.dumps({"duration_seconds": d})
            for d in [10.0, 10.0, 10.0, 10.0, 10.0, 25.0]
        ) + "\n")
        obs = lever.run(self._manifest(p), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert obs["detail"]["regression_pct"] > 25.0

    def test_error_when_malformed_json(self, tmp_path):
        lever = RuntimeRegressionLever()
        p = tmp_path / "rt.jsonl"
        p.write_text('{"duration_seconds": 1.0}\nnot-json\n')
        obs = lever.run(self._manifest(p), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "parse_runtime"


class TestFlakyTestDetectorLever:
    def _manifest(self, path, **kw):
        inputs = {
            "history_path": str(path),
            "window_hours": 48,
            "max_findings": 25,
        }
        inputs.update(kw)
        return {"inputs": inputs}

    def _line(self, test_id, passed, hours_ago=0):
        from datetime import datetime, timedelta, timezone
        ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
        return json.dumps({"test_id": test_id, "passed": passed, "ts": ts})

    def test_skipped_when_file_missing(self, tmp_path):
        lever = FlakyTestDetectorLever()
        obs = lever.run(
            self._manifest(tmp_path / "nope.jsonl"),
            tmp_path / ".brain",
        )
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "no_test_history"

    def test_clean_when_all_consistent(self, tmp_path):
        lever = FlakyTestDetectorLever()
        p = tmp_path / "hist.jsonl"
        p.write_text(
            self._line("t1", True) + "\n"
            + self._line("t1", True, 1) + "\n"
            + self._line("t2", False) + "\n"
        )
        obs = lever.run(self._manifest(p), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_found_when_test_has_mixed_outcomes(self, tmp_path):
        lever = FlakyTestDetectorLever()
        p = tmp_path / "hist.jsonl"
        p.write_text(
            self._line("t_flaky", True) + "\n"
            + self._line("t_flaky", False, 1) + "\n"
        )
        obs = lever.run(self._manifest(p), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert "t_flaky" in obs["detail"]["findings"]

    def test_respects_window_hours(self, tmp_path):
        lever = FlakyTestDetectorLever()
        p = tmp_path / "hist.jsonl"
        # Flaky outcomes are 100h apart, window = 48h → only latest counts
        p.write_text(
            self._line("t_old", True, 100) + "\n"
            + self._line("t_old", False, 1) + "\n"
        )
        obs = lever.run(self._manifest(p, window_hours=48), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_respects_max_findings(self, tmp_path):
        lever = FlakyTestDetectorLever()
        p = tmp_path / "hist.jsonl"
        lines = []
        for i in range(10):
            lines.append(self._line(f"t{i}", True))
            lines.append(self._line(f"t{i}", False, 1))
        p.write_text("\n".join(lines) + "\n")
        obs = lever.run(self._manifest(p, max_findings=3), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert len(obs["detail"]["findings"]) == 3


class TestCoverageDeltaLever:
    def _manifest(self, cov, base, **kw):
        inputs = {
            "coverage_path": str(cov),
            "baseline_path": str(base),
            "drop_threshold_pct": 2.0,
        }
        inputs.update(kw)
        return {"inputs": inputs}

    def _write_coverage(self, path, line_rate):
        path.write_text(f'<?xml version="1.0"?><coverage line-rate="{line_rate}"/>')

    def _write_baseline(self, path, line_rate):
        path.write_text(json.dumps({"line_rate": line_rate}))

    def test_skipped_when_coverage_missing(self, tmp_path):
        lever = CoverageDeltaLever()
        base = tmp_path / "base.json"
        self._write_baseline(base, 0.85)
        obs = lever.run(
            self._manifest(tmp_path / "no.xml", base),
            tmp_path / ".brain",
        )
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "no_coverage_report"

    def test_skipped_when_baseline_missing(self, tmp_path):
        lever = CoverageDeltaLever()
        cov = tmp_path / "cov.xml"
        self._write_coverage(cov, 0.85)
        obs = lever.run(
            self._manifest(cov, tmp_path / "no.json"),
            tmp_path / ".brain",
        )
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "no_baseline"

    def test_clean_when_above_threshold(self, tmp_path):
        lever = CoverageDeltaLever()
        cov = tmp_path / "cov.xml"
        base = tmp_path / "base.json"
        self._write_coverage(cov, 0.84)
        self._write_baseline(base, 0.85)
        obs = lever.run(self._manifest(cov, base), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_found_when_drop_exceeds_threshold(self, tmp_path):
        lever = CoverageDeltaLever()
        cov = tmp_path / "cov.xml"
        base = tmp_path / "base.json"
        self._write_coverage(cov, 0.75)
        self._write_baseline(base, 0.85)
        obs = lever.run(self._manifest(cov, base), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert obs["detail"]["drop_pp"] > 2.0

    def test_error_when_coverage_xml_malformed(self, tmp_path):
        lever = CoverageDeltaLever()
        cov = tmp_path / "cov.xml"
        base = tmp_path / "base.json"
        cov.write_text("<<not xml>>")
        self._write_baseline(base, 0.85)
        obs = lever.run(self._manifest(cov, base), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "parse_coverage"


class TestDepVulnerabilityCheckLever:
    def _manifest(self, **kw):
        inputs = {"audit_bin": "pip-audit", "timeout_seconds": 60, "max_findings": 25}
        inputs.update(kw)
        return {"inputs": inputs}

    def test_skipped_when_tool_missing(self, tmp_path):
        lever = DepVulnerabilityCheckLever()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["stage"] == "audit_missing"
        assert "pip install pip-audit" in obs["detail"]["reason"]

    def test_clean_on_exit_zero_empty_output(self, tmp_path):
        lever = DepVulnerabilityCheckLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_found_when_vulnerabilities_reported(self, tmp_path):
        lever = DepVulnerabilityCheckLever()
        payload = json.dumps({"dependencies": [
            {"name": "cryptography", "version": "3.0", "vulns": [
                {"id": "GHSA-xxxx", "fix_versions": ["41.0.4"]}
            ]},
        ]})
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout=payload, stderr="")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert any("cryptography" in f and "GHSA-xxxx" in f for f in obs["detail"]["findings"])

    def test_error_on_timeout(self, tmp_path):
        lever = DepVulnerabilityCheckLever()
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="pip-audit", timeout=60)):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "pip_audit"

    def test_error_on_malformed_json(self, tmp_path):
        lever = DepVulnerabilityCheckLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="not-json", stderr="")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "parse_audit"


class TestSchemaDriftCheckLever:
    def _manifest(self, **kw):
        inputs = {
            "diff_spec": "HEAD~1..HEAD",
            "schema_patterns": ["**/*.schema.json"],
            "max_findings": 25,
        }
        inputs.update(kw)
        return {"inputs": inputs}

    def test_clean_when_no_schema_in_diff(self, tmp_path):
        lever = SchemaDriftCheckLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="main.py\n")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["schemas_checked"] == 0

    def test_clean_when_additive_only(self, tmp_path):
        lever = SchemaDriftCheckLever()
        (tmp_path / "user.schema.json").write_text(
            json.dumps({"id": 1, "name": "x", "email": "y"})
        )
        (tmp_path / ".brain").mkdir()
        diff_result = MagicMock(returncode=0, stdout="user.schema.json\n")
        show_result = MagicMock(returncode=0, stdout=json.dumps({"id": 1, "name": "x"}))
        with patch("subprocess.run", side_effect=[diff_result, show_result]):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_found_when_field_removed(self, tmp_path):
        lever = SchemaDriftCheckLever()
        (tmp_path / "user.schema.json").write_text(json.dumps({"id": 1}))
        (tmp_path / ".brain").mkdir()
        diff_result = MagicMock(returncode=0, stdout="user.schema.json\n")
        show_result = MagicMock(returncode=0, stdout=json.dumps({"id": 1, "name": "x"}))
        with patch("subprocess.run", side_effect=[diff_result, show_result]):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert any("removed 'name'" in f for f in obs["detail"]["findings"])

    def test_found_when_type_changed(self, tmp_path):
        lever = SchemaDriftCheckLever()
        (tmp_path / "user.schema.json").write_text(json.dumps({"id": "abc"}))
        (tmp_path / ".brain").mkdir()
        diff_result = MagicMock(returncode=0, stdout="user.schema.json\n")
        show_result = MagicMock(returncode=0, stdout=json.dumps({"id": 1}))
        with patch("subprocess.run", side_effect=[diff_result, show_result]):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert any("type 'id'" in f and "int->str" in f for f in obs["detail"]["findings"])

    def test_error_when_current_malformed(self, tmp_path):
        lever = SchemaDriftCheckLever()
        (tmp_path / "user.schema.json").write_text("{{not json")
        (tmp_path / ".brain").mkdir()
        diff_result = MagicMock(returncode=0, stdout="user.schema.json\n")
        with patch("subprocess.run", side_effect=[diff_result]):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "parse_schema"


class TestApiContractCheckLever:
    def _manifest(self, **kw):
        inputs = {
            "diff_spec": "HEAD~1..HEAD",
            "roots": ["backend"],
            "decorator_names": ["app.get", "app.post", "app.route", "router.get"],
        }
        inputs.update(kw)
        return {"inputs": inputs}

    def test_clean_when_no_py_changed(self, tmp_path):
        lever = ApiContractCheckLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_clean_when_additive_routes(self, tmp_path):
        lever = ApiContractCheckLever()
        current_src = (
            "@app.get('/users')\ndef a(): pass\n"
            "@app.get('/posts')\ndef b(): pass\n"
        )
        previous_src = "@app.get('/users')\ndef a(): pass\n"
        (tmp_path / "backend").mkdir()
        (tmp_path / "backend" / "routes.py").write_text(current_src)
        (tmp_path / ".brain").mkdir()
        diff_result = MagicMock(returncode=0, stdout="backend/routes.py\n")
        show_result = MagicMock(returncode=0, stdout=previous_src)
        with patch("subprocess.run", side_effect=[diff_result, show_result]):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_found_when_route_removed(self, tmp_path):
        lever = ApiContractCheckLever()
        current_src = "@app.get('/users')\ndef a(): pass\n"
        previous_src = (
            "@app.get('/users')\ndef a(): pass\n"
            "@app.post('/posts')\ndef b(): pass\n"
        )
        (tmp_path / "backend").mkdir()
        (tmp_path / "backend" / "routes.py").write_text(current_src)
        (tmp_path / ".brain").mkdir()
        diff_result = MagicMock(returncode=0, stdout="backend/routes.py\n")
        show_result = MagicMock(returncode=0, stdout=previous_src)
        with patch("subprocess.run", side_effect=[diff_result, show_result]):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert any("POST /posts" in f for f in obs["detail"]["findings"])

    def test_ignores_non_decorator_calls(self, tmp_path):
        lever = ApiContractCheckLever()
        current_src = "print('hello')\nresult = app.get('/not-a-decorator')\n"
        previous_src = current_src
        (tmp_path / "backend").mkdir()
        (tmp_path / "backend" / "m.py").write_text(current_src)
        (tmp_path / ".brain").mkdir()
        diff_result = MagicMock(returncode=0, stdout="backend/m.py\n")
        show_result = MagicMock(returncode=0, stdout=previous_src)
        with patch("subprocess.run", side_effect=[diff_result, show_result]):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_error_when_git_missing(self, tmp_path):
        lever = ApiContractCheckLever()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "git_diff"


class TestMigrationLintLever:
    def _manifest(self, **kw):
        inputs = {
            "diff_spec": "HEAD~1..HEAD",
            "migration_globs": ["**/migrations/*.sql"],
            "max_findings": 25,
        }
        inputs.update(kw)
        return {"inputs": inputs}

    def test_clean_when_no_migrations_added(self, tmp_path):
        lever = MigrationLintLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="src/app.py\n")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_clean_when_migration_is_safe(self, tmp_path):
        lever = MigrationLintLever()
        (tmp_path / "migrations").mkdir()
        (tmp_path / "migrations" / "001.sql").write_text(
            "ALTER TABLE users ADD COLUMN email VARCHAR(255) NOT NULL DEFAULT '';\n"
        )
        (tmp_path / ".brain").mkdir()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="migrations/001.sql\n")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_found_not_null_without_default(self, tmp_path):
        lever = MigrationLintLever()
        (tmp_path / "migrations").mkdir()
        (tmp_path / "migrations" / "002.sql").write_text(
            "ALTER TABLE users ADD COLUMN email VARCHAR(255) NOT NULL;\n"
        )
        (tmp_path / ".brain").mkdir()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="migrations/002.sql\n")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert any("NOT NULL without DEFAULT" in f for f in obs["detail"]["findings"])

    def test_found_drop_column(self, tmp_path):
        lever = MigrationLintLever()
        (tmp_path / "migrations").mkdir()
        (tmp_path / "migrations" / "003.sql").write_text(
            "ALTER TABLE users DROP COLUMN legacy_field;\n"
        )
        (tmp_path / ".brain").mkdir()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="migrations/003.sql\n")
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert any("DROP COLUMN" in f for f in obs["detail"]["findings"])

    def test_error_when_git_missing(self, tmp_path):
        lever = MigrationLintLever()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "git_diff"


class TestI18nKeyCheckLever:
    def _manifest(self, **kw):
        inputs = {
            "diff_spec": "HEAD~1..HEAD",
            "source_extensions": [".tsx", ".jsx"],
            "min_length": 3,
            "max_findings": 25,
        }
        inputs.update(kw)
        return {"inputs": inputs}

    def _diff(self, *files):
        parts = []
        for path, *lines in files:
            parts.append(f"diff --git a/{path} b/{path}")
            parts.append(f"--- a/{path}")
            parts.append(f"+++ b/{path}")
            parts.append("@@ -1 +1,%d @@" % len(lines))
            for line in lines:
                parts.append("+" + line)
        return "\n".join(parts) + "\n"

    def test_clean_when_no_frontend_in_diff(self, tmp_path):
        lever = I18nKeyCheckLever()
        diff = self._diff(("a.py", "print('hi')"))
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff)
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_clean_when_wrapped_in_t(self, tmp_path):
        lever = I18nKeyCheckLever()
        diff = self._diff(
            ("src/Comp.tsx", "const x = <p>{t('welcome.message')}</p>;"),
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff)
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_found_hardcoded_jsx_text(self, tmp_path):
        lever = I18nKeyCheckLever()
        diff = self._diff(
            ("src/Comp.tsx", "return <div>Sign in here</div>;"),
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff)
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert any("Sign in here" in f for f in obs["detail"]["findings"])

    def test_respects_min_length(self, tmp_path):
        lever = I18nKeyCheckLever()
        diff = self._diff(
            ("src/Comp.tsx", "return <span>Hi</span>;"),
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff)
            obs = lever.run(self._manifest(min_length=10), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_error_when_git_missing(self, tmp_path):
        lever = I18nKeyCheckLever()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "git_diff"


class TestBundleSizeCheckLever:
    def _manifest(self, stats, base, **kw):
        inputs = {
            "stats_path": str(stats),
            "baseline_path": str(base),
            "regression_threshold_pct": 5.0,
        }
        inputs.update(kw)
        return {"inputs": inputs}

    def test_skipped_when_stats_missing(self, tmp_path):
        lever = BundleSizeCheckLever()
        base = tmp_path / "baseline.json"
        base.write_text(json.dumps({"total_size_bytes": 1000}))
        obs = lever.run(
            self._manifest(tmp_path / "no.json", base),
            tmp_path / ".brain",
        )
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "no_bundle_stats"

    def test_skipped_when_baseline_missing(self, tmp_path):
        lever = BundleSizeCheckLever()
        stats = tmp_path / "stats.json"
        stats.write_text(json.dumps({"total_size_bytes": 1000}))
        obs = lever.run(
            self._manifest(stats, tmp_path / "no.json"),
            tmp_path / ".brain",
        )
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "no_baseline"

    def test_clean_within_threshold(self, tmp_path):
        lever = BundleSizeCheckLever()
        stats = tmp_path / "stats.json"
        base = tmp_path / "baseline.json"
        stats.write_text(json.dumps({"total_size_bytes": 1020}))  # 2% up
        base.write_text(json.dumps({"total_size_bytes": 1000}))
        obs = lever.run(self._manifest(stats, base), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_found_regression_exceeds_threshold(self, tmp_path):
        lever = BundleSizeCheckLever()
        stats = tmp_path / "stats.json"
        base = tmp_path / "baseline.json"
        stats.write_text(json.dumps({"total_size_bytes": 1200}))  # 20% up
        base.write_text(json.dumps({"total_size_bytes": 1000}))
        obs = lever.run(self._manifest(stats, base), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert obs["detail"]["regression_pct"] > 5.0

    def test_error_on_malformed_json(self, tmp_path):
        lever = BundleSizeCheckLever()
        stats = tmp_path / "stats.json"
        base = tmp_path / "baseline.json"
        stats.write_text("{{not-json")
        base.write_text(json.dumps({"total_size_bytes": 1000}))
        obs = lever.run(self._manifest(stats, base), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "parse_stats"


class TestPerfRegressionSpotterLever:
    def _manifest(self, path, **kw):
        inputs = {
            "perf_log_path": str(path),
            "window_size": 5,
            "regression_threshold_pct": 20.0,
        }
        inputs.update(kw)
        return {"inputs": inputs}

    def test_skipped_when_file_missing(self, tmp_path):
        lever = PerfRegressionSpotterLever()
        obs = lever.run(
            self._manifest(tmp_path / "nope.jsonl"),
            tmp_path / ".brain",
        )
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "no_perf_history"

    def test_skipped_when_insufficient_history(self, tmp_path):
        lever = PerfRegressionSpotterLever()
        p = tmp_path / "perf.jsonl"
        p.write_text(json.dumps({"metric_name": "api.p50", "duration_ms": 10.0}) + "\n")
        obs = lever.run(self._manifest(p), tmp_path / ".brain")
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "insufficient_history"

    def test_clean_when_all_metrics_stable(self, tmp_path):
        lever = PerfRegressionSpotterLever()
        p = tmp_path / "perf.jsonl"
        lines = []
        for d in [100.0, 102.0, 98.0, 101.0, 99.0, 103.0]:
            lines.append(json.dumps({"metric_name": "api.p50", "duration_ms": d}))
        for d in [5.0, 5.5, 4.8, 5.2, 5.0, 5.3]:
            lines.append(json.dumps({"metric_name": "db.write", "duration_ms": d}))
        p.write_text("\n".join(lines) + "\n")
        obs = lever.run(self._manifest(p), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["metrics_checked"] == 2

    def test_found_when_one_metric_regresses(self, tmp_path):
        lever = PerfRegressionSpotterLever()
        p = tmp_path / "perf.jsonl"
        lines = []
        for d in [100.0, 102.0, 98.0, 101.0, 99.0, 150.0]:
            lines.append(json.dumps({"metric_name": "api.p50", "duration_ms": d}))
        for d in [5.0, 5.5, 4.8, 5.2, 5.0, 5.3]:
            lines.append(json.dumps({"metric_name": "db.write", "duration_ms": d}))
        p.write_text("\n".join(lines) + "\n")
        obs = lever.run(self._manifest(p), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert any("api.p50" in f for f in obs["detail"]["findings"])
        assert not any("db.write" in f for f in obs["detail"]["findings"])

    def test_error_when_malformed_json(self, tmp_path):
        lever = PerfRegressionSpotterLever()
        p = tmp_path / "perf.jsonl"
        p.write_text(
            json.dumps({"metric_name": "a", "duration_ms": 1.0}) + "\nnot-json\n"
        )
        obs = lever.run(self._manifest(p), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "parse_perf"


class TestA11ySmokeLever:
    def _manifest(self, url="https://example.com", **kw):
        inputs = {
            "scanner_bin": "pa11y",
            "url": url,
            "extra_args": ["--reporter", "json"],
            "timeout_seconds": 10,
        }
        inputs.update(kw)
        return {"inputs": inputs}

    def test_skipped_when_no_url(self, tmp_path):
        lever = A11ySmokeLever()
        obs = lever.run(self._manifest(url=""), tmp_path / ".brain")
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "no_url_configured"

    def test_error_when_scanner_missing(self, tmp_path):
        lever = A11ySmokeLever()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "scanner_missing"

    def test_clean_when_no_violations(self, tmp_path):
        lever = A11ySmokeLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({"violations": []}),
                stderr="",
            )
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["violations"] == 0

    def test_found_parses_pa11y_list_shape(self, tmp_path):
        lever = A11ySmokeLever()
        payload = [
            {"type": "error", "code": "WCAG2AA.Principle1", "message": "no alt"},
            {"type": "error", "code": "WCAG2AA.Principle4", "message": "missing label"},
        ]
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=2, stdout=json.dumps(payload), stderr=""
            )
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert obs["detail"]["violations"] == 2
        assert any("no alt" in f for f in obs["detail"]["findings"])

    def test_error_on_malformed_json(self, tmp_path):
        lever = A11ySmokeLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="not-json", stderr=""
            )
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "parse_a11y"


class TestDeadLinkCheckLever:
    def _manifest(self, **kw):
        inputs = {"diff_spec": "HEAD~1..HEAD"}
        inputs.update(kw)
        return {"inputs": inputs}

    def _diff_mock(self, paths):
        return MagicMock(
            returncode=0,
            stdout="\n".join(paths) + ("\n" if paths else ""),
            stderr="",
        )

    def test_clean_when_no_md_changed(self, tmp_path):
        lever = DeadLinkCheckLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = self._diff_mock([])
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["markdowns_checked"] == 0

    def test_clean_when_all_links_resolve(self, tmp_path):
        lever = DeadLinkCheckLever()
        (tmp_path / "target.md").write_text("# target")
        doc = tmp_path / "doc.md"
        doc.write_text("See [target](target.md) and [ext](https://example.com)")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = self._diff_mock(["doc.md"])
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["markdowns_checked"] == 1

    def test_found_when_relative_link_missing(self, tmp_path):
        lever = DeadLinkCheckLever()
        doc = tmp_path / "doc.md"
        doc.write_text("See [gone](missing.md#frag)")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = self._diff_mock(["doc.md"])
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert any("missing.md" in f for f in obs["detail"]["findings"])

    def test_ignores_external_and_anchor_only(self, tmp_path):
        lever = DeadLinkCheckLever()
        doc = tmp_path / "doc.md"
        doc.write_text(
            "[x](http://a.example) [y](mailto:a@b) [z](#section) "
            "[t](tel:123) [d](data:image/png;base64,abc)"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = self._diff_mock(["doc.md"])
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_error_when_git_missing(self, tmp_path):
        lever = DeadLinkCheckLever()
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "git_diff"


class TestEnvVarDriftLever:
    def _manifest(self, **kw):
        inputs = {
            "diff_spec": "HEAD~1..HEAD",
            "env_example_path": ".env.example",
        }
        inputs.update(kw)
        return {"inputs": inputs}

    def _diff_mock(self, paths):
        return MagicMock(
            returncode=0,
            stdout="\n".join(paths) + ("\n" if paths else ""),
            stderr="",
        )

    def test_skipped_when_env_example_missing(self, tmp_path):
        lever = EnvVarDriftLever()
        obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "no_env_example"

    def test_clean_when_all_declared(self, tmp_path):
        lever = EnvVarDriftLever()
        (tmp_path / ".env.example").write_text("FOO=a\nBAR=b\n")
        (tmp_path / "app.py").write_text(
            "import os\nx = os.getenv('FOO')\ny = os.environ['BAR']\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = self._diff_mock(["app.py"])
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["declared_vars"] == 2

    def test_found_when_undeclared_var_referenced(self, tmp_path):
        lever = EnvVarDriftLever()
        (tmp_path / ".env.example").write_text("FOO=a\n# comment\n")
        (tmp_path / "app.py").write_text(
            "import os\nx = os.environ.get('NEW_KEY')\ny = os.getenv('FOO')\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = self._diff_mock(["app.py"])
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert any("NEW_KEY" in f for f in obs["detail"]["findings"])
        assert not any("FOO" in f for f in obs["detail"]["findings"])

    def test_ignores_non_literal_names(self, tmp_path):
        lever = EnvVarDriftLever()
        (tmp_path / ".env.example").write_text("")
        (tmp_path / "app.py").write_text(
            "import os\nname = 'X'\nx = os.getenv(name)\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = self._diff_mock(["app.py"])
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "clean"

    def test_error_when_git_missing(self, tmp_path):
        lever = EnvVarDriftLever()
        (tmp_path / ".env.example").write_text("FOO=a\n")
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            obs = lever.run(self._manifest(), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "git_diff"


class TestConfigSchemaCheckLever:
    def _manifest(self, schemas, **kw):
        inputs = {"diff_spec": "HEAD~1..HEAD", "schemas": schemas}
        inputs.update(kw)
        return {"inputs": inputs}

    def _diff_mock(self, paths):
        return MagicMock(
            returncode=0,
            stdout="\n".join(paths) + ("\n" if paths else ""),
            stderr="",
        )

    def test_skipped_when_no_schemas_configured(self, tmp_path):
        lever = ConfigSchemaCheckLever()
        obs = lever.run(self._manifest({}), tmp_path / ".brain")
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "no_schemas_configured"

    def test_clean_when_config_not_in_diff(self, tmp_path):
        lever = ConfigSchemaCheckLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = self._diff_mock(["other.py"])
            obs = lever.run(
                self._manifest({"config.json": {"k": "str"}}),
                tmp_path / ".brain",
            )
        assert obs["outcome"] == "clean"
        assert obs["detail"]["configs_checked"] == 0

    def test_clean_when_all_keys_match(self, tmp_path):
        lever = ConfigSchemaCheckLever()
        (tmp_path / "config.json").write_text(
            json.dumps({"name": "x", "port": 8080, "ratio": 1.5})
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = self._diff_mock(["config.json"])
            obs = lever.run(
                self._manifest({
                    "config.json": {
                        "name": "str",
                        "port": "int",
                        "ratio": "int|float",
                    }
                }),
                tmp_path / ".brain",
            )
        assert obs["outcome"] == "clean"
        assert obs["detail"]["configs_checked"] == 1

    def test_found_when_key_missing_or_wrong_type(self, tmp_path):
        lever = ConfigSchemaCheckLever()
        (tmp_path / "config.json").write_text(
            json.dumps({"port": "8080"})
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = self._diff_mock(["config.json"])
            obs = lever.run(
                self._manifest({
                    "config.json": {"name": "str", "port": "int"}
                }),
                tmp_path / ".brain",
            )
        assert obs["outcome"] == "found"
        findings = obs["detail"]["findings"]
        assert any("missing 'name'" in f for f in findings)
        assert any("'port' is str" in f for f in findings)

    def test_error_when_config_malformed_json(self, tmp_path):
        lever = ConfigSchemaCheckLever()
        (tmp_path / "config.json").write_text("{{not-json")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = self._diff_mock(["config.json"])
            obs = lever.run(
                self._manifest({"config.json": {"k": "str"}}),
                tmp_path / ".brain",
            )
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "parse_config"


class TestBullAuditLever:
    """Brazen Bull skeleton — 5 frozen invariants.

    Invariant matrix:
      schema_valid            unparseable JSONL in window → finding
      outcome_in_set          outcome not in OUTCOMES → finding
      duration_bounded        duration_ms > threshold → finding
      csr_not_collapsed       ratio < floor OR CSR unavailable → finding
      no_repeated_lever_errors  (lever, stage) error count > N → finding
    """

    def _manifest(self, ledger, csr=None, **kw):
        inputs = {
            "ledger_path": str(ledger),
            "window_events": 100,
            "duration_threshold_ms": 30_000,
            "csr_floor": 0.5,
            "repeated_error_threshold": 3,
        }
        if csr is not None:
            inputs["csr_path"] = str(csr)
        inputs.update(kw)
        return {"inputs": inputs}

    def _good_event(self, lever="foo", outcome="clean", duration_ms=10, stage=None):
        detail = {"stage": stage} if stage else {}
        line = {
            "ts": "2026-04-12T10:00:00+00:00",
            "type": f"lever.{lever}.observation",
            "lever": lever,
            "outcome": outcome,
            "detail": detail,
            "duration_ms": duration_ms,
        }
        return json.dumps(line)

    def _write_csr(self, path, ratio):
        path.write_text(json.dumps({"ratio": ratio, "claims_total": 10}))

    def test_skipped_when_ledger_missing(self, tmp_path):
        lever = BullAuditLever()
        obs = lever.run(
            self._manifest(tmp_path / "nope.jsonl"),
            tmp_path / ".brain",
        )
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "no_ledger"

    def test_skipped_when_ledger_empty(self, tmp_path):
        lever = BullAuditLever()
        p = tmp_path / "events.jsonl"
        p.write_text("")
        obs = lever.run(self._manifest(p), tmp_path / ".brain")
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "empty_ledger"

    def test_clean_when_all_invariants_hold(self, tmp_path):
        lever = BullAuditLever()
        p = tmp_path / "events.jsonl"
        csr = tmp_path / "csr.json"
        p.write_text("\n".join(self._good_event() for _ in range(10)) + "\n")
        self._write_csr(csr, 0.95)
        obs = lever.run(self._manifest(p, csr=csr), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["invariants_checked"] == 5

    def test_found_schema_invalid_in_window(self, tmp_path):
        lever = BullAuditLever()
        p = tmp_path / "events.jsonl"
        csr = tmp_path / "csr.json"
        self._write_csr(csr, 0.9)
        p.write_text(
            self._good_event() + "\nnot-json\n" + self._good_event() + "\n"
        )
        obs = lever.run(self._manifest(p, csr=csr), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert any("schema_valid" in f for f in obs["detail"]["findings"])

    def test_outcome_in_set_invariant_unit(self, tmp_path):
        """outcome_in_set is defense-in-depth: LedgerEvent.from_jsonl already
        rejects unknown outcomes at parse time, so to exercise the invariant
        we build events directly and call the function.
        """
        from scripts.levers.bull_audit import _inv_outcome_in_set, _InvariantContext
        bad_event = LedgerEvent(
            ts="2026-04-12T10:00:00+00:00",
            type="lever.foo.observation",
            lever="foo",
            outcome="clean",
            detail={},
        )
        object.__setattr__(bad_event, "outcome", "bogus")
        ctx = _InvariantContext(
            events=[bad_event], schema_errors=0, csr=0.9,
            duration_threshold_ms=30_000, csr_floor=0.5,
            repeated_error_threshold=3,
        )
        finding = _inv_outcome_in_set(ctx)
        assert finding is not None
        assert "bogus" in finding

    def test_found_duration_above_threshold(self, tmp_path):
        lever = BullAuditLever()
        p = tmp_path / "events.jsonl"
        csr = tmp_path / "csr.json"
        self._write_csr(csr, 0.9)
        lines = [self._good_event(duration_ms=60_000)] + [self._good_event() for _ in range(3)]
        p.write_text("\n".join(lines) + "\n")
        obs = lever.run(self._manifest(p, csr=csr), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert any("duration_bounded" in f for f in obs["detail"]["findings"])

    def test_found_csr_collapsed(self, tmp_path):
        lever = BullAuditLever()
        p = tmp_path / "events.jsonl"
        csr = tmp_path / "csr.json"
        self._write_csr(csr, 0.30)
        p.write_text(self._good_event() + "\n")
        obs = lever.run(self._manifest(p, csr=csr), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert any("csr_not_collapsed" in f for f in obs["detail"]["findings"])

    def test_found_csr_unavailable(self, tmp_path):
        lever = BullAuditLever()
        p = tmp_path / "events.jsonl"
        p.write_text(self._good_event() + "\n")
        obs = lever.run(
            self._manifest(p, csr=tmp_path / "nope.json"),
            tmp_path / ".brain",
        )
        assert obs["outcome"] == "found"
        assert any("csr_not_collapsed" in f for f in obs["detail"]["findings"])

    def test_found_repeated_lever_errors(self, tmp_path):
        lever = BullAuditLever()
        p = tmp_path / "events.jsonl"
        csr = tmp_path / "csr.json"
        self._write_csr(csr, 0.9)
        lines = [
            self._good_event(outcome="error", stage="git_diff", lever="ruff_chain")
            for _ in range(5)
        ]
        p.write_text("\n".join(lines) + "\n")
        obs = lever.run(self._manifest(p, csr=csr), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert any("no_repeated_lever_errors" in f for f in obs["detail"]["findings"])

    def test_window_limits_read(self, tmp_path):
        """Events beyond the window must not influence invariants."""
        lever = BullAuditLever()
        p = tmp_path / "events.jsonl"
        csr = tmp_path / "csr.json"
        self._write_csr(csr, 0.9)
        old_bad = self._good_event(outcome="bogus")
        recent_good = [self._good_event() for _ in range(5)]
        p.write_text("\n".join([old_bad] * 10 + recent_good) + "\n")
        manifest = self._manifest(p, csr=csr)
        manifest["inputs"]["window_events"] = 5
        obs = lever.run(manifest, tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["events_read"] == 5

    def test_grandfathered_legacy_events_not_schema_errors(self, tmp_path):
        """Pre-substrate events (one-token type + ``timestamp`` not ``ts``)
        are explicitly grandfathered per the substrate plan. bull_audit
        must not count them as schema drift, or the invariant is
        permanently broken on any live ledger."""
        lever = BullAuditLever()
        p = tmp_path / "events.jsonl"
        csr = tmp_path / "csr.json"
        self._write_csr(csr, 0.9)
        legacy = json.dumps({
            "event_id": "evt-1",
            "timestamp": "2026-01-16T18:53:08+0530",
            "type": "session_saved",
            "emitter": "brain_save_session",
            "data": {"session_id": "s1"},
        })
        real_drift = "not-json-at-all"
        lines = [legacy] * 5 + [real_drift] + [self._good_event() for _ in range(3)]
        p.write_text("\n".join(lines) + "\n")
        obs = lever.run(self._manifest(p, csr=csr), tmp_path / ".brain")
        assert obs["detail"]["schema_errors"] == 1, obs["detail"]

    def test_grandfathering_rejects_dotted_type_without_ts(self, tmp_path):
        """Dotted types (new-substrate convention) missing ``ts`` are
        real drift, not grandfathered. A dotted type that uses
        ``timestamp`` is still a bug."""
        lever = BullAuditLever()
        p = tmp_path / "events.jsonl"
        csr = tmp_path / "csr.json"
        self._write_csr(csr, 0.9)
        bad_new = json.dumps({
            "timestamp": "2026-04-13T00:00:00+00:00",
            "type": "lever.foo.observation",
        })
        p.write_text(bad_new + "\n" + self._good_event() + "\n")
        obs = lever.run(self._manifest(p, csr=csr), tmp_path / ".brain")
        assert obs["detail"]["schema_errors"] == 1


class TestPlanAuditLever:
    """Wave 7+8 accountability lever.

    Bucket matrix — evaluation ORDER matters:
      1. never_audited          — no results entry
      2. stale                  — disk mtime > results.plan_mtime + threshold
                                  (BEATS abandoned: touch = reconsideration)
      3. needs_deepen           — verdict=DEEPEN
      4. deepen_exhausted       — verdict=DEEPEN_EXHAUSTED (audit gave up)
      5. failed_audit           — verdict=REJECT
      6. abandoned              — verdict=ABANDONED (NOT rotting)
      7. verified_with_evidence — verdict=ACCEPT, quality ∈ {strong, weak}
      8. verified_no_evidence   — verdict=ACCEPT, quality ∈ {none, missing}
                                  ← Wave 8: ROTTING (rubber-stamp ACCEPT)

    rotting = never_audited ∪ stale ∪ needs_deepen ∪ deepen_exhausted
              ∪ failed_audit ∪ verified_no_evidence
    """

    def _manifest(self, plan_dirs, results_path, **kw):
        inputs = {
            "plan_dirs": [str(p) for p in plan_dirs],
            "audit_results_path": str(results_path),
            "max_report": 10,
            "stale_threshold_seconds": 60,
        }
        inputs.update(kw)
        return {"inputs": inputs}

    def _write_plan(self, path, name, mtime_iso):
        plan = path / name
        plan.write_text(f"# {name}\n")
        dt = datetime.fromisoformat(mtime_iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ts = dt.timestamp()
        os.utime(plan, (ts, ts))
        return plan

    def test_skipped_when_plan_dirs_missing(self, tmp_path):
        lever = PlanAuditLever()
        ghost_a = tmp_path / "no-such-a"
        ghost_b = tmp_path / "no-such-b"
        results = tmp_path / "results.json"
        results.write_text("{}")
        obs = lever.run(self._manifest([ghost_a, ghost_b], results), tmp_path / ".brain")
        assert obs["outcome"] == "skipped"
        assert obs["detail"]["reason"] == "no_plans_found"

    def test_clean_when_all_plans_verified(self, tmp_path):
        lever = PlanAuditLever()
        pdir = tmp_path / "plans"
        pdir.mkdir()
        self._write_plan(pdir, "a.md", "2026-04-10T10:00:00")
        self._write_plan(pdir, "b.md", "2026-04-09T10:00:00")
        results = tmp_path / "results.json"
        results.write_text(json.dumps({
            "a.md": {
                "verdict": "ACCEPT",
                "plan_mtime": "2026-04-10T10:00:30",
                "verification_quality": "strong",
            },
            "b.md": {
                "verdict": "ACCEPT",
                "plan_mtime": "2026-04-09T10:00:30",
                "verification_quality": "strong",
            },
        }))
        obs = lever.run(self._manifest([pdir], results), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["plans_total"] == 2
        assert obs["detail"]["by_bucket"]["verified_with_evidence"] == 2

    def test_found_when_plan_never_audited(self, tmp_path):
        lever = PlanAuditLever()
        pdir = tmp_path / "plans"
        pdir.mkdir()
        self._write_plan(pdir, "fresh.md", "2026-04-12T10:00:00")
        results = tmp_path / "results.json"
        results.write_text("{}")
        obs = lever.run(self._manifest([pdir], results), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert obs["detail"]["plans_rotting"] == 1
        assert obs["detail"]["by_bucket"]["never_audited"] == 1
        assert obs["detail"]["top_rot"][0]["name"] == "fresh.md"
        assert obs["detail"]["top_rot"][0]["bucket"] == "never_audited"

    def test_found_when_plan_stale(self, tmp_path):
        lever = PlanAuditLever()
        pdir = tmp_path / "plans"
        pdir.mkdir()
        self._write_plan(pdir, "drifted.md", "2026-04-12T12:00:00")
        results = tmp_path / "results.json"
        results.write_text(json.dumps({
            "drifted.md": {
                "verdict": "ACCEPT",
                "plan_mtime": "2026-04-10T10:00:00",
            }
        }))
        obs = lever.run(self._manifest([pdir], results), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert obs["detail"]["by_bucket"]["stale"] == 1
        assert obs["detail"]["top_rot"][0]["bucket"] == "stale"

    def test_found_when_verdict_is_deepen_or_reject(self, tmp_path):
        lever = PlanAuditLever()
        pdir = tmp_path / "plans"
        pdir.mkdir()
        self._write_plan(pdir, "deep.md", "2026-04-10T10:00:00")
        self._write_plan(pdir, "rej.md", "2026-04-10T10:00:00")
        results = tmp_path / "results.json"
        results.write_text(json.dumps({
            "deep.md": {"verdict": "DEEPEN", "plan_mtime": "2026-04-10T10:00:30"},
            "rej.md": {"verdict": "REJECT", "plan_mtime": "2026-04-10T10:00:30"},
        }))
        obs = lever.run(self._manifest([pdir], results), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert obs["detail"]["by_bucket"]["needs_deepen"] == 1
        assert obs["detail"]["by_bucket"]["failed_audit"] == 1

    def test_found_when_verdict_is_deepen_exhausted(self, tmp_path):
        lever = PlanAuditLever()
        pdir = tmp_path / "plans"
        pdir.mkdir()
        self._write_plan(pdir, "exh.md", "2026-04-10T10:00:00")
        results = tmp_path / "results.json"
        results.write_text(json.dumps({
            "exh.md": {
                "verdict": "DEEPEN_EXHAUSTED",
                "plan_mtime": "2026-04-10T10:00:30",
            },
        }))
        obs = lever.run(self._manifest([pdir], results), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert obs["detail"]["by_bucket"]["deepen_exhausted"] == 1
        assert obs["detail"]["plans_rotting"] == 1
        assert obs["detail"]["top_rot"][0]["bucket"] == "deepen_exhausted"

    def test_verdict_abandoned_does_not_count_as_rot(self, tmp_path):
        lever = PlanAuditLever()
        pdir = tmp_path / "plans"
        pdir.mkdir()
        self._write_plan(pdir, "dead.md", "2026-04-10T10:00:00")
        results = tmp_path / "results.json"
        results.write_text(json.dumps({
            "dead.md": {"verdict": "ABANDONED", "plan_mtime": "2026-04-10T10:00:30"},
        }))
        obs = lever.run(self._manifest([pdir], results), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["by_bucket"]["abandoned"] == 1
        assert "plans_rotting" not in obs["detail"]

    def test_top_rot_ordered_newest_first_and_capped_at_max_report(self, tmp_path):
        lever = PlanAuditLever()
        pdir = tmp_path / "plans"
        pdir.mkdir()
        # 12 rotting plans, mtimes April 1..12
        for day in range(1, 13):
            self._write_plan(pdir, f"p{day:02d}.md", f"2026-04-{day:02d}T10:00:00")
        results = tmp_path / "results.json"
        results.write_text("{}")
        m = self._manifest([pdir], results)
        m["inputs"]["max_report"] = 5
        obs = lever.run(m, tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert obs["detail"]["plans_rotting"] == 12
        assert len(obs["detail"]["top_rot"]) == 5
        names = [r["name"] for r in obs["detail"]["top_rot"]]
        assert names == ["p12.md", "p11.md", "p10.md", "p09.md", "p08.md"]

    def test_error_when_results_json_malformed(self, tmp_path):
        lever = PlanAuditLever()
        pdir = tmp_path / "plans"
        pdir.mkdir()
        self._write_plan(pdir, "x.md", "2026-04-10T10:00:00")
        results = tmp_path / "results.json"
        results.write_text("{not valid json")
        obs = lever.run(self._manifest([pdir], results), tmp_path / ".brain")
        assert obs["outcome"] == "error"
        assert obs["detail"]["stage"] == "parse_results"

    def test_results_json_retry_success(self, tmp_path, monkeypatch):
        """Simulate TB mid-write TOCTOU: first read fails, second succeeds.
        Lever must retry once and classify normally."""
        lever = PlanAuditLever()
        pdir = tmp_path / "plans"
        pdir.mkdir()
        self._write_plan(pdir, "x.md", "2026-04-10T10:00:00")
        results = tmp_path / "results.json"
        results.write_text(json.dumps({
            "x.md": {
                "verdict": "ACCEPT",
                "plan_mtime": "2026-04-10T10:00:30",
                "verification_quality": "strong",
            },
        }))

        real_read = Path.read_text
        call_count = {"n": 0}

        def flaky_read(self, *a, **kw):
            if self == results and call_count["n"] == 0:
                call_count["n"] += 1
                return "{ broken first read"
            return real_read(self, *a, **kw)

        monkeypatch.setattr(Path, "read_text", flaky_read)
        obs = lever.run(self._manifest([pdir], results), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert call_count["n"] == 1

    def test_plan_deleted_during_walk(self, tmp_path, monkeypatch):
        """Plan file deleted between enumerate and stat — FileNotFoundError
        must NOT error the lever; skip the plan and classify the rest."""
        lever = PlanAuditLever()
        pdir = tmp_path / "plans"
        pdir.mkdir()
        self._write_plan(pdir, "keep.md", "2026-04-10T10:00:00")
        ghost = self._write_plan(pdir, "ghost.md", "2026-04-10T10:00:00")
        results = tmp_path / "results.json"
        results.write_text(json.dumps({
            "keep.md": {
                "verdict": "ACCEPT",
                "plan_mtime": "2026-04-10T10:00:30",
                "verification_quality": "strong",
            },
        }))

        real_stat = Path.stat

        def flaky_stat(self, *a, **kw):
            if self == ghost:
                raise FileNotFoundError(str(self))
            return real_stat(self, *a, **kw)

        monkeypatch.setattr(Path, "stat", flaky_stat)
        obs = lever.run(self._manifest([pdir], results), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["plans_total"] == 1

    # --- Wave 8: verification_quality split --------------------------------

    def test_verified_with_evidence_when_quality_strong(self, tmp_path):
        lever = PlanAuditLever()
        pdir = tmp_path / "plans"
        pdir.mkdir()
        self._write_plan(pdir, "evidence.md", "2026-04-10T10:00:00")
        results = tmp_path / "results.json"
        results.write_text(json.dumps({
            "evidence.md": {
                "verdict": "ACCEPT",
                "plan_mtime": "2026-04-10T10:00:30",
                "verification_quality": "strong",
            },
        }))
        obs = lever.run(self._manifest([pdir], results), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["by_bucket"]["verified_with_evidence"] == 1
        assert "verified_no_evidence" not in obs["detail"]["by_bucket"]

    def test_verified_with_evidence_when_quality_weak(self, tmp_path):
        lever = PlanAuditLever()
        pdir = tmp_path / "plans"
        pdir.mkdir()
        self._write_plan(pdir, "weak.md", "2026-04-10T10:00:00")
        results = tmp_path / "results.json"
        results.write_text(json.dumps({
            "weak.md": {
                "verdict": "ACCEPT",
                "plan_mtime": "2026-04-10T10:00:30",
                "verification_quality": "weak",
            },
        }))
        obs = lever.run(self._manifest([pdir], results), tmp_path / ".brain")
        assert obs["outcome"] == "clean"
        assert obs["detail"]["by_bucket"]["verified_with_evidence"] == 1

    def test_verified_no_evidence_when_quality_none(self, tmp_path):
        lever = PlanAuditLever()
        pdir = tmp_path / "plans"
        pdir.mkdir()
        self._write_plan(pdir, "rubber.md", "2026-04-10T10:00:00")
        results = tmp_path / "results.json"
        results.write_text(json.dumps({
            "rubber.md": {
                "verdict": "ACCEPT",
                "plan_mtime": "2026-04-10T10:00:30",
                "verification_quality": "none",
            },
        }))
        obs = lever.run(self._manifest([pdir], results), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert obs["detail"]["by_bucket"]["verified_no_evidence"] == 1
        assert obs["detail"]["plans_rotting"] == 1
        assert obs["detail"]["top_rot"][0]["bucket"] == "verified_no_evidence"
        assert obs["detail"]["top_rot"][0]["name"] == "rubber.md"

    def test_verified_no_evidence_when_quality_field_missing(self, tmp_path):
        lever = PlanAuditLever()
        pdir = tmp_path / "plans"
        pdir.mkdir()
        self._write_plan(pdir, "missing.md", "2026-04-10T10:00:00")
        results = tmp_path / "results.json"
        results.write_text(json.dumps({
            "missing.md": {
                "verdict": "ACCEPT",
                "plan_mtime": "2026-04-10T10:00:30",
            },
        }))
        obs = lever.run(self._manifest([pdir], results), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert obs["detail"]["by_bucket"]["verified_no_evidence"] == 1

    def test_top_rot_ordering_never_audited_beats_verified_no_evidence(
        self, tmp_path,
    ):
        """Priority: never_audited > stale > deepen_exhausted > needs_deepen >
        failed_audit > verified_no_evidence. Assert mtime-tie-broken ordering
        places fresher verified_no_evidence BELOW older never_audited because
        top_rot sorts by mtime, while bucket membership itself is correct."""
        lever = PlanAuditLever()
        pdir = tmp_path / "plans"
        pdir.mkdir()
        # Three plans, all rotting, each in a different bucket:
        self._write_plan(pdir, "new.md", "2026-04-12T10:00:00")          # never_audited
        self._write_plan(pdir, "rej.md", "2026-04-11T10:00:00")          # failed_audit
        self._write_plan(pdir, "rubber.md", "2026-04-10T10:00:00")       # verified_no_evidence
        results = tmp_path / "results.json"
        results.write_text(json.dumps({
            "rej.md": {"verdict": "REJECT", "plan_mtime": "2026-04-11T10:00:30"},
            "rubber.md": {
                "verdict": "ACCEPT",
                "plan_mtime": "2026-04-10T10:00:30",
                "verification_quality": "none",
            },
        }))
        obs = lever.run(self._manifest([pdir], results), tmp_path / ".brain")
        assert obs["outcome"] == "found"
        assert obs["detail"]["plans_rotting"] == 3
        assert obs["detail"]["by_bucket"] == {
            "never_audited": 1,
            "failed_audit": 1,
            "verified_no_evidence": 1,
        }
        # mtime-based ordering within rotting: newer first.
        buckets_in_order = [r["bucket"] for r in obs["detail"]["top_rot"]]
        assert buckets_in_order == [
            "never_audited",
            "failed_audit",
            "verified_no_evidence",
        ]
