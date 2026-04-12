"""Lever — bundle_size_check.

Bundle bloat creeps in one small import at a time. This lever reads a
``stats.json`` produced by the frontend build (expected shape:
``{"total_size_bytes": N}``), compares it to a baseline of the same
shape, and flags when the regression exceeds ``regression_threshold_pct``.

Missing stats or baseline → skipped (first run; no comparison possible).
Structurally mirrors ``coverage_delta`` so the pattern stays consistent
across watch-metric-file levers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .base import Lever, LeverObservation


class BundleSizeCheckLever(Lever):
    name = "bundle_size_check"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        stats_str = inputs.get("stats_path", "dist/stats.json")
        baseline_str = inputs.get(
            "baseline_path", ".brain/metrics/bundle_baseline.json"
        )
        threshold_pct = float(inputs.get("regression_threshold_pct", 5.0))
        project_root = brain_path.parent

        stats_path = Path(stats_str)
        if not stats_path.is_absolute():
            stats_path = project_root / stats_str
        baseline_path = Path(baseline_str)
        if not baseline_path.is_absolute():
            baseline_path = project_root / baseline_str

        if not stats_path.exists():
            return self.observation_skipped(
                "no_bundle_stats", path=str(stats_path)
            )
        if not baseline_path.exists():
            return self.observation_skipped(
                "no_baseline", path=str(baseline_path)
            )

        try:
            current_data = json.loads(stats_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return self.observation_error("parse_stats", f"invalid json: {e}")
        except OSError as e:
            return self.observation_error("parse_stats", f"read failed: {e}")

        try:
            baseline_data = json.loads(baseline_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return self.observation_error("parse_baseline", f"invalid json: {e}")
        except OSError as e:
            return self.observation_error("parse_baseline", f"read failed: {e}")

        try:
            current = int(current_data.get("total_size_bytes"))
            baseline = int(baseline_data.get("total_size_bytes"))
        except (TypeError, ValueError, AttributeError):
            return self.observation_error(
                "parse_stats", "total_size_bytes missing/non-integer"
            )
        if baseline <= 0:
            return self.observation_error(
                "parse_baseline", f"baseline non-positive: {baseline}"
            )

        regression_pct = ((current - baseline) / baseline) * 100.0
        base = {
            "current_bytes": current,
            "baseline_bytes": baseline,
            "regression_pct": round(regression_pct, 2),
        }
        if regression_pct > threshold_pct:
            return self.observation_found({
                **base,
                "threshold_pct": threshold_pct,
            })
        return self.observation_clean(base)
