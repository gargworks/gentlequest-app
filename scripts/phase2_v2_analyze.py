#!/usr/bin/env python3
"""Phase-2 v2 analysis — dollar-cost headline + composite breakdown.

Headline: per-trial cost in dollars (Claude Sonnet 4.6 pricing as of writing;
adjust _PRICE_* below if model changes). Multiplier reported alongside.

Composite breakdown (engineering-side):
  - cache effect:       cost-saving from cache_read tokens vs uncached input
  - substrate effect:   delta in nucleus_* tool input/output tokens
  - iteration effect:   turns-to-completion delta

Per-trial unit: one CC session (`session_id` from proxy capture).

Spec: .brain/plans/phase2_test_vs_control_spec.md
Acceptance bands (per spec):
  >1.5x with p<0.05  → positive
  1.0–1.5x w/ p<0.05 → neutral, reframe
  ≤1.0x or n.s.      → negative or underpowered
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import median
from collections import defaultdict


PHASE2_V2_DIR = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/measurement/phase2_v2")

# Anthropic Claude Sonnet 4.6 pricing (USD per 1M tokens, approx).
# Source: anthropic.com/pricing as of 2026-04. Update if model changes.
_PRICE_INPUT_PER_M  = 3.00
_PRICE_CACHE_READ   = 0.30   # 10% of input
_PRICE_CACHE_WRITE  = 3.75   # 1.25x input (5-min TTL standard rate)
_PRICE_OUTPUT_PER_M = 15.00


def _trial_cost_usd(turns: list[dict]) -> dict:
    """Per-trial cost decomposition in USD."""
    inp = sum(t.get("response_usage_counters", {}).get("input_tokens", 0) for t in turns)
    cr  = sum(t.get("response_usage_counters", {}).get("cache_read_input_tokens", 0) for t in turns)
    cc  = sum(t.get("response_usage_counters", {}).get("cache_creation_input_tokens", 0) for t in turns)
    out = sum(t.get("response_usage_counters", {}).get("output_tokens", 0) for t in turns)

    cost_input  = inp * _PRICE_INPUT_PER_M  / 1_000_000
    cost_cr     = cr  * _PRICE_CACHE_READ   / 1_000_000
    cost_cw     = cc  * _PRICE_CACHE_WRITE  / 1_000_000
    cost_output = out * _PRICE_OUTPUT_PER_M / 1_000_000
    total_cost  = cost_input + cost_cr + cost_cw + cost_output

    return {
        "n_turns": len(turns),
        "tokens": {"input": inp, "cache_read": cr, "cache_creation": cc, "output": out},
        "cost_usd": total_cost,
        "cost_breakdown": {
            "input": cost_input, "cache_read": cost_cr,
            "cache_creation": cost_cw, "output": cost_output,
        },
    }


def _load_arm(path: Path) -> list[dict]:
    """Group turns by session_id; one trial per session."""
    if not path.exists():
        return []
    by_session = defaultdict(list)
    with path.open() as f:
        for line in f:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            sid = rec.get("session_id", "?")
            by_session[sid].append(rec)
    return [_trial_cost_usd(turns) for turns in by_session.values()]


def mann_whitney_u(x: list[float], y: list[float]) -> tuple[float, float]:
    if not x or not y: return float("nan"), float("nan")
    nx, ny = len(x), len(y)
    pooled = sorted([(v, "x") for v in x] + [(v, "y") for v in y])
    ranks = [0.0] * len(pooled); i = 0
    while i < len(pooled):
        j = i
        while j + 1 < len(pooled) and pooled[j+1][0] == pooled[i][0]: j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j+1): ranks[k] = avg
        i = j + 1
    rx = sum(r for r, (_, lab) in zip(ranks, pooled) if lab == "x")
    ux = rx - nx * (nx+1) / 2
    u = min(ux, nx*ny - ux)
    mu = nx * ny / 2
    sigma = math.sqrt(nx * ny * (nx+ny+1) / 12)
    if sigma == 0: return u, 1.0
    z = (u - mu) / sigma
    return u, 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))


def _summary(label: str, trials: list[dict]) -> dict:
    if not trials:
        return {"arm": label, "n_trials": 0}
    costs = [t["cost_usd"] for t in trials]
    turns = [t["n_turns"] for t in trials]
    return {
        "arm": label, "n_trials": len(trials),
        "cost_mean_usd":   sum(costs) / len(costs),
        "cost_median_usd": median(costs),
        "cost_min_usd":    min(costs),
        "cost_max_usd":    max(costs),
        "turns_mean":      sum(turns) / len(turns),
        "turns_median":    median(turns),
        "tokens_total":    sum(t["tokens"]["input"]+t["tokens"]["output"] for t in trials),
        "cache_read_total":      sum(t["tokens"]["cache_read"] for t in trials),
        "cache_creation_total":  sum(t["tokens"]["cache_creation"] for t in trials),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    baseline = _load_arm(PHASE2_V2_DIR / "turns.baseline.jsonl")
    experimental = _load_arm(PHASE2_V2_DIR / "turns.experimental.jsonl")
    sb, se = _summary("baseline", baseline), _summary("experimental", experimental)

    multiplier = float("nan"); p = float("nan")
    if baseline and experimental:
        b_costs = [t["cost_usd"] for t in baseline]
        e_costs = [t["cost_usd"] for t in experimental]
        multiplier = (se["cost_mean_usd"] / sb["cost_mean_usd"]) if sb["cost_mean_usd"] > 0 else float("inf")
        # Note: multiplier > 1 means experimental costs MORE than baseline →
        # baseline (with substrate) is cheaper → substrate adds value.
        _, p = mann_whitney_u(b_costs, e_costs)

    # Iteration delta
    iter_delta = (se["turns_mean"] / sb["turns_mean"]) if (baseline and experimental and sb["turns_mean"] > 0) else float("nan")

    verdict = "INSUFFICIENT_DATA"
    if not (math.isnan(multiplier) or math.isnan(p)):
        if multiplier > 1.5 and p < 0.05:
            verdict = "POSITIVE — substrate adds attributable value above caching"
        elif 1.0 <= multiplier <= 1.5 and p < 0.05:
            verdict = "NEUTRAL — small marginal; reframe positioning around composite story"
        elif multiplier > 1.0 and p >= 0.05:
            verdict = "DIRECTIONAL — trend present but underpowered"
        else:
            verdict = "NEGATIVE — substrate not in token economics"

    if args.json:
        print(json.dumps({
            "baseline": sb, "experimental": se,
            "multiplier_experimental_over_baseline": multiplier,
            "iteration_multiplier": iter_delta,
            "p_value_two_sided": p,
            "verdict": verdict,
        }, indent=2))
        return 0

    print("=== Phase-2 v2 (test vs control) — dollar-cost analysis ===\n")
    print(f"  Pricing model: Claude Sonnet 4.6 (input ${_PRICE_INPUT_PER_M}/M, "
          f"output ${_PRICE_OUTPUT_PER_M}/M, cache_read ${_PRICE_CACHE_READ}/M, "
          f"cache_creation ${_PRICE_CACHE_WRITE}/M)\n")

    for s in (sb, se):
        if s["n_trials"] == 0:
            print(f"  {s['arm']}: no trials"); continue
        print(f"  {s['arm']:<14}  trials={s['n_trials']:<3}  "
              f"cost ${s['cost_mean_usd']:.4f} ± ${(s['cost_max_usd']-s['cost_min_usd'])/2:.4f}  "
              f"turns avg={s['turns_mean']:.1f}  cache_read_total={s['cache_read_total']:,}")
    print()

    if math.isnan(multiplier):
        print("  Headline: insufficient data on at least one arm.")
    else:
        savings = (se["cost_mean_usd"] - sb["cost_mean_usd"])
        print(f"  ───────────────────────────────────────────────────")
        print(f"  HEADLINE — Nucleus saves ${savings:.4f} per session")
        print(f"             ({multiplier:.2f}x vs without-substrate)")
        print(f"  ───────────────────────────────────────────────────")
        print()
        print(f"  COMPOSITE breakdown:")
        print(f"    iteration multiplier (turns ratio):   {iter_delta:.2f}x")
        print(f"    cache effect:    cache_read tokens contribute heavily; see per-arm totals above")
        print(f"    substrate effect: delta = baseline ${sb['cost_mean_usd']:.4f} - experimental ${se['cost_mean_usd']:.4f}")
        print()
        print(f"  Significance: p = {p:.4f} (two-sided Mann-Whitney U)")

    print()
    print(f"  Verdict: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
