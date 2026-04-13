"""Lever — golden_benchmark_check.

CSR (Claim Survival Rate) is the flywheel's trust metric. If it drops
below ``baseline_csr`` the system is breaking claims faster than it is
recovering them. This lever reads ``.brain/flywheel/csr.json`` and
surfaces a finding whenever CSR regresses, so cron_hourly / post_commit
catches the regression without waiting for a human to open the dashboard.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .base import Lever, LeverObservation


class GoldenBenchmarkCheckLever(Lever):
    name = "golden_benchmark_check"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        csr_path_str = inputs.get("csr_path", ".brain/flywheel/csr.json")
        baseline_csr = float(inputs.get("baseline_csr", 0.90))
        window_hours = int(inputs.get("window_hours", 24))

        csr_path = Path(csr_path_str)
        if not csr_path.is_absolute():
            csr_path = brain_path.parent / csr_path_str

        try:
            raw = csr_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return self.observation_skipped("no_csr_snapshot", path=str(csr_path))
        except OSError as e:
            return self.observation_error("csr_load", f"read failed: {e}")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            return self.observation_error("parse_csr", f"invalid json: {e}")

        if not isinstance(data, dict):
            return self.observation_error(
                "parse_csr", f"csr snapshot is not an object: {type(data).__name__}"
            )
        csr_value = data.get("ratio", data.get("csr"))
        try:
            csr = float(csr_value)
        except (TypeError, ValueError):
            return self.observation_error(
                "parse_csr", f"ratio/csr field not numeric: {csr_value!r}"
            )

        if csr < baseline_csr:
            delta = round(csr - baseline_csr, 6)
            return self.observation_found({
                "csr": csr,
                "baseline_csr": baseline_csr,
                "delta": delta,
                "window_hours": window_hours,
            })
        return self.observation_clean({
            "csr": csr,
            "baseline_csr": baseline_csr,
        })
