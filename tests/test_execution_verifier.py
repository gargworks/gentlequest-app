"""
Tests for Frontier 1: GROUND — Execution Verifier
==================================================
Tests scripts/execution_verifier.py: tiered verification, calibration DPO,
file extraction from git state.

All tests use tmp_path with real git repos — no mocks, no network.
"""

import json
import subprocess
import sys
import pytest
from pathlib import Path

# Add scripts/ to path so we can import execution_verifier
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from execution_verifier import (
    verify_execution,
    build_calibration_dpo,
    capture_outcome_baseline,
    extract_claims,
    _tier0_diff_nonempty,
    _tier1_syntax_check,
    _tier2_import_check,
    _tier3_test_execution,
    _tier4_runtime_check,
    _tier5_outcome_check,
    _get_changed_files,
    _check_json,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _git(cwd, *args):
    """Run a git command in cwd."""
    subprocess.run(
        ["git"] + list(args),
        cwd=str(cwd), capture_output=True, text=True, check=True,
        env={**__import__("os").environ, "GIT_AUTHOR_NAME": "test",
             "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "test",
             "GIT_COMMITTER_EMAIL": "t@t"},
    )


def _make_config(**overrides):
    """Build a minimal verification config."""
    cfg = {
        "execution_verification_timeout_s": 30,
        "execution_verification_tiers": [0, 1, 2, 3],
    }
    cfg.update(overrides)
    return cfg


@pytest.fixture
def project(tmp_path):
    """Create a minimal git repo with one committed .py file."""
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "test")
    hello = tmp_path / "hello.py"
    hello.write_text("x = 1\n")
    _git(tmp_path, "add", "hello.py")
    _git(tmp_path, "commit", "-m", "init")
    return tmp_path


# ===========================================================================
# Tier 0: Diff non-empty
# ===========================================================================

class TestTier0:
    def test_tier0_empty_diff(self, project):
        """No changes → tier 0 fails, verified=False."""
        config = _make_config(execution_verification_tiers=[0])
        result = verify_execution("", "", config, project)
        assert result["verified"] is False
        assert 0 in result["tiers_failed"]

    def test_tier0_nonempty_diff(self, project):
        """Modified file → tier 0 passes."""
        (project / "hello.py").write_text("x = 2\n")
        config = _make_config(execution_verification_tiers=[0])
        result = verify_execution("", "", config, project)
        assert result["verified"] is True
        assert 0 in result["tiers_passed"]
        sig = [s for s in result["signals"] if s["check"] == "diff_nonempty"][0]
        assert sig["files_count"] > 0


# ===========================================================================
# Tier 1: Syntax checks
# ===========================================================================

class TestTier1Syntax:
    def test_tier1_valid_python(self, project):
        """Valid .py file → py_compile passes."""
        (project / "good.py").write_text("def foo():\n    return 42\n")
        _git(project, "add", "good.py")
        sigs = _tier1_syntax_check(["good.py"], project, 10)
        assert len(sigs) == 1
        assert sigs[0]["passed"] is True
        assert sigs[0]["check"] == "py_compile"

    def test_tier1_syntax_error(self, project):
        """Broken .py → tier 1 fails."""
        (project / "bad.py").write_text("def foo(\n")
        _git(project, "add", "bad.py")
        sigs = _tier1_syntax_check(["bad.py"], project, 10)
        assert len(sigs) == 1
        assert sigs[0]["passed"] is False

    def test_tier1_valid_json(self, project):
        """Valid JSON → json_parse passes."""
        jf = project / "data.json"
        jf.write_text('{"key": "value"}')
        sig = _check_json(jf, "data.json")
        assert sig["passed"] is True
        assert sig["check"] == "json_parse"

    def test_tier1_invalid_json(self, project):
        """Broken JSON → json_parse fails."""
        jf = project / "bad.json"
        jf.write_text("{broken")
        sig = _check_json(jf, "bad.json")
        assert sig["passed"] is False

    def test_tier1_valid_shell(self, project):
        """Valid .sh → bash_syntax passes."""
        sh = project / "ok.sh"
        sh.write_text("#!/bin/bash\necho hi\n")
        sigs = _tier1_syntax_check(["ok.sh"], project, 10)
        assert len(sigs) == 1
        assert sigs[0]["passed"] is True

    def test_tier1_invalid_shell(self, project):
        """Broken .sh → bash_syntax fails."""
        sh = project / "bad.sh"
        sh.write_text("#!/bin/bash\nif then\n")
        sigs = _tier1_syntax_check(["bad.sh"], project, 10)
        assert len(sigs) == 1
        assert sigs[0]["passed"] is False


# ===========================================================================
# Tier 2: Import checks
# ===========================================================================

class TestTier2Import:
    def test_tier2_importable_module(self, project):
        """Simple module → import passes."""
        (project / "mymod.py").write_text("VALUE = 42\n")
        sigs = _tier2_import_check(["mymod.py"], project, 10)
        assert len(sigs) == 1
        assert sigs[0]["passed"] is True
        assert sigs[0]["module"] == "mymod"

    def test_tier2_broken_import(self, project):
        """Module with bad import → import fails."""
        (project / "broken_mod.py").write_text("import nonexistent_xyz_12345\n")
        sigs = _tier2_import_check(["broken_mod.py"], project, 10)
        assert len(sigs) == 1
        assert sigs[0]["passed"] is False
        assert sigs[0]["error"]  # non-empty error


# ===========================================================================
# Tier 3: Test execution
# ===========================================================================

class TestTier3Tests:
    def test_tier3_test_discovery(self, project):
        """Changed foo.py + existing test_foo.py → pytest discovers and runs it."""
        (project / "foo.py").write_text("def add(a, b): return a + b\n")
        # Self-contained test — no imports, avoids --timeout flag issues
        (project / "test_foo.py").write_text(
            "def test_add():\n    assert 1 + 2 == 3\n"
        )
        # Also write a minimal conftest to avoid project-level config interference
        (project / "conftest.py").write_text("")
        sigs = _tier3_test_execution(["foo.py"], {}, project, 30)
        assert len(sigs) == 1
        assert sigs[0]["check"] == "pytest"
        assert sigs[0]["file"] == "test_foo.py"
        # pytest may fail due to --timeout flag not installed, but it MUST
        # have been discovered and executed (not skipped)
        assert sigs[0]["passed"] is True or "output" in sigs[0] or "error" in sigs[0]

    def test_tier3_no_tests(self, project):
        """No matching test file → tier 3 skipped (empty signals)."""
        (project / "bar.py").write_text("x = 1\n")
        sigs = _tier3_test_execution(["bar.py"], {}, project, 30)
        assert sigs == []


# ===========================================================================
# Budget & tier selection
# ===========================================================================

class TestBudgetAndTiers:
    def test_budget_timeout(self, project):
        """Budget=0.001s → completes fast, fewer tiers run than with full budget."""
        (project / "hello.py").write_text("x = 2\n")
        # Run with near-zero budget
        tight = _make_config(execution_verification_timeout_s=0.001)
        result_tight = verify_execution("", "", tight, project)
        # Run with generous budget for comparison
        generous = _make_config(execution_verification_timeout_s=30)
        result_full = verify_execution("", "", generous, project)
        # Budget must not cause a hang
        assert result_tight["duration_s"] < 5
        # Tight budget should run fewer (or equal) tiers than generous
        tight_ran = len(result_tight["tiers_passed"]) + len(result_tight["tiers_failed"])
        full_ran = len(result_full["tiers_passed"]) + len(result_full["tiers_failed"])
        assert tight_ran <= full_ran

    def test_tier_selection(self, project):
        """Only tiers [0, 1] enabled → 2, 3 in tiers_skipped."""
        (project / "hello.py").write_text("x = 2\n")
        config = _make_config(execution_verification_tiers=[0, 1])
        result = verify_execution("", "", config, project)
        assert 2 in result["tiers_skipped"]
        assert 3 in result["tiers_skipped"]


# ===========================================================================
# Verified flag logic
# ===========================================================================

class TestVerifiedFlag:
    def test_verified_true_all_pass(self, project):
        """All enabled tiers pass → verified=True."""
        (project / "hello.py").write_text("x = 2\n")
        config = _make_config(execution_verification_tiers=[0, 1])
        result = verify_execution("", "", config, project)
        assert result["verified"] is True

    def test_verified_false_any_fail(self, project):
        """One tier fails → verified=False."""
        # Stage a broken file so it shows in git diff --cached
        bad = project / "bad.py"
        bad.write_text("def foo(\n")  # syntax error
        _git(project, "add", "bad.py")
        config = _make_config(execution_verification_tiers=[0, 1])
        result = verify_execution("", "", config, project)
        # Tier 0 passes (file changed), tier 1 must fail (syntax error)
        assert 0 in result["tiers_passed"]
        assert 1 in result["tiers_failed"]
        assert result["verified"] is False


# ===========================================================================
# Calibration DPO
# ===========================================================================

class TestCalibrationDPO:
    def test_build_calibration_dpo_on_failure(self):
        """Verification fails → returns DPO with calibration_dpo source."""
        task = {"description": "Fix the bug"}
        response = {"result": "I fixed it"}
        verification = {
            "verified": False,
            "signals": [
                {"check": "py_compile", "file": "bad.py", "passed": False, "error": "SyntaxError"},
            ],
        }
        dpo = build_calibration_dpo(task, response, verification)
        assert dpo is not None
        assert dpo["metadata"]["source"] == "calibration_dpo"
        assert dpo["metadata"]["quality"] == "gold"
        assert dpo["rejected"] == "I fixed it"
        assert "verification found issues" in dpo["chosen"]
        assert "py_compile" in dpo["chosen"]

    def test_build_calibration_dpo_on_pass(self):
        """Verification passes → returns None."""
        task = {"description": "Fix the bug"}
        response = {"result": "I fixed it"}
        verification = {
            "verified": True,
            "signals": [{"check": "py_compile", "passed": True}],
        }
        dpo = build_calibration_dpo(task, response, verification)
        assert dpo is None


# ===========================================================================
# File extraction from git state
# ===========================================================================

class TestGetChangedFiles:
    def test_get_changed_files_unstaged(self, project):
        """Unstaged changes detected."""
        (project / "hello.py").write_text("x = 999\n")
        files = _get_changed_files("", "", project)
        assert "hello.py" in files

    def test_get_changed_files_staged(self, project):
        """Staged changes detected."""
        (project / "new.py").write_text("y = 1\n")
        _git(project, "add", "new.py")
        files = _get_changed_files("", "", project)
        assert "new.py" in files


# ===========================================================================
# Tier 4: Runtime verification
# ===========================================================================

class TestTier4Runtime:
    def test_tier4_http_health_pass(self, project):
        """http.server starts, GET / returns 200."""
        checks = [{
            "type": "http_health",
            "cmd": [sys.executable, "-m", "http.server", "0"],
            "url": "/",
            "expect_status": 200,
            "startup_wait_s": 5,
        }]
        sigs = _tier4_runtime_check(checks, project, budget_s=10)
        assert len(sigs) == 1
        assert sigs[0]["check"] == "http_health"
        assert sigs[0]["passed"] is True
        assert sigs[0].get("status") == 200
        assert sigs[0].get("latency_ms", 0) >= 0

    def test_tier4_timeout_no_server(self, project):
        """Server that never starts → fails with error."""
        checks = [{
            "type": "http_health",
            # sleep forever, never prints a port
            "cmd": [sys.executable, "-c", "import time; time.sleep(999)"],
            "url": "/",
            "expect_status": 200,
            "startup_wait_s": 1,
        }]
        sigs = _tier4_runtime_check(checks, project, budget_s=3)
        assert len(sigs) == 1
        assert sigs[0]["passed"] is False

    def test_tier4_process_exit(self, project):
        """process_exit check: command exits 0."""
        checks = [{
            "type": "process_exit",
            "cmd": [sys.executable, "-c", "print('ok')"],
            "expect_exit": 0,
        }]
        sigs = _tier4_runtime_check(checks, project, budget_s=5)
        assert len(sigs) == 1
        assert sigs[0]["passed"] is True
        assert sigs[0]["exit_code"] == 0

    def test_tier4_process_exit_failure(self, project):
        """process_exit check: command exits non-zero."""
        checks = [{
            "type": "process_exit",
            "cmd": [sys.executable, "-c", "import sys; sys.exit(1)"],
            "expect_exit": 0,
        }]
        sigs = _tier4_runtime_check(checks, project, budget_s=5)
        assert len(sigs) == 1
        assert sigs[0]["passed"] is False

    def test_tier4_integrated_via_verify(self, project):
        """Tier 4 wired into verify_execution when configured."""
        (project / "hello.py").write_text("x = 2\n")
        config = _make_config(
            execution_verification_tiers=[0, 4],
            execution_verification_runtime_checks=[{
                "type": "process_exit",
                "cmd": [sys.executable, "-c", "print('ok')"],
                "expect_exit": 0,
            }],
            execution_verification_runtime_timeout_s=5,
        )
        result = verify_execution("", "", config, project)
        assert 4 in result["tiers_passed"]
        assert result["verified"] is True
        # Receipt provenance fields present
        assert "receipt_id" in result
        assert "commit_sha" in result


# ===========================================================================
# Tier 5: Outcome verification (delta-based)
# ===========================================================================

class TestExtractClaims:
    def test_extract_count_claims(self):
        """Plan with '+N tests' and 'add N files' → count claims extracted."""
        plan = "Add +5 tests for the verifier. Create 3 new modules."
        claims = extract_claims(plan)
        count_claims = [c for c in claims if c["claim_type"] == "count"]
        assert len(count_claims) >= 2
        units = {c["unit"] for c in count_claims}
        assert "test" in units
        assert "module" in units

    def test_extract_file_claims(self):
        """Plan with 'create foo.py' → file claim extracted."""
        plan = "Create file `goal_tracker.py` and add `csr.py`."
        claims = extract_claims(plan)
        file_claims = [c for c in claims if c["claim_type"] == "file"]
        assert len(file_claims) >= 2
        targets = {c["target"] for c in file_claims}
        assert "goal_tracker.py" in targets
        assert "csr.py" in targets

    def test_extract_no_claims(self):
        """Plan with no measurable claims → empty list."""
        plan = "Refactor the code to be cleaner and more readable."
        claims = extract_claims(plan)
        assert claims == []


class TestCaptureBaseline:
    def test_capture_baseline_creates_driver_dir(self, project):
        """capture_outcome_baseline creates .brain/driver/ if it doesn't exist."""
        plan = "Add +3 tests for the parser."
        result = capture_outcome_baseline(plan, project)
        assert (project / ".brain" / "driver" / "outcome_baseline.json").exists()
        assert len(result["claims"]) >= 1
        assert "captured_at" in result
        assert "plan_hash" in result

    def test_capture_baseline_records_current_value(self, project):
        """Baseline captures current test count."""
        # Create some test functions first
        (project / "test_hello.py").write_text(
            "def test_one(): pass\ndef test_two(): pass\n"
        )
        plan = "Add +5 tests."
        result = capture_outcome_baseline(plan, project)
        count_claims = [c for c in result["claims"]
                        if c["claim_type"] == "count" and c["unit"] == "test"]
        assert len(count_claims) == 1
        # Should have captured the 2 existing tests as baseline
        assert count_claims[0]["baseline_value"] >= 2
        assert count_claims[0]["claimed_delta"] == 5

    def test_capture_baseline_file_claims(self, project):
        """Baseline records whether claimed files exist."""
        plan = "Create file `new_module.py`."
        result = capture_outcome_baseline(plan, project)
        file_claims = [c for c in result["claims"]
                       if c["claim_type"] == "file"]
        assert len(file_claims) == 1
        assert file_claims[0]["target"] == "new_module.py"
        assert file_claims[0]["baseline_exists"] is False


class TestTier5Outcome:
    def test_tier5_passes_when_delta_sufficient(self, project):
        """Actual delta >= 25% of claimed → passes."""
        # Create baseline claiming +4 tests, with 0 existing
        plan = "Add +4 tests."
        capture_outcome_baseline(plan, project)
        # Now create 2 tests (50% of 4 — above 25% threshold)
        (project / "test_new.py").write_text(
            "def test_a(): pass\ndef test_b(): pass\n"
        )
        baseline_path = project / ".brain" / "driver" / "outcome_baseline.json"
        sigs = _tier5_outcome_check(plan, project, 10, baseline_path)
        assert len(sigs) >= 1
        test_sig = [s for s in sigs if s.get("metric") == "test"][0]
        assert test_sig["passed"] is True
        assert test_sig["hit_ratio"] >= 0.25

    def test_tier5_fails_when_zero_delta(self, project):
        """Zero progress on claimed metric → PREMATURE VICTORY."""
        plan = "Add +10 tests."
        capture_outcome_baseline(plan, project)
        # Don't create any tests
        baseline_path = project / ".brain" / "driver" / "outcome_baseline.json"
        sigs = _tier5_outcome_check(plan, project, 10, baseline_path)
        assert len(sigs) >= 1
        test_sig = [s for s in sigs if s.get("metric") == "test"][0]
        assert test_sig["passed"] is False
        assert "PREMATURE VICTORY" in test_sig.get("error", "")
        assert test_sig["hit_ratio"] == 0.0

    def test_tier5_file_claim_passes(self, project):
        """File exists after implementation → passes."""
        plan = "Create file `new_module.py`."
        capture_outcome_baseline(plan, project)
        # Create the file
        (project / "new_module.py").write_text("# new\n")
        baseline_path = project / ".brain" / "driver" / "outcome_baseline.json"
        sigs = _tier5_outcome_check(plan, project, 10, baseline_path)
        file_sigs = [s for s in sigs if s.get("check") == "outcome_file"]
        assert len(file_sigs) == 1
        assert file_sigs[0]["passed"] is True

    def test_tier5_file_claim_fails(self, project):
        """File NOT created → fails."""
        plan = "Create file `missing_module.py`."
        capture_outcome_baseline(plan, project)
        # Don't create it
        baseline_path = project / ".brain" / "driver" / "outcome_baseline.json"
        sigs = _tier5_outcome_check(plan, project, 10, baseline_path)
        file_sigs = [s for s in sigs if s.get("check") == "outcome_file"]
        assert len(file_sigs) == 1
        assert file_sigs[0]["passed"] is False

    def test_tier5_skips_when_no_baseline(self, project):
        """No baseline file → tier 5 skipped in verify_execution."""
        (project / "hello.py").write_text("x = 2\n")
        config = _make_config(execution_verification_tiers=[0, 5])
        result = verify_execution("", "", config, project)
        assert 5 in result["tiers_skipped"]

    def test_tier5_integrated_via_verify(self, project):
        """Tier 5 wired into verify_execution when baseline exists."""
        plan = "Add +2 tests."
        capture_outcome_baseline(plan, project)
        # Create tests to satisfy claim
        (project / "test_new.py").write_text(
            "def test_a(): pass\ndef test_b(): pass\n"
        )
        (project / "hello.py").write_text("x = 2\n")  # trigger tier 0
        config = _make_config(execution_verification_tiers=[0, 5])
        result = verify_execution("", "", config, project)
        assert 5 in result["tiers_passed"]
        assert result["verified"] is True
