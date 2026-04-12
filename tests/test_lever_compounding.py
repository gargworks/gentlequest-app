"""Tests for the lever → Phase D compounding loop.

Proves that lever observations written to .brain/ledger/events.jsonl
actually affect TB's Phase D review scoring — i.e. the ledger is a
*hot* substrate, not just a log file.

If this contract holds, any future lever (#15 ruff_chain plus the other
~30 from the 71-item blitz) automatically compounds the moment it writes
a `lever.<name>.observation outcome=found` event.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.third_brother_driver import (
    _find_lever_findings_in_diff,
    _spawn_lever_fix_task,
)


DIFF_WITH_DRIVER = (
    "diff --git a/scripts/third_brother_driver.py b/scripts/third_brother_driver.py\n"
    "index abc..def 100644\n"
    "--- a/scripts/third_brother_driver.py\n"
    "+++ b/scripts/third_brother_driver.py\n"
    "@@ -42,1 +42,2 @@\n"
    "+from driver_config import X\n"
)

DIFF_UNRELATED = (
    "diff --git a/README.md b/README.md\n"
    "index abc..def 100644\n"
    "--- a/README.md\n"
    "+++ b/README.md\n"
    "@@ -1,1 +1,1 @@\n"
    "+hello\n"
)


def _write_ledger(path: Path, events: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n")


class TestFindLeverFindingsInDiff:
    def test_empty_diff_returns_empty(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        _write_ledger(ledger, [{
            "type": "lever.ruff_chain.observation",
            "outcome": "found",
            "detail": {"findings": ["scripts/third_brother_driver.py:42:1: E402"]},
        }])
        assert _find_lever_findings_in_diff("", ledger_path=ledger) == []

    def test_missing_ledger_returns_empty(self, tmp_path):
        assert _find_lever_findings_in_diff(
            DIFF_WITH_DRIVER, ledger_path=tmp_path / "nope.jsonl"
        ) == []

    def test_clean_outcome_does_not_match(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        _write_ledger(ledger, [{
            "type": "lever.ruff_chain.observation",
            "outcome": "clean",
            "detail": {"files_checked": 1},
        }])
        assert _find_lever_findings_in_diff(DIFF_WITH_DRIVER, ledger_path=ledger) == []

    def test_non_lever_events_ignored(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        _write_ledger(ledger, [{
            "type": "phase.failure",
            "outcome": "found",
            "detail": {"findings": ["scripts/third_brother_driver.py:42 error"]},
        }])
        assert _find_lever_findings_in_diff(DIFF_WITH_DRIVER, ledger_path=ledger) == []

    def test_found_but_different_file_does_not_match(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        _write_ledger(ledger, [{
            "type": "lever.ruff_chain.observation",
            "outcome": "found",
            "detail": {"findings": ["some_other_file.py:10:1: E402"]},
        }])
        assert _find_lever_findings_in_diff(DIFF_WITH_DRIVER, ledger_path=ledger) == []

    def test_found_on_diff_file_matches(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        _write_ledger(ledger, [{
            "type": "lever.ruff_chain.observation",
            "outcome": "found",
            "detail": {"findings": ["scripts/third_brother_driver.py:42:1: E402"]},
        }])
        matches = _find_lever_findings_in_diff(DIFF_WITH_DRIVER, ledger_path=ledger)
        assert len(matches) == 1
        assert matches[0]["type"] == "lever.ruff_chain.observation"

    def test_malformed_json_lines_skipped(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        valid = json.dumps({
            "type": "lever.ruff_chain.observation",
            "outcome": "found",
            "detail": {"findings": ["scripts/third_brother_driver.py:42 E402"]},
        })
        ledger.write_text(f"{{malformed\nnot-json\n{valid}\n")
        matches = _find_lever_findings_in_diff(DIFF_WITH_DRIVER, ledger_path=ledger)
        assert len(matches) == 1

    def test_window_limits_lookback(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        old_match = {
            "type": "lever.ruff_chain.observation",
            "outcome": "found",
            "detail": {"findings": ["scripts/third_brother_driver.py:42 E402"]},
        }
        noise = {"type": "phase.noise", "outcome": "clean", "detail": {}}
        # Put the match at index 0, then 50 noise entries after.
        events = [old_match] + [noise] * 50
        _write_ledger(ledger, events)
        # With a small window, the old match falls outside the lookback.
        matches = _find_lever_findings_in_diff(
            DIFF_WITH_DRIVER, ledger_path=ledger, window=10
        )
        assert matches == []
        # With a big window, it's visible again.
        matches = _find_lever_findings_in_diff(
            DIFF_WITH_DRIVER, ledger_path=ledger, window=100
        )
        assert len(matches) == 1

    def test_unrelated_diff_does_not_match(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        _write_ledger(ledger, [{
            "type": "lever.ruff_chain.observation",
            "outcome": "found",
            "detail": {"findings": ["scripts/third_brother_driver.py:42 E402"]},
        }])
        # README.md diff should not match a driver.py finding.
        assert _find_lever_findings_in_diff(
            DIFF_UNRELATED, ledger_path=ledger
        ) == []

    def test_multiple_levers_all_returned(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        _write_ledger(ledger, [
            {
                "type": "lever.ruff_chain.observation",
                "outcome": "found",
                "lever": "ruff_chain",
                "detail": {"findings": ["scripts/third_brother_driver.py:42 E402"]},
            },
            {
                "type": "lever.mypy_chain.observation",
                "outcome": "found",
                "lever": "mypy_chain",
                "detail": {"findings": ["scripts/third_brother_driver.py:99 type error"]},
            },
        ])
        matches = _find_lever_findings_in_diff(DIFF_WITH_DRIVER, ledger_path=ledger)
        assert len(matches) == 2
        levers = {m.get("lever") for m in matches}
        assert levers == {"ruff_chain", "mypy_chain"}


class TestSpawnLeverFixTask:
    def _match(self, lever="ruff_chain", finding="scripts/third_brother_driver.py:42:1: E402"):
        return {
            "type": f"lever.{lever}.observation",
            "outcome": "found",
            "lever": lever,
            "detail": {"findings": [finding]},
        }

    def test_creates_task_with_lever_gate_source(self, tmp_path):
        tasks_path = tmp_path / "tasks.json"
        parent = {"id": "t-100", "scope": ["scripts/**"]}
        new_id = _spawn_lever_fix_task(
            parent, [self._match()], tasks_path=tasks_path
        )
        assert new_id is not None
        assert new_id.startswith("lever-fix-ruff_chain-")
        data = json.loads(tasks_path.read_text())
        created = [t for t in data["tasks"] if t["id"] == new_id]
        assert len(created) == 1
        assert created[0]["source"] == "lever_gate"
        assert created[0]["status"] == "pending"
        assert created[0]["priority"] == "high"
        assert created[0]["lever_gate_parent_task_id"] == "t-100"
        assert created[0]["scope"] == ["scripts/third_brother_driver.py"]

    def test_dedupes_same_finding_set(self, tmp_path):
        tasks_path = tmp_path / "tasks.json"
        parent = {"id": "t-200", "scope": ["scripts/**"]}
        match = self._match()
        first = _spawn_lever_fix_task(parent, [match], tasks_path=tasks_path)
        second = _spawn_lever_fix_task(parent, [match], tasks_path=tasks_path)
        assert first == second
        data = json.loads(tasks_path.read_text())
        lever_tasks = [t for t in data["tasks"] if t.get("source") == "lever_gate"]
        assert len(lever_tasks) == 1

    def test_new_task_when_finding_set_differs(self, tmp_path):
        tasks_path = tmp_path / "tasks.json"
        parent = {"id": "t-300", "scope": ["scripts/**"]}
        first = _spawn_lever_fix_task(
            parent,
            [self._match(finding="scripts/third_brother_driver.py:42:1: E402")],
            tasks_path=tasks_path,
        )
        second = _spawn_lever_fix_task(
            parent,
            [self._match(finding="scripts/other_file.py:10:1: F401")],
            tasks_path=tasks_path,
        )
        assert first != second
        data = json.loads(tasks_path.read_text())
        lever_tasks = [t for t in data["tasks"] if t.get("source") == "lever_gate"]
        assert len(lever_tasks) == 2

    def test_creates_tasks_json_if_missing(self, tmp_path):
        tasks_path = tmp_path / "nested" / "tasks.json"
        tasks_path.parent.mkdir()
        parent = {"id": "t-400"}
        new_id = _spawn_lever_fix_task(
            parent, [self._match()], tasks_path=tasks_path
        )
        assert new_id is not None
        assert tasks_path.exists()
        data = json.loads(tasks_path.read_text())
        assert len(data["tasks"]) == 1

    def test_completed_dedup_task_allows_new_spawn(self, tmp_path):
        """If the prior lever-fix task is completed, a new one should spawn
        because the finding re-surfaced despite being 'fixed'."""
        tasks_path = tmp_path / "tasks.json"
        parent = {"id": "t-500"}
        first = _spawn_lever_fix_task(parent, [self._match()], tasks_path=tasks_path)
        # Mark the first task as completed.
        data = json.loads(tasks_path.read_text())
        for t in data["tasks"]:
            if t["id"] == first:
                t["status"] = "completed"
        tasks_path.write_text(json.dumps(data))
        # Spawn again with same findings — should create a NEW task.
        second = _spawn_lever_fix_task(parent, [self._match()], tasks_path=tasks_path)
        assert second is not None
        assert second != first
        data = json.loads(tasks_path.read_text())
        pending = [t for t in data["tasks"]
                   if t.get("source") == "lever_gate" and t.get("status") == "pending"]
        assert len(pending) == 1
