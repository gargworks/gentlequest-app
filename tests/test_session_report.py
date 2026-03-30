"""Tests for generate_session_report in third_brother_driver.py"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
import third_brother_driver as drv


@pytest.fixture
def driver_dir(tmp_path, monkeypatch):
    """Set up a temp driver directory with the expected file structure."""
    monkeypatch.setattr(drv, "DRIVER_DIR", tmp_path)
    monkeypatch.setattr(drv, "RUNS_PATH", tmp_path / "runs.jsonl")
    monkeypatch.setattr(drv, "SHADOW_LOG_PATH", tmp_path / "shadow_log.jsonl")
    return tmp_path


def _write_runs(path, runs):
    with open(path, "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")


def _write_shadow(path, entries):
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


class TestGenerateSessionReport:
    def test_creates_report_file(self, driver_dir):
        today = datetime.now().strftime("%Y-%m-%d")
        _write_runs(driver_dir / "runs.jsonl", [
            {"ts": f"{today}T10:00:00", "task_id": "t-1", "task_title": "Task A",
             "outcome": "completed", "turns": 5, "duration_seconds": 60, "driver_version": "v2"},
        ])
        _write_shadow(driver_dir / "shadow_log.jsonl", [
            {"ts": f"{today}T10:00:00", "task_id": "t-1"},
        ])
        drv.generate_session_report("sess-abc-123")
        reports = list((driver_dir / "session_reports").glob("*.md"))
        assert len(reports) == 1
        assert "sess-abc-123" in reports[0].name

    def test_report_content(self, driver_dir):
        today = datetime.now().strftime("%Y-%m-%d")
        _write_runs(driver_dir / "runs.jsonl", [
            {"ts": f"{today}T10:00:00", "task_id": "t-1", "task_title": "Task A",
             "outcome": "completed", "turns": 5, "duration_seconds": 60, "driver_version": "v2"},
            {"ts": f"{today}T10:05:00", "task_id": "t-2", "task_title": "Task B",
             "outcome": "timeout", "turns": 30, "duration_seconds": 300, "driver_version": "v2"},
        ])
        _write_shadow(driver_dir / "shadow_log.jsonl", [
            {"ts": f"{today}T10:00:00"},
            {"ts": f"{today}T10:05:00"},
        ])
        drv.generate_session_report("sess-xyz")
        report = next((driver_dir / "session_reports").glob("*.md")).read_text()

        assert "**Tasks attempted:** 2" in report
        assert "**Total duration:** 360s" in report
        assert "**Total turns:** 35" in report
        assert "completed: 1" in report
        assert "timeout: 1" in report
        assert "Task A" in report
        assert "Task B" in report
        assert "shadow_log entries added today:** 2" in report

    def test_no_runs_skips_report(self, driver_dir):
        """No runs today → no report file created."""
        _write_runs(driver_dir / "runs.jsonl", [
            {"ts": "2020-01-01T10:00:00", "task_id": "t-old", "task_title": "Old",
             "outcome": "completed", "turns": 1, "duration_seconds": 10, "driver_version": "v2"},
        ])
        drv.generate_session_report("sess-noop")
        reports_dir = driver_dir / "session_reports"
        assert not reports_dir.exists() or len(list(reports_dir.glob("*.md"))) == 0

    def test_filters_v2_only(self, driver_dir):
        """Only v2 runs should be included."""
        today = datetime.now().strftime("%Y-%m-%d")
        _write_runs(driver_dir / "runs.jsonl", [
            {"ts": f"{today}T10:00:00", "task_id": "t-v1", "task_title": "V1 task",
             "outcome": "completed", "turns": 1, "duration_seconds": 10},
            {"ts": f"{today}T10:01:00", "task_id": "t-v2", "task_title": "V2 task",
             "outcome": "completed", "turns": 5, "duration_seconds": 50, "driver_version": "v2"},
        ])
        drv.generate_session_report("sess-filter")
        report = next((driver_dir / "session_reports").glob("*.md")).read_text()
        assert "**Tasks attempted:** 1" in report
        assert "V2 task" in report
        assert "V1 task" not in report

    def test_empty_session_id(self, driver_dir):
        """Works with empty session_id."""
        today = datetime.now().strftime("%Y-%m-%d")
        _write_runs(driver_dir / "runs.jsonl", [
            {"ts": f"{today}T10:00:00", "task_id": "t-1", "task_title": "Task A",
             "outcome": "completed", "turns": 3, "duration_seconds": 30, "driver_version": "v2"},
        ])
        drv.generate_session_report("")
        reports = list((driver_dir / "session_reports").glob("*.md"))
        assert len(reports) == 1
        report = reports[0].read_text()
        assert "**Session ID:** N/A" in report

    def test_malformed_jsonl_lines_skipped(self, driver_dir):
        """Gracefully skips bad JSON lines."""
        today = datetime.now().strftime("%Y-%m-%d")
        with open(driver_dir / "runs.jsonl", "w") as f:
            f.write("not json\n")
            f.write(json.dumps({
                "ts": f"{today}T10:00:00", "task_id": "t-1", "task_title": "OK",
                "outcome": "completed", "turns": 1, "duration_seconds": 10, "driver_version": "v2",
            }) + "\n")
        with open(driver_dir / "shadow_log.jsonl", "w") as f:
            f.write("{bad\n")
            f.write(json.dumps({"ts": f"{today}T10:00:00"}) + "\n")

        drv.generate_session_report("sess-bad-lines")
        report = next((driver_dir / "session_reports").glob("*.md")).read_text()
        assert "**Tasks attempted:** 1" in report
        assert "shadow_log entries added today:** 1" in report

    def test_no_shadow_log_file(self, driver_dir):
        """Report still generates when shadow_log.jsonl is missing."""
        today = datetime.now().strftime("%Y-%m-%d")
        _write_runs(driver_dir / "runs.jsonl", [
            {"ts": f"{today}T10:00:00", "task_id": "t-1", "task_title": "Solo",
             "outcome": "completed", "turns": 2, "duration_seconds": 20, "driver_version": "v2"},
        ])
        # Don't create shadow_log.jsonl
        drv.generate_session_report("sess-no-shadow")
        report = next((driver_dir / "session_reports").glob("*.md")).read_text()
        assert "shadow_log entries added today:** 0" in report
