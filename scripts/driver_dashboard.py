#!/usr/bin/env python3
"""
Third Brother Driver Dashboard
================================
Real-time terminal dashboard for monitoring driver state.

Usage:
    python3 scripts/driver_dashboard.py            # one-shot display
    python3 scripts/driver_dashboard.py --watch     # refresh every 5s
"""

import json
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DRIVER_DIR = PROJECT_ROOT / ".brain" / "driver"


def load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def load_jsonl(path: Path, limit: int = 50) -> list:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries[-limit:]


def render(clear: bool = False):
    """Render the dashboard."""
    if clear:
        print("\033[2J\033[H", end="")  # ANSI clear screen

    # ── State ──
    state = load_json(DRIVER_DIR / "state.json")
    config = load_json(DRIVER_DIR / "config.json")
    tasks_data = load_json(DRIVER_DIR / "tasks.json")
    tasks = tasks_data.get("tasks", [])
    runs = load_jsonl(DRIVER_DIR / "runs.jsonl")
    alerts = load_jsonl(DRIVER_DIR / "alerts.jsonl")

    # ── Trust Ladder ──
    ladder = config.get("trust_ladder", {})
    phase = ladder.get("current_phase", 1)
    phase_names = {1: "supervised", 2: "auto-safe", 3: "auto-committed", 4: "overnight"}

    # ── Task Stats ──
    status_counts = {}
    for t in tasks:
        s = t.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    # ── Run Stats ──
    completed_runs = [r for r in runs if r.get("outcome") == "completed"]
    failed_runs = [r for r in runs if r.get("outcome") in ("blocked", "error", "timeout")]
    total_runs = len(runs)
    completion_rate = len(completed_runs) / total_runs * 100 if total_runs else 0

    # Avg duration
    durations = [r.get("duration_seconds", 0) for r in runs if r.get("duration_seconds")]
    avg_duration = sum(durations) / len(durations) if durations else 0

    # Current streak
    streak = 0
    for r in reversed(runs):
        if r.get("outcome") == "completed":
            streak += 1
        else:
            break

    # ── Header ──
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_phase = state.get("phase", "idle")
    current_task = state.get("task_id", "-")
    session = state.get("session_id", "-")

    print(f"""
============================================================
  THIRD BROTHER DRIVER v2 — Dashboard       {now}
============================================================

  STATE
  -----
  Phase:      {current_phase}
  Task:       {current_task}
  Session:    {session[:20]}{'...' if len(str(session)) > 20 else ''}

  TRUST LADDER
  ------------
  Level:      Phase {phase} ({phase_names.get(phase, '?')})
  Effort:     {config.get('claude_effort', '?')}
  Max turns:  {config.get('claude_max_turns', '?')}

  TASK QUEUE
  ----------""")

    for status in ["committed", "in_progress", "completed", "blocked", "skipped"]:
        count = status_counts.get(status, 0)
        icon = {"committed": "+", "in_progress": ">", "completed": "v",
                "blocked": "x", "skipped": "-"}.get(status, "?")
        if count:
            print(f"  [{icon}] {status:15s} {count}")

    print(f"""
  RUN HISTORY ({total_runs} total)
  ---------------------------------
  Completed:       {len(completed_runs):3d}  ({completion_rate:.0f}%)
  Failed:          {len(failed_runs):3d}
  Avg duration:    {avg_duration:.0f}s
  Current streak:  {streak} consecutive successes""")

    # Last 5 runs
    if runs:
        print(f"\n  Last 5 runs:")
        for r in runs[-5:]:
            ts = r.get("ts", "?")[:19]
            outcome = r.get("outcome", "?")
            task_id = r.get("task_id", "?")
            dur = r.get("duration_seconds", 0)
            turns = r.get("turns", 0)
            icon = "v" if outcome == "completed" else "x"
            print(f"    [{icon}] {ts}  {task_id:10s}  {outcome:12s}  {dur:4d}s  {turns}t")

    # Alerts
    if alerts:
        recent_alerts = alerts[-5:]
        print(f"\n  ALERTS (last {len(recent_alerts)})")
        print(f"  ------")
        for a in recent_alerts:
            ts = a.get("ts", "?")[:19]
            rule = a.get("rule", "?")
            severity = a.get("severity", a.get("action", "?"))
            detail = a.get("detail", "")[:50]
            print(f"    {ts}  [{severity:8s}]  {rule}: {detail}")

    print(f"\n============================================================")


def main():
    parser = argparse.ArgumentParser(description="Driver Dashboard")
    parser.add_argument("--watch", action="store_true", help="Refresh every 5s")
    args = parser.parse_args()

    if args.watch:
        try:
            while True:
                render(clear=True)
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nDashboard stopped.")
    else:
        render()


if __name__ == "__main__":
    main()
