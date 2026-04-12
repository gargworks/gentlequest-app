"""Lever — perf_regression_spotter.

Performance metrics drift one basis point at a time until the P95
graph suddenly hockey-sticks. This lever reads a JSONL of labelled
perf samples (``{metric_name, duration_ms, ...}``) and flags *each*
metric whose latest sample regresses beyond
``regression_threshold_pct`` vs the median of its prior
``window_size`` samples.

Grouping by ``metric_name`` is what makes this different from
``runtime_regression`` — one file, many metrics, one observation
with a findings list.
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from .base import Lever, LeverObservation


class PerfRegressionSpotterLever(Lever):
    name = "perf_regression_spotter"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        perf_str = inputs.get("perf_log_path", ".brain/metrics/perf.jsonl")
        window_size = int(inputs.get("window_size", 10))
        threshold_pct = float(inputs.get("regression_threshold_pct", 20.0))
        max_findings = int(inputs.get("max_findings", 25))

        perf_path = Path(perf_str)
        if not perf_path.is_absolute():
            perf_path = brain_path.parent / perf_str

        try:
            raw = perf_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return self.observation_skipped(
                "no_perf_history", path=str(perf_path)
            )
        except OSError as e:
            return self.observation_error("perf_load", f"read failed: {e}")

        by_metric: Dict[str, List[float]] = defaultdict(list)
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                return self.observation_error(
                    "parse_perf", f"invalid json: {e}"
                )
            if not isinstance(entry, dict):
                continue
            metric = entry.get("metric_name")
            dur = entry.get("duration_ms")
            if not isinstance(metric, str) or not metric:
                continue
            try:
                by_metric[metric].append(float(dur))
            except (TypeError, ValueError):
                continue

        measurable = {m: v for m, v in by_metric.items() if len(v) >= 2}
        if not measurable:
            return self.observation_skipped(
                "insufficient_history", metrics=len(by_metric)
            )

        findings: List[str] = []
        for metric in sorted(measurable):
            samples = measurable[metric]
            latest = samples[-1]
            prior = samples[-(window_size + 1):-1]
            baseline = statistics.median(prior)
            if baseline <= 0:
                continue
            regression_pct = ((latest - baseline) / baseline) * 100.0
            if regression_pct > threshold_pct:
                findings.append(
                    f"{metric}: +{regression_pct:.1f}% "
                    f"({baseline:.1f}ms->{latest:.1f}ms)"
                )
                if len(findings) >= max_findings:
                    break

        base = {
            "metrics_checked": len(measurable),
            "threshold_pct": threshold_pct,
        }
        if findings:
            return self.observation_found({**base, "findings": findings})
        return self.observation_clean(base)
