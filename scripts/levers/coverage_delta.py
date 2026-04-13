"""Lever — coverage_delta.

Coverage regressions are easy to miss when they arrive as a 0.5 pp drift
per PR. This lever parses the coverage.xml produced by ``coverage``
(cobertura-flavoured — ``<coverage line-rate="0.85">``), compares it
against a baseline JSON (``{"line_rate": 0.85}``), and flags a drop
greater than ``drop_threshold_pct`` percentage points.

Missing coverage.xml → ``skipped`` (no run to judge). Missing baseline →
``skipped`` (first-run bootstrap). Malformed XML / JSON → ``error``.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict

from .base import Lever, LeverObservation


class CoverageDeltaLever(Lever):
    name = "coverage_delta"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        coverage_str = inputs.get("coverage_path", "coverage.xml")
        baseline_str = inputs.get(
            "baseline_path", ".brain/metrics/coverage_baseline.json"
        )
        drop_threshold_pct = float(inputs.get("drop_threshold_pct", 2.0))
        project_root = brain_path.parent

        coverage_path = Path(coverage_str)
        if not coverage_path.is_absolute():
            coverage_path = project_root / coverage_str
        baseline_path = Path(baseline_str)
        if not baseline_path.is_absolute():
            baseline_path = project_root / baseline_str

        if not coverage_path.exists():
            return self.observation_skipped(
                "no_coverage_report", path=str(coverage_path)
            )
        if not baseline_path.exists():
            return self.observation_skipped(
                "no_baseline", path=str(baseline_path)
            )

        try:
            tree = ET.parse(coverage_path)
        except ET.ParseError as e:
            return self.observation_error("parse_coverage", f"invalid xml: {e}")
        except OSError as e:
            return self.observation_error("parse_coverage", f"read failed: {e}")

        root = tree.getroot()
        line_rate_str = root.get("line-rate")
        try:
            current = float(line_rate_str)
        except (TypeError, ValueError):
            return self.observation_error(
                "parse_coverage", f"line-rate missing/non-numeric: {line_rate_str!r}"
            )

        try:
            baseline_data = json.loads(baseline_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return self.observation_error("parse_baseline", f"invalid json: {e}")
        except OSError as e:
            return self.observation_error("parse_baseline", f"read failed: {e}")

        try:
            baseline = float(baseline_data.get("line_rate"))
        except (TypeError, ValueError, AttributeError):
            return self.observation_error(
                "parse_baseline", f"line_rate missing/non-numeric"
            )

        drop_pp = (baseline - current) * 100.0
        base = {
            "current_line_rate": round(current, 4),
            "baseline_line_rate": round(baseline, 4),
            "drop_pp": round(drop_pp, 3),
        }
        if drop_pp > drop_threshold_pct:
            return self.observation_found({
                **base,
                "threshold_pp": drop_threshold_pct,
            })
        return self.observation_clean(base)
