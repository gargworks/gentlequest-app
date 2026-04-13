"""Lever — runtime_regression.

Slow tests rot the feedback loop. This lever reads a JSONL of recent
pytest runs (``{ts, duration_seconds, ...}``) and flags when the *latest*
run's duration regresses beyond ``regression_threshold_pct`` vs the
median of the prior ``window_size`` runs.

Zero history / one-entry history → ``skipped`` (no baseline yet).
Median is computed on prior runs only so the latest entry never
compares against itself.

Named ``runtime_regression`` (not ``test_runtime_regression``) so the
filename doesn't collide with pytest's ``test_*.py`` discovery rule or
the repo-level ``.gitignore test_*.py`` pattern.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any, Dict, List

from .base import Lever, LeverObservation


class RuntimeRegressionLever(Lever):
    name = "runtime_regression"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        runtimes_str = inputs.get("runtimes_path", ".brain/metrics/test_runtime.jsonl")
        window_size = int(inputs.get("window_size", 10))
        threshold_pct = float(inputs.get("regression_threshold_pct", 25.0))

        runtimes_path = Path(runtimes_str)
        if not runtimes_path.is_absolute():
            runtimes_path = brain_path.parent / runtimes_str

        try:
            raw = runtimes_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return self.observation_skipped(
                "no_runtime_history", path=str(runtimes_path)
            )
        except OSError as e:
            return self.observation_error("runtime_load", f"read failed: {e}")

        durations: List[float] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                return self.observation_error(
                    "parse_runtime", f"invalid json: {e}"
                )
            if not isinstance(entry, dict):
                continue
            dur = entry.get("duration_seconds")
            try:
                durations.append(float(dur))
            except (TypeError, ValueError):
                continue

        if len(durations) < 2:
            return self.observation_skipped(
                "insufficient_history", entries=len(durations)
            )

        latest = durations[-1]
        prior = durations[-(window_size + 1):-1]
        baseline = statistics.median(prior)
        if baseline <= 0:
            return self.observation_error(
                "parse_runtime", f"baseline non-positive: {baseline}"
            )
        regression_pct = ((latest - baseline) / baseline) * 100.0

        base = {
            "latest_seconds": round(latest, 3),
            "baseline_seconds": round(baseline, 3),
            "regression_pct": round(regression_pct, 2),
            "window_size": len(prior),
        }
        if regression_pct > threshold_pct:
            return self.observation_found({
                **base,
                "threshold_pct": threshold_pct,
            })
        return self.observation_clean(base)
