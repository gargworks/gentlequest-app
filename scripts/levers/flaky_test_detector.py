"""Lever — flaky_test_detector.

A test that oscillates between pass and fail within the observation
window is flaky — it erodes trust in the full suite and masks real
regressions. This lever reads a JSONL of pytest outcomes
(``{test_id, passed, ts}``) and flags every test whose history in the
window contains *both* a pass and a fail.

The ``ts`` field is parsed as ISO-8601 (lenient — stripped ``Z`` is OK).
Entries outside the window are ignored. Missing / empty history →
``skipped``.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Set

from .base import Lever, LeverObservation


class _Counter:
    __slots__ = ("passed", "failed")

    def __init__(self) -> None:
        self.passed = False
        self.failed = False


class FlakyTestDetectorLever(Lever):
    name = "flaky_test_detector"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        history_str = inputs.get("history_path", ".brain/metrics/pytest_history.jsonl")
        window_hours = float(inputs.get("window_hours", 48))
        max_findings = int(inputs.get("max_findings", 25))

        history_path = Path(history_str)
        if not history_path.is_absolute():
            history_path = brain_path.parent / history_str

        try:
            raw = history_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return self.observation_skipped(
                "no_test_history", path=str(history_path)
            )
        except OSError as e:
            return self.observation_error("history_load", f"read failed: {e}")

        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        counters: Dict[str, _Counter] = {}
        considered = 0
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                return self.observation_error(
                    "parse_history", f"invalid json: {e}"
                )
            if not isinstance(entry, dict):
                continue
            test_id = entry.get("test_id")
            ts_raw = entry.get("ts")
            if not isinstance(test_id, str) or not isinstance(ts_raw, str):
                continue
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except ValueError:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts < cutoff:
                continue
            considered += 1
            slot = counters.setdefault(test_id, _Counter())
            if entry.get("passed") is True:
                slot.passed = True
            elif entry.get("passed") is False:
                slot.failed = True

        flaky: Set[str] = {tid for tid, c in counters.items() if c.passed and c.failed}
        sorted_flaky = sorted(flaky)[:max_findings]

        base = {
            "entries_in_window": considered,
            "tests_tracked": len(counters),
            "window_hours": window_hours,
        }
        if sorted_flaky:
            return self.observation_found({**base, "findings": sorted_flaky})
        return self.observation_clean(base)
