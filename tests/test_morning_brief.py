"""Tests for scripts/morning_brief.py — context gathering and prompt assembly."""

import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scripts.morning_brief as mb


@pytest.fixture
def brief_env(tmp_path):
    """Isolated environment with driver data files."""
    driver = tmp_path / ".brain" / "driver"
    driver.mkdir(parents=True)
    briefings = tmp_path / ".brain" / "briefings"

    # Patch module paths
    orig = {
        "BRAIN_PATH": mb.BRAIN_PATH,
        "DRIVER_DIR": mb.DRIVER_DIR,
        "BRIEFINGS_DIR": mb.BRIEFINGS_DIR,
        "SHADOW_LOG": mb.SHADOW_LOG,
        "TASKS_PATH": mb.TASKS_PATH,
        "RUNS_PATH": mb.RUNS_PATH,
        "PROJECT_ROOT": mb.PROJECT_ROOT,
    }
    mb.DRIVER_DIR = driver
    mb.BRIEFINGS_DIR = briefings
    mb.SHADOW_LOG = driver / "shadow_log.jsonl"
    mb.TASKS_PATH = driver / "tasks.json"
    mb.RUNS_PATH = driver / "runs.jsonl"

    yield {"tmp": tmp_path, "driver": driver, "briefings": briefings}

    for k, v in orig.items():
        setattr(mb, k, v)


class TestGatherShadowLog:
    def test_parses_entries(self, brief_env):
        log = brief_env["driver"] / "shadow_log.jsonl"
        log.write_text(
            json.dumps({"task_title": "Fix bug", "outcome": "completed",
                         "latency_ms": 120000, "total_turns": 10}) + "\n"
            + json.dumps({"task_title": "Add test", "outcome": "blocked",
                           "latency_ms": 60000, "total_turns": 5}) + "\n"
        )

        result = mb.gather_shadow_log(n=10)
        assert "Fix bug" in result
        assert "completed" in result
        assert "blocked" in result

    def test_missing_file(self, brief_env):
        result = mb.gather_shadow_log()
        assert "no shadow_log" in result

    def test_limits_to_n(self, brief_env):
        log = brief_env["driver"] / "shadow_log.jsonl"
        lines = [json.dumps({"task_title": f"Task {i}", "outcome": "completed",
                              "latency_ms": 1000, "total_turns": 1})
                 for i in range(20)]
        log.write_text("\n".join(lines) + "\n")

        result = mb.gather_shadow_log(n=3)
        assert "Task 17" in result
        assert "Task 10" not in result


class TestGatherPendingTasks:
    def test_filters_pending(self, brief_env):
        tasks = {
            "tasks": [
                {"id": "t1", "title": "Done", "status": "completed", "priority": 1},
                {"id": "t2", "title": "Pending", "status": "committed", "priority": 2},
                {"id": "t3", "title": "Blocked", "status": "blocked", "priority": 1,
                 "failure_reason": "timeout"},
            ]
        }
        mb.TASKS_PATH.write_text(json.dumps(tasks))

        result = mb.gather_pending_tasks()
        assert "Pending" in result
        assert "Blocked" in result
        assert "Done" not in result
        assert "timeout" in result

    def test_missing_file(self, brief_env):
        result = mb.gather_pending_tasks()
        assert "no tasks.json" in result

    def test_no_pending(self, brief_env):
        tasks = {"tasks": [{"id": "t1", "title": "Done", "status": "completed"}]}
        mb.TASKS_PATH.write_text(json.dumps(tasks))

        result = mb.gather_pending_tasks()
        assert "no pending" in result


class TestGatherRecentRuns:
    def test_parses_runs(self, brief_env):
        runs = brief_env["driver"] / "runs.jsonl"
        runs.write_text(
            json.dumps({"task_title": "Test A", "outcome": "completed",
                         "duration_seconds": 60, "turns": 10, "retry_count": 0}) + "\n"
            + json.dumps({"task_title": "Test B", "outcome": "timeout",
                           "duration_seconds": 120, "turns": 5, "retry_count": 2}) + "\n"
        )

        result = mb.gather_recent_runs()
        assert "Test A" in result
        assert "Test B" in result
        assert "2 retries" in result

    def test_missing_file(self, brief_env):
        result = mb.gather_recent_runs()
        assert "no runs.jsonl" in result


class TestBuildContext:
    def test_assembles_all_sections(self, brief_env):
        # Write minimal data
        mb.SHADOW_LOG.write_text(
            json.dumps({"task_title": "X", "outcome": "completed",
                         "latency_ms": 1000, "total_turns": 1}) + "\n")
        mb.TASKS_PATH.write_text(json.dumps({"tasks": [
            {"id": "t1", "title": "Y", "status": "committed", "priority": 1}
        ]}))
        mb.RUNS_PATH.write_text(
            json.dumps({"task_title": "Z", "outcome": "completed",
                         "duration_seconds": 30, "turns": 5}) + "\n")

        with patch.object(mb, "gather_git_log", return_value="abc123 feat: something"):
            ctx = mb.build_context(since="2026-03-22")

        assert "Git log" in ctx
        assert "Shadow log" in ctx
        assert "Pending tasks" in ctx
        assert "Recent driver runs" in ctx
        assert "Priorities for today" in ctx


class TestMondayLookback:
    """Monday briefings should look back to Friday (3 days) not Sunday (1 day)."""

    def test_monday_lookback_3_days(self, brief_env):
        """On Monday 2026-03-30, since should be Friday 2026-03-27."""
        with patch.object(mb, "run_claude", return_value="mock brief"), \
             patch.object(mb, "gather_git_log") as mock_git:
            mock_git.return_value = "(no commits)"
            # Simulate --date=2026-03-30 (a Monday)
            with patch("sys.argv", ["morning_brief.py", "--date", "2026-03-30", "--dry-run"]):
                mb.main()
            mock_git.assert_called_once_with("2026-03-27")

    def test_tuesday_lookback_1_day(self, brief_env):
        """On Tuesday 2026-03-31, since should be Monday 2026-03-30."""
        with patch.object(mb, "run_claude", return_value="mock brief"), \
             patch.object(mb, "gather_git_log") as mock_git:
            mock_git.return_value = "(no commits)"
            with patch("sys.argv", ["morning_brief.py", "--date", "2026-03-31", "--dry-run"]):
                mb.main()
            mock_git.assert_called_once_with("2026-03-30")

    def test_friday_lookback_1_day(self, brief_env):
        """On Friday 2026-03-27, since should be Thursday 2026-03-26."""
        with patch.object(mb, "run_claude", return_value="mock brief"), \
             patch.object(mb, "gather_git_log") as mock_git:
            mock_git.return_value = "(no commits)"
            with patch("sys.argv", ["morning_brief.py", "--date", "2026-03-27", "--dry-run"]):
                mb.main()
            mock_git.assert_called_once_with("2026-03-26")


class TestSaveBriefing:
    def test_creates_file(self, brief_env):
        path = mb.save_briefing("Test content", "2026-03-23")
        assert path.exists()
        text = path.read_text()
        assert "Morning Brief" in text
        assert "Test content" in text
        assert "2026-03-23" in text

    def test_creates_directory(self, brief_env):
        # briefings dir doesn't exist yet
        assert not mb.BRIEFINGS_DIR.exists()
        mb.save_briefing("x", "2026-03-23")
        assert mb.BRIEFINGS_DIR.exists()
