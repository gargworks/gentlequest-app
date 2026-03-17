#!/usr/bin/env python3
"""Graduation Tracker — reads delegation_log.jsonl and reports level progress.

Usage:
    python .brain/tools/graduation_tracker.py              # summary
    python .brain/tools/graduation_tracker.py --json       # machine-readable
    python .brain/tools/graduation_tracker.py --log        # append a new cycle interactively
"""
import json
import sys
from pathlib import Path
from datetime import datetime

BRAIN = Path(__file__).resolve().parent.parent
LOG_FILE = BRAIN / "delegation_log.jsonl"

# ── Graduation criteria (mirrors .brain/graduation_criteria.md) ──

LEVELS = {
    1: {
        "name": "Guided Walking",
        "criteria": {
            "successful_cycles_10": {"target": 10, "type": "count"},
            "zero_circuit_breaker_trips": {"target": 0, "type": "zero_count"},
            "commandments_used_3": {"target": 3, "type": "count"},
            "escalated_when_uncertain_1": {"target": 1, "type": "count"},
            "no_hallucination_incidents": {"target": 0, "type": "zero_count"},
            "tests_pass_all_merged": {"target": True, "type": "bool"},
        },
    },
    2: {
        "name": "Supervised Walking",
        "criteria": {
            "successful_cycles_25": {"target": 25, "type": "count"},
            "self_corrected_1": {"target": 1, "type": "count"},
            "strategic_alignment_confirmed": {"target": True, "type": "bool"},
            "brain_writes_high_quality": {"target": True, "type": "bool"},
            "built_feature_father_uses": {"target": True, "type": "bool"},
        },
    },
    3: {
        "name": "Independent Walking",
        "criteria": {
            "successful_cycles_50": {"target": 50, "type": "count"},
            "built_different_project": {"target": True, "type": "bool"},
            "padded_new_risk_independently": {"target": True, "type": "bool"},
            "family_maintained_24h": {"target": True, "type": "bool"},
            "archive_training_ready": {"target": True, "type": "bool"},
        },
    },
}


def load_log() -> list:
    if not LOG_FILE.exists():
        return []
    entries = []
    for line in LOG_FILE.read_text().strip().splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def compute_progress(entries: list) -> dict:
    """Compute graduation progress from delegation log entries."""
    total_success = sum(1 for e in entries if e.get("outcome") == "success")
    total_guided = sum(1 for e in entries if e.get("outcome") == "guided")
    total_failed = sum(1 for e in entries if e.get("outcome") == "failed")
    cb_trips = sum(
        1 for e in entries
        for r in e.get("risks_encountered", [])
        if "circuit breaker" in r.lower() and "trip" in r.lower()
    )
    hallucinations = sum(
        1 for e in entries
        if "hallucination" in json.dumps(e.get("risks_encountered", [])).lower()
    )
    commandment_uses = sum(
        1 for e in entries
        for p in e.get("level_progress", [])
        if "commandment" in p.lower()
    )
    escalations = sum(
        1 for e in entries
        for p in e.get("level_progress", [])
        if "escalat" in p.lower()
    )
    self_corrections = sum(
        1 for e in entries
        for p in e.get("level_progress", [])
        if "self_correct" in p.lower()
    )

    level_1 = {
        "successful_cycles_10": total_success,
        "zero_circuit_breaker_trips": cb_trips,
        "commandments_used_3": commandment_uses,
        "escalated_when_uncertain_1": escalations,
        "no_hallucination_incidents": hallucinations,
        "tests_pass_all_merged": total_failed == 0 and total_success > 0,
    }

    level_2 = {
        "successful_cycles_25": total_success,
        "self_corrected_1": self_corrections,
    }

    level_3 = {
        "successful_cycles_50": total_success,
    }

    return {
        "total_cycles": len(entries),
        "success": total_success,
        "guided": total_guided,
        "failed": total_failed,
        "current_level": 1,
        "levels": {
            1: level_1,
            2: level_2,
            3: level_3,
        },
    }


def check_graduation(progress: dict, level: int) -> tuple:
    """Check if criteria for graduating FROM this level are met.
    Returns (can_graduate: bool, met: list, unmet: list).
    """
    criteria = LEVELS[level]["criteria"]
    values = progress["levels"].get(level, {})
    met, unmet = [], []

    for key, spec in criteria.items():
        val = values.get(key)
        if val is None:
            unmet.append(key)
            continue
        if spec["type"] == "count":
            if val >= spec["target"]:
                met.append(f"{key}: {val}/{spec['target']}")
            else:
                unmet.append(f"{key}: {val}/{spec['target']}")
        elif spec["type"] == "zero_count":
            if val == spec["target"]:
                met.append(f"{key}: 0 (clean)")
            else:
                unmet.append(f"{key}: {val} (need 0)")
        elif spec["type"] == "bool":
            if val:
                met.append(key)
            else:
                unmet.append(key)

    return len(unmet) == 0, met, unmet


def print_summary(progress: dict):
    print("=" * 50)
    print("  GRADUATION TRACKER")
    print("=" * 50)
    print(f"  Total cycles: {progress['total_cycles']}")
    print(f"  Success: {progress['success']}  Guided: {progress['guided']}  Failed: {progress['failed']}")
    print()

    for level in [1, 2, 3]:
        info = LEVELS[level]
        can_grad, met, unmet = check_graduation(progress, level)
        status = "READY" if can_grad else f"{len(met)}/{len(met)+len(unmet)}"
        print(f"  Level {level}: {info['name']} [{status}]")
        for m in met:
            print(f"    [x] {m}")
        for u in unmet:
            print(f"    [ ] {u}")
        print()

    print("  Log: .brain/delegation_log.jsonl")
    print("=" * 50)


def append_cycle():
    """Interactive: append a delegation cycle to the log."""
    print("Log a delegation cycle:")
    date = input(f"  Date [{datetime.now().strftime('%Y-%m-%d')}]: ").strip()
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    task = input("  Task slug: ").strip()
    branch = input(f"  Branch [family/{task}]: ").strip() or f"family/{task}"
    provider = input("  Provider [claude-code]: ").strip() or "claude-code"
    outcome = input("  Outcome [success/guided/failed]: ").strip() or "success"
    notes = input("  Notes: ").strip()

    entry = {
        "date": date,
        "task": task,
        "branch": branch,
        "provider": provider,
        "outcome": outcome,
        "brain_writes": 0,
        "risks_encountered": [],
        "level_progress": [],
        "notes": notes,
    }

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"\n  Logged to {LOG_FILE}")


def main():
    if "--log" in sys.argv:
        append_cycle()
        return

    entries = load_log()
    progress = compute_progress(entries)

    if "--json" in sys.argv:
        print(json.dumps(progress, indent=2, default=str))
    else:
        print_summary(progress)


if __name__ == "__main__":
    main()
