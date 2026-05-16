#!/usr/bin/env python3
"""Phase-2 (test vs control) analysis — Mann-Whitney U + multiplier report.

Input: .brain/measurement/phase2/turns.{baseline,experimental}.jsonl
       (produced by phase2_trial_runner.sh).

For each turn, we use the same cost-equivalent metric as Phase 1:
  effective_billed = input_tokens + cache_creation_input_tokens * 1.25
                                  + cache_read_input_tokens * 0.10
This matches Anthropic's pricing structure (cache reads ~10% of normal
input rate; cache creation ~25% premium one-time).

We aggregate per-trial (one trial = many turns from one CC session sequence)
by summing effective_billed across all of that trial's turns. The trial is
the unit of comparison; turns within a trial are not independent.

Mann-Whitney U is non-parametric → no normality assumption needed for the
small samples at v1 (~10-30 trials per arm).

Spec: .brain/plans/phase2_test_vs_control_spec.md
Acceptance bands:
  multiplier > 1.5x with p < 0.05  → positive (Nucleus runtime substrate adds value)
  multiplier 1.0–1.5x with p < 0.05 → neutral (small marginal; reframe positioning)
  multiplier ≤ 1.0x or non-significant → negative (substrate not in token economics)

Usage:
  python3 scripts/phase2_analyze.py
  python3 scripts/phase2_analyze.py --json     # machine-readable
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import median


PHASE2_DIR = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/measurement/phase2")


def _effective_billed(rec: dict) -> float:
    ru = rec.get("response_usage_counters", {}) or {}
    inp = float(ru.get("input_tokens", 0) or 0)
    cr = float(ru.get("cache_read_input_tokens", 0) or 0)
    cc = float(ru.get("cache_creation_input_tokens", 0) or 0)
    return inp + 1.25 * cc + 0.10 * cr


def _load_arm(path: Path) -> list[float]:
    """Sum effective_billed per trial. A 'trial' here = a contiguous run of
    turns with the same session_id (proxy assigns one CC session per trial).
    Returns a list of per-trial total cost values."""
    if not path.exists():
        return []
    by_session: dict[str, float] = {}
    with path.open() as f:
        for line in f:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            sid = rec.get("session_id", "?")
            by_session.setdefault(sid, 0.0)
            by_session[sid] += _effective_billed(rec)
    return list(by_session.values())


def mann_whitney_u(x: list[float], y: list[float]) -> tuple[float, float]:
    """Two-sided Mann-Whitney U test, normal-approximation p-value.

    Returns (U, p). For the small samples we expect (~10-30 each), the normal
    approximation is acceptable but won't be exact for ties or n<10. For
    final reporting use scipy.stats.mannwhitneyu; this stdlib impl is
    sufficient for the directional read.
    """
    if not x or not y:
        return float("nan"), float("nan")
    nx, ny = len(x), len(y)
    pooled = sorted([(v, "x") for v in x] + [(v, "y") for v in y])

    # Average ranks, accounting for ties.
    ranks = [0.0] * len(pooled)
    i = 0
    while i < len(pooled):
        j = i
        while j + 1 < len(pooled) and pooled[j + 1][0] == pooled[i][0]:
            j += 1
        avg_rank = (i + j) / 2 + 1  # 1-indexed
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1

    rx = sum(r for r, (_, label) in zip(ranks, pooled) if label == "x")
    ux = rx - nx * (nx + 1) / 2
    uy = nx * ny - ux
    u = min(ux, uy)

    mu = nx * ny / 2
    sigma = math.sqrt(nx * ny * (nx + ny + 1) / 12)
    if sigma == 0:
        return u, 1.0
    z = (u - mu) / sigma
    # Two-sided normal-approx p-value
    p = 2 * (1 - _phi(abs(z)))
    return u, p


def _phi(z: float) -> float:
    """Standard normal CDF via erf."""
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def _summary(label: str, vals: list[float]) -> dict:
    if not vals:
        return {"arm": label, "n": 0}
    return {
        "arm": label,
        "n": len(vals),
        "mean": sum(vals) / len(vals),
        "median": median(vals),
        "min": min(vals),
        "max": max(vals),
        "values": vals,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    baseline = _load_arm(PHASE2_DIR / "turns.baseline.jsonl")
    experimental = _load_arm(PHASE2_DIR / "turns.experimental.jsonl")
    sb, se = _summary("baseline", baseline), _summary("experimental", experimental)

    multiplier = float("nan")
    p = float("nan")
    if baseline and experimental:
        multiplier = sb["mean"] / se["mean"] if se["mean"] > 0 else float("inf")
        _, p = mann_whitney_u(baseline, experimental)

    verdict = "INSUFFICIENT_DATA"
    if not (math.isnan(multiplier) or math.isnan(p)):
        if multiplier > 1.5 and p < 0.05:
            verdict = "POSITIVE — substrate adds attributable value"
        elif 1.0 <= multiplier <= 1.5 and p < 0.05:
            verdict = "NEUTRAL — small marginal; reframe positioning"
        elif multiplier > 1.0 and p >= 0.05:
            verdict = "DIRECTIONAL — trend present but underpowered (need more trials)"
        else:
            verdict = "NEGATIVE — substrate not in token economics"

    if args.json:
        print(json.dumps({
            "baseline": sb, "experimental": se,
            "multiplier_baseline_over_experimental": multiplier,
            "p_value_two_sided": p,
            "verdict": verdict,
        }, indent=2))
        return 0

    print("=== Phase-2 (test vs control) analysis ===\n")
    for s in (sb, se):
        if s["n"] == 0:
            print(f"  {s['arm']}: no trials"); continue
        print(f"  {s['arm']:<14}  n={s['n']:<4}  mean={s['mean']:>10,.0f}  "
              f"median={s['median']:>10,.0f}  range=[{s['min']:,.0f}, {s['max']:,.0f}]")
    print()
    if math.isnan(multiplier):
        print("  Multiplier: insufficient data on at least one arm.")
    else:
        print(f"  Multiplier (baseline / experimental): {multiplier:.3f}x")
        print(f"  Two-sided p-value (Mann-Whitney U):  {p:.4f}")
    print()
    print(f"  Verdict: {verdict}")
    print()
    print("  Acceptance bands per .brain/plans/phase2_test_vs_control_spec.md:")
    print("    >1.5x  + p<0.05 → positive")
    print("    1.0-1.5x + p<0.05 → neutral, reframe")
    print("    ≤1.0x or non-significant → negative or underpowered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
