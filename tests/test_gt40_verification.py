"""
Tests for GT40 independent verification system.

GT40 = script-level subprocess verification that runs AFTER Claude completes,
gating ACCEPT on real exit codes rather than Claude's self-reporting.
"""

import json
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp-server-nucleus" / "src"))

from scripts.third_brother_driver import (
    _parse_verification_commands,
    _run_verification_commands,
)


# ── Parser tests ─────────────────────────────────────────────


class TestParseVerificationCommands:
    """Test extraction of runnable commands from plan markdown."""

    def test_basic_backtick_commands(self):
        text = "1. `python3 -m pytest tests/test_foo.py -q`\n2. `cat .brain/csr.json`"
        cmds = _parse_verification_commands(text)
        assert len(cmds) == 2
        assert cmds[0]["command"] == "python3 -m pytest tests/test_foo.py -q"
        assert cmds[0]["skipped"] is False
        assert cmds[1]["command"] == "cat .brain/csr.json"

    def test_prose_lines_skipped(self):
        text = """1. Check the session transcript
2. Lokesh reviews everything before pasting
3. All character limits re-checked after edits"""
        cmds = _parse_verification_commands(text)
        assert len(cmds) == 0

    def test_recursion_guard_audit_plans(self):
        text = "1. `python3 scripts/third_brother_driver.py --audit-plans 1`"
        cmds = _parse_verification_commands(text)
        assert len(cmds) == 1
        assert cmds[0]["skipped"] is True
        assert cmds[0]["skip_reason"] == "recursion guard"

    def test_recursion_guard_sparring(self):
        text = "1. `python3 scripts/third_brother_driver.py --sparring 3`"
        cmds = _parse_verification_commands(text)
        assert len(cmds) == 1
        assert cmds[0]["skipped"] is True

    def test_recursion_guard_compound(self):
        text = "1. `python3 scripts/third_brother_driver.py --compound-audit 1`"
        cmds = _parse_verification_commands(text)
        assert len(cmds) == 1
        assert cmds[0]["skipped"] is True

    def test_mixed_runnable_and_skipped(self):
        text = """1. `python3 -c "print('hello')"`
2. Run `python3 scripts/third_brother_driver.py --sparring 3`
3. `cat .brain/flywheel/csr.json`
4. Check the session transcript"""
        cmds = _parse_verification_commands(text)
        assert len(cmds) == 3  # prose line excluded
        assert cmds[0]["skipped"] is False
        assert cmds[1]["skipped"] is True  # recursion guard
        assert cmds[2]["skipped"] is False

    def test_non_shell_backticks_skipped(self):
        """Backtick content that isn't a shell command should be skipped."""
        text = "1. `ratio < 1.0`, `claims_unsurvived > 0`"
        cmds = _parse_verification_commands(text)
        assert len(cmds) == 0

    def test_empty_input(self):
        assert _parse_verification_commands("") == []
        assert _parse_verification_commands("   \n\n  ") == []

    def test_pipe_commands_preserved(self):
        text = '1. `cat .brain/tasks.json | python3 -c "import sys,json; print(json.load(sys.stdin))"`'
        cmds = _parse_verification_commands(text)
        assert len(cmds) == 1
        assert "|" in cmds[0]["command"]

    def test_numbered_with_description_after(self):
        """Commands followed by → expected output."""
        text = "1. `python3 -m pytest tests/ -q` → 21 passed"
        cmds = _parse_verification_commands(text)
        assert len(cmds) == 1
        assert cmds[0]["command"] == "python3 -m pytest tests/ -q"

    def test_bullet_format(self):
        text = "- `pytest tests/test_app.py -x` passes\n- `pytest tests/test_compliance.py -v`"
        cmds = _parse_verification_commands(text)
        assert len(cmds) == 2

    def test_short_backtick_content_skipped(self):
        """Commands shorter than 3 chars are skipped."""
        text = "1. `ls`"  # exactly 2 chars — skipped by len check
        cmds = _parse_verification_commands(text)
        assert len(cmds) == 0


# ── Runner tests ─────────────────────────────────────────────


class TestRunVerificationCommands:
    """Test subprocess execution of verification commands."""

    def test_passing_command(self):
        result = _run_verification_commands('1. `python3 -c "print(42)"`')
        assert result["passed"] is True
        assert result["passed_count"] == 1
        assert result["failed_count"] == 0
        assert result["results"][0]["exit_code"] == 0

    def test_failing_command(self):
        result = _run_verification_commands('1. `python3 -c "assert False"`')
        assert result["passed"] is False
        assert result["failed_count"] == 1
        assert result["results"][0]["exit_code"] == 1
        assert "assert" in result["results"][0]["stderr"].lower()

    def test_mixed_pass_fail(self):
        text = '1. `python3 -c "print(1)"`\n2. `python3 -c "raise SystemExit(1)"`'
        result = _run_verification_commands(text)
        assert result["passed"] is False
        assert result["passed_count"] == 1
        assert result["failed_count"] == 1

    def test_skipped_commands_dont_block(self):
        """Skipped commands (recursion guard) should not cause failure."""
        text = '1. `python3 scripts/third_brother_driver.py --sparring 1`'
        result = _run_verification_commands(text)
        assert result["passed"] is True  # no failures, only skips
        assert result["skipped_count"] == 1
        assert result["failed_count"] == 0

    def test_no_parseable_commands(self):
        result = _run_verification_commands("Just some prose, no commands")
        assert result["passed"] is True
        assert result["total"] == 0
        assert "no parseable" in result.get("note", "")

    def test_timeout_per_command(self):
        # 1-second timeout on a 5-second sleep → should fail
        result = _run_verification_commands(
            '1. `python3 -c "import time; time.sleep(5)"`',
            timeout_per_cmd=1)
        assert result["passed"] is False
        assert result["results"][0]["passed"] is False
        assert "timed out" in result["results"][0].get("stderr", "").lower()

    def test_stdout_captured(self):
        result = _run_verification_commands('1. `python3 -c "print(12345)"`')
        assert "12345" in result["results"][0]["stdout"]

    def test_duration_tracked(self):
        result = _run_verification_commands('1. `python3 -c "print(1)"`')
        assert result["duration_s"] >= 0
        assert result["results"][0]["duration_s"] >= 0

    def test_all_skipped_is_pass(self):
        """If all commands are recursion-guarded, result is PASS (nothing failed)."""
        text = """1. `python3 scripts/third_brother_driver.py --audit-plans 1`
2. `python3 scripts/third_brother_driver.py --compound-audit 1`"""
        result = _run_verification_commands(text)
        assert result["passed"] is True
        assert result["skipped_count"] == 2
        assert result["passed_count"] == 0
        assert result["failed_count"] == 0
