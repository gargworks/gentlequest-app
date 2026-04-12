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

from scripts.third_brother_driver import _find_lever_findings_in_diff


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
