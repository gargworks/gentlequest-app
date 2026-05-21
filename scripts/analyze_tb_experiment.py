#!/usr/bin/env python3
"""Summarise TB interactions + review outcomes from .brain/driver/ jsonl logs.

Groups by batcomputer_enabled flag (A/B compare). Reports:
- Phase C: avg prompt/response words, duration
- Phase D: verdict distribution, avg duration
- Review log: parse method breakdown

Usage:
    python3 scripts/analyze_tb_experiment.py
"""
import json
from pathlib import Path

BRAIN_DIR = Path(__file__).resolve().parent.parent / ".brain" / "driver"
TB_LOG = BRAIN_DIR / "tb_interactions.jsonl"
REVIEW_LOG = BRAIN_DIR / "review_log.jsonl"


def load_jsonl(path: Path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def avg(xs):
    return round(sum(xs) / len(xs), 1) if xs else 0


def summarize(interactions, label):
    phase_c = [i for i in interactions if i.get("phase") == "C"]
    phase_d = [i for i in interactions if i.get("phase") == "D"]

    print(f"--- {label} ---")
    print(f"  interactions: {len(interactions)} (C={len(phase_c)}, D={len(phase_d)})")

    if phase_c:
        print(f"  Phase C avg prompt words:   {avg([i['prompt_words'] for i in phase_c])}")
        print(f"  Phase C avg response words: {avg([i['response_words'] for i in phase_c])}")
        print(f"  Phase C avg duration_ms:    {avg([i['duration_ms'] for i in phase_c])}")

    if phase_d:
        verdicts = [i.get("verdict", "") for i in phase_d]
        total = len(verdicts) or 1
        for v in ("ACCEPT", "DEEPEN", "ESCALATE"):
            n = verdicts.count(v)
            print(f"  Phase D {v:9s}: {n:3d} ({n / total:.0%})")
        print(f"  Phase D avg duration_ms:   {avg([i['duration_ms'] for i in phase_d])}")
    print()


def main():
    interactions = load_jsonl(TB_LOG)
    on = [i for i in interactions if i.get("batcomputer_enabled")]
    off = [i for i in interactions if not i.get("batcomputer_enabled")]

    print("=" * 60)
    print("  TB A/B EXPERIMENT")
    print("=" * 60)
    print(f"Total TB interactions: {len(interactions)} (ON={len(on)}, OFF={len(off)})\n")

    if off:
        summarize(off, "BATCOMPUTER OFF (baseline)")
    if on:
        summarize(on, "BATCOMPUTER ON (treatment)")

    print("-- review_log.jsonl (from tb_review_output) --")
    reviews = load_jsonl(REVIEW_LOG)
    print(f"Reviews logged: {len(reviews)}")
    parse_methods = {}
    for r in reviews:
        m = r.get("parse_method", "?")
        parse_methods[m] = parse_methods.get(m, 0) + 1
    for m, n in sorted(parse_methods.items(), key=lambda x: -x[1]):
        print(f"  parse={m}: {n}")


if __name__ == "__main__":
    main()
