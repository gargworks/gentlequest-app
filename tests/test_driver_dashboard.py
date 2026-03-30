"""
Tests for scripts/driver_dashboard.py

Covers: load_json, load_jsonl, render() sections, empty state, completion rate.
"""

import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import driver_dashboard as dash


# ── Fixtures ──────────────────────────────────────────────


@pytest.fixture
def driver_dir(tmp_path):
    """Populate a temp driver dir with realistic fixture data."""
    d = tmp_path / ".brain" / "driver"
    d.mkdir(parents=True)

    (d / "state.json").write_text(json.dumps({
        "phase": "executing",
        "task_id": "task-042",
        "session_id": "sess-abc123def456ghij7890"
    }))

    (d / "config.json").write_text(json.dumps({
        "trust_ladder": {"current_phase": 2},
        "claude_effort": "max",
        "claude_max_turns": 30
    }))

    (d / "tasks.json").write_text(json.dumps({
        "tasks": [
            {"id": "t1", "status": "completed"},
            {"id": "t2", "status": "completed"},
            {"id": "t3", "status": "in_progress"},
            {"id": "t4", "status": "committed"},
            {"id": "t5", "status": "blocked"},
        ]
    }))

    runs = [
        {"ts": "2026-03-23T10:00:00Z", "task_id": "t1", "outcome": "completed", "duration_seconds": 120, "turns": 5},
        {"ts": "2026-03-23T10:05:00Z", "task_id": "t2", "outcome": "error", "duration_seconds": 30, "turns": 2},
        {"ts": "2026-03-23T10:10:00Z", "task_id": "t3", "outcome": "completed", "duration_seconds": 90, "turns": 4},
        {"ts": "2026-03-23T10:15:00Z", "task_id": "t4", "outcome": "completed", "duration_seconds": 60, "turns": 3},
    ]
    (d / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in runs) + "\n")

    alerts = [
        {"ts": "2026-03-23T10:12:00Z", "rule": "token_limit", "severity": "warn", "detail": "Approaching 80% token budget"},
    ]
    (d / "alerts.jsonl").write_text("\n".join(json.dumps(a) for a in alerts) + "\n")

    return d


# ── load_json ─────────────────────────────────────────────


def test_load_json_missing_file(tmp_path):
    result = dash.load_json(tmp_path / "nonexistent.json")
    assert result == {}


def test_load_json_valid(tmp_path):
    p = tmp_path / "data.json"
    p.write_text(json.dumps({"key": "value"}))
    assert dash.load_json(p) == {"key": "value"}


def test_load_json_corrupt(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not valid json")
    assert dash.load_json(p) == {}


# ── load_jsonl ────────────────────────────────────────────


def test_load_jsonl_missing_file(tmp_path):
    assert dash.load_jsonl(tmp_path / "missing.jsonl") == []


def test_load_jsonl_respects_limit(tmp_path):
    p = tmp_path / "events.jsonl"
    lines = [json.dumps({"i": i}) for i in range(10)]
    p.write_text("\n".join(lines))
    result = dash.load_jsonl(p, limit=3)
    assert len(result) == 3
    # Should return the LAST 3 entries
    assert result[0]["i"] == 7
    assert result[2]["i"] == 9


def test_load_jsonl_skips_bad_lines(tmp_path):
    p = tmp_path / "mixed.jsonl"
    p.write_text('{"ok":1}\n{BAD\n{"ok":2}\n')
    result = dash.load_jsonl(p)
    assert len(result) == 2


# ── render() helpers ──────────────────────────────────────


FROZEN_NOW = datetime(2026, 3, 23, 12, 0, 0)


def _render_with_dir(target_dir, capsys):
    """Swap DRIVER_DIR, freeze datetime, call render(), return stdout."""
    orig = dash.DRIVER_DIR
    try:
        dash.DRIVER_DIR = target_dir
        with patch("driver_dashboard.datetime") as mock_dt:
            mock_dt.now.return_value = FROZEN_NOW
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            dash.render(clear=False)
    finally:
        dash.DRIVER_DIR = orig
    return capsys.readouterr().out


# ── render() sections ────────────────────────────────────


def test_render_sections(driver_dir, capsys):
    """render() output contains all expected section headers."""
    out = _render_with_dir(driver_dir, capsys)

    assert "TASK QUEUE" in out
    assert "RUN HISTORY" in out
    assert "TRUST LADDER" in out
    assert "ALERTS" in out


def test_render_state_values(driver_dir, capsys):
    """render() shows the state values from fixture data."""
    out = _render_with_dir(driver_dir, capsys)

    assert "executing" in out
    assert "task-042" in out
    assert "Phase 2" in out
    assert "auto-safe" in out


def test_render_alerts_shown(driver_dir, capsys):
    """render() displays alert details."""
    out = _render_with_dir(driver_dir, capsys)

    assert "token_limit" in out
    assert "warn" in out


# ── Empty state ───────────────────────────────────────────


def test_render_empty_state(tmp_path, capsys):
    """render() does not crash when all files are missing."""
    empty = tmp_path / "empty_driver"
    empty.mkdir()
    out = _render_with_dir(empty, capsys)

    assert "TASK QUEUE" in out
    assert "RUN HISTORY (0 total)" in out
    # No ALERTS section when none exist
    assert "ALERTS" not in out


# ── Completion rate ───────────────────────────────────────


def test_completion_rate(driver_dir, capsys):
    """Completion rate = completed / total * 100 -> 3/4 = 75%."""
    out = _render_with_dir(driver_dir, capsys)

    # Fixture: 4 runs, 3 completed -> 75%
    assert "(75%)" in out


def test_completion_rate_zero_runs(tmp_path, capsys):
    """Zero runs -> 0% completion, no division error."""
    empty = tmp_path / "no_runs"
    empty.mkdir()
    out = _render_with_dir(empty, capsys)

    assert "(0%)" in out
