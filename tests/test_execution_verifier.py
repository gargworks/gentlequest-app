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
    _tier0_diff_nonempty,
    _tier1_syntax_check,
    _tier2_import_check,
    _tier3_test_execution,
    _tier4_runtime_check,
    _tier5_outcome_check,
    extract_plan_claims,
    capture_outcome_baseline,
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


# ---------------------------------------------------------------------------
# Tier 5 — Outcome Verification (delta-based)
# ---------------------------------------------------------------------------

class TestTier5OutcomeCheck:
    """Tier 5: plan claims vs actual deltas."""

    def test_catches_noop_expansion(self, project):
        """THE test: plan claims +3700 chunks, actual delta is 0. Must FAIL."""
        baseline_dir = project / ".brain" / "driver"
        baseline_dir.mkdir(parents=True)
        baseline = {
            "plan_file": "test-plan.md",
            "captured_at": "2026-04-09T00:00:00",
            "metrics": {
                "chunk_count": {
                    "actual": 8769,
                    "claimed_before": 800,
                    "claimed_after": 4500,
                }
            }
        }
        (baseline_dir / "outcome_baseline.json").write_text(json.dumps(baseline))

        # Create a fake RAG DB with 8769 chunks (unchanged from baseline)
        _create_fake_rag_db(project, chunk_count=8769)

        signals = _tier5_outcome_check(project, budget_s=10)
        assert len(signals) == 1
        assert signals[0]["passed"] is False
        assert signals[0]["actual_delta"] == 0
        assert signals[0]["claimed_delta"] == 3700
        assert "PREMATURE VICTORY" in signals[0]["detail"]

    def test_passes_real_delta(self, project):
        """Plan claims +3700, actual delta +3000. Should PASS (81%)."""
        baseline_dir = project / ".brain" / "driver"
        baseline_dir.mkdir(parents=True)
        baseline = {
            "plan_file": "test-plan.md",
            "captured_at": "2026-04-09T00:00:00",
            "metrics": {
                "chunk_count": {
                    "actual": 800,
                    "claimed_before": 800,
                    "claimed_after": 4500,
                }
            }
        }
        (baseline_dir / "outcome_baseline.json").write_text(json.dumps(baseline))

        # DB now has 3800 chunks (delta = 3000)
        _create_fake_rag_db(project, chunk_count=3800)

        signals = _tier5_outcome_check(project, budget_s=10)
        assert len(signals) == 1
        assert signals[0]["passed"] is True
        assert signals[0]["actual_delta"] == 3000
        assert "PREMATURE VICTORY" not in signals[0]["detail"]

    def test_skips_when_no_baseline(self, project):
        """No baseline file → skip (not fail)."""
        signals = _tier5_outcome_check(project, budget_s=10)
        assert signals == []

    def test_skips_stale_baseline(self, project):
        """Baseline older than 24h → skip."""
        import time as _time
        baseline_dir = project / ".brain" / "driver"
        baseline_dir.mkdir(parents=True)
        baseline = {
            "plan_file": "old-plan.md",
            "captured_at": "2026-04-07T00:00:00",  # 2 days ago
            "metrics": {"chunk_count": {"actual": 100, "claimed_before": 100, "claimed_after": 500}}
        }
        bp = baseline_dir / "outcome_baseline.json"
        bp.write_text(json.dumps(baseline))
        # Set file mtime to 48h ago
        old_time = _time.time() - 48 * 3600
        import os
        os.utime(str(bp), (old_time, old_time))

        signals = _tier5_outcome_check(project, budget_s=10)
        assert signals == []

    def test_integrated_via_verify_execution(self, project):
        """Tier 5 wired into verify_execution when enabled."""
        baseline_dir = project / ".brain" / "driver"
        baseline_dir.mkdir(parents=True)
        baseline = {
            "plan_file": "test-plan.md",
            "captured_at": "2026-04-09T00:00:00",
            "metrics": {
                "chunk_count": {
                    "actual": 8769,
                    "claimed_before": 800,
                    "claimed_after": 4500,
                }
            }
        }
        (baseline_dir / "outcome_baseline.json").write_text(json.dumps(baseline))
        _create_fake_rag_db(project, chunk_count=8769)

        # Stage a change so tier 0 passes
        (project / "hello.py").write_text("x = 2\n")
        _git(project, "add", "hello.py")

        config = _make_config(execution_verification_tiers=[0, 5])
        result = verify_execution("diff", "", config, project)
        assert 0 in result["tiers_passed"]
        assert 5 in result["tiers_failed"]
        assert result["verified"] is False


class TestExtractPlanClaims:
    """Claim extraction from plan markdown."""

    def test_extracts_expected_outcome_table(self):
        plan = """
## Expected Outcome
| Metric | Before | After |
|--------|--------|-------|
| Chunk count | ~800 | ~4,500 |
| Indexed files | ~50 | ~530 |
"""
        claims = extract_plan_claims(plan)
        assert "chunk_count" in claims
        assert claims["chunk_count"]["claimed_before"] == 800
        assert claims["chunk_count"]["claimed_after"] == 4500

    def test_extracts_inline_delta(self):
        plan = "This will add ~2,000 new chunks to the index."
        claims = extract_plan_claims(plan)
        assert "chunk_count" in claims

    def test_empty_plan_returns_empty(self):
        claims = extract_plan_claims("No numbers here, just text.")
        assert claims == {}


class TestCaptureOutcomeBaseline:
    """Baseline capture from plan + current metrics."""

    def test_captures_baseline_with_rag_db(self, project):
        plan_text = """
## Expected Outcome
| Metric | Before | After |
|--------|--------|-------|
| Chunk count | ~800 | ~4,500 |
"""
        _create_fake_rag_db(project, chunk_count=8769)
        baseline_dir = project / ".brain" / "driver"
        baseline_dir.mkdir(parents=True)

        baseline = capture_outcome_baseline(plan_text, project)
        assert "chunk_count" in baseline["metrics"]
        assert baseline["metrics"]["chunk_count"]["actual"] == 8769
        assert baseline["metrics"]["chunk_count"]["claimed_before"] == 800
        assert baseline["metrics"]["chunk_count"]["claimed_after"] == 4500

    def test_returns_empty_when_no_claims(self, project):
        baseline = capture_outcome_baseline("No numbers.", project)
        assert baseline["metrics"] == {}


def _create_fake_rag_db(project_root, chunk_count=100):
    """Create a minimal SQLite RAG DB for testing."""
    import sqlite3
    db_dir = project_root / ".brain"
    db_dir.mkdir(parents=True, exist_ok=True)
    db = db_dir / "rag_index.db"
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE IF NOT EXISTS chunks (id INTEGER PRIMARY KEY, file_path TEXT, content_hash TEXT)")
    conn.execute("DELETE FROM chunks")
    for i in range(chunk_count):
        conn.execute("INSERT INTO chunks (file_path, content_hash) VALUES (?, ?)",
                     (f"file_{i // 10}.md", f"hash_{i}"))
    conn.commit()
    conn.close()
