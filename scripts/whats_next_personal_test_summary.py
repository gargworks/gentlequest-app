#!/usr/bin/env python3
"""Aggregate whats_next.py personal-test observations.

Reads .brain/research/2026-04-28_tier_architecture/personal_test_log.jsonl
and reports source-distribution / top-action churn / score trend so peer
can decide whether to surface whats_next.py v0.1 as ready-for-beta or
needs v0.2 refinement.

Usage:
    python3 scripts/whats_next_personal_test_summary.py
    python3 scripts/whats_next_personal_test_summary.py --since 2026-05-01
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / ".brain" / "research" / "2026-04-28_tier_architecture" / "personal_test_log.jsonl"


def load(since: str | None = None) -> list[dict]:
    if not LOG_PATH.exists():
        return []
    rows = []
    with LOG_PATH.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if since and r.get("ts", "") < since:
                continue
            rows.append(r)
    return rows


def summarize(rows: list[dict]) -> str:
    if not rows:
        return "no observations yet"
    lines = []
    lines.append(f"# whats_next.py personal-test summary (n={len(rows)})")
    lines.append("")
    lines.append(f"first run: {rows[0].get('ts','?')}")
    lines.append(f"last run:  {rows[-1].get('ts','?')}")
    lines.append("")

    top_sources = Counter()
    top_summaries = Counter()
    score_distribution = []
    for r in rows:
        for a in r.get("top", [])[:1]:
            top_sources[a.get("source", "?")] += 1
            top_summaries[a.get("summary", "?")[:50]] += 1
            score_distribution.append(a.get("score", 0.0))

    lines.append("## Top-1 source distribution")
    for src, n in top_sources.most_common():
        lines.append(f"  {src:10s}  {n}/{len(rows)}  ({100*n/len(rows):.0f}%)")
    lines.append("")

    lines.append("## Top-1 summary churn (most-frequent surface)")
    for summary, n in top_summaries.most_common(5):
        lines.append(f"  {n}× — {summary}")
    lines.append("")

    if score_distribution:
        lines.append("## Top-1 score stats")
        avg = sum(score_distribution) / len(score_distribution)
        lo, hi = min(score_distribution), max(score_distribution)
        lines.append(f"  mean={avg:.2f}  min={lo:.2f}  max={hi:.2f}  n={len(score_distribution)}")
        lines.append("")

    n_default = sum(1 for r in rows if r.get("top") and r["top"][0].get("source") == "default")
    n_actionable = len(rows) - n_default
    lines.append(f"## Verdict signal")
    lines.append(f"  actionable surfaces: {n_actionable}/{len(rows)} ({100*n_actionable/len(rows):.0f}%)")
    lines.append(f"  default-baseline (no urgent): {n_default}/{len(rows)} ({100*n_default/len(rows):.0f}%)")
    lines.append("")
    lines.append("# Interpretation")
    if n_actionable >= 3 and n_default >= 3:
        lines.append("  Healthy mix — script surfaces real signals when present + correctly defaults to no-urgent when state is clean.")
        lines.append("  Ready-for-Lokesh-review.")
    elif n_actionable < 3:
        lines.append("  Mostly default-baseline. Either life is genuinely quiet OR scoring is missing actual signals.")
        lines.append("  Run a few more days OR introspect: did peer hit moments where intuition said 'should act' but script said 'no urgent'?")
    elif n_default < 3:
        lines.append("  Always-actionable. Either life is genuinely busy OR scoring threshold too low.")
        lines.append("  Calibrate baseline_idle_suggestion threshold (currently 6.0).")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=None, help="ISO timestamp lower bound")
    args = ap.parse_args()
    rows = load(since=args.since)
    print(summarize(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
