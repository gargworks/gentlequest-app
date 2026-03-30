#!/usr/bin/env python3
"""
Morning Briefing Generator — Third Brother context assembly + Claude analysis.

Gathers: git log since yesterday, shadow_log last 10 entries, pending tasks.
Sends to Claude via `claude -p` for analysis.
Outputs: priorities, stalled work, suggested focus.
Saves to .brain/briefings/YYYY-MM-DD.md.

Usage:
    python3 scripts/morning_brief.py                    # generate today's brief
    python3 scripts/morning_brief.py --date 2026-03-22  # specific date
    python3 scripts/morning_brief.py --dry-run           # print context, skip Claude
    python3 scripts/morning_brief.py --stdout             # print to stdout instead of file
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRAIN_PATH = PROJECT_ROOT / ".brain"
DRIVER_DIR = BRAIN_PATH / "driver"
BRIEFINGS_DIR = BRAIN_PATH / "briefings"
SHADOW_LOG = DRIVER_DIR / "shadow_log.jsonl"
TASKS_PATH = DRIVER_DIR / "tasks.json"
RUNS_PATH = DRIVER_DIR / "runs.jsonl"


# ── Context gatherers ────────────────────────────────────────

def gather_git_log(since: str) -> str:
    """git log --since yesterday, compact format."""
    try:
        result = subprocess.run(
            ["git", "log", f"--since={since}", "--oneline", "--no-merges", "--max-count=30"],
            capture_output=True, text=True, timeout=10, cwd=str(PROJECT_ROOT),
        )
        log = result.stdout.strip()
        return log if log else "(no commits since yesterday)"
    except Exception as e:
        return f"(git log error: {e})"


def gather_shadow_log(n: int = 10) -> str:
    """Last N entries from shadow_log.jsonl — task outcomes, durations."""
    if not SHADOW_LOG.exists():
        return "(no shadow_log found)"

    lines = SHADOW_LOG.read_text().strip().split("\n")
    recent = lines[-n:] if len(lines) >= n else lines

    entries = []
    for line in recent:
        try:
            e = json.loads(line)
            duration_min = round(e.get("latency_ms", 0) / 60000, 1)
            entries.append(
                f"- [{e.get('outcome', '?')}] {e.get('task_title', '?')} "
                f"({duration_min}min, {e.get('total_turns', 0)} turns)"
            )
        except json.JSONDecodeError:
            continue

    return "\n".join(entries) if entries else "(shadow_log empty)"


def gather_pending_tasks() -> str:
    """Pending tasks from driver task queue."""
    if not TASKS_PATH.exists():
        return "(no tasks.json found)"

    try:
        data = json.loads(TASKS_PATH.read_text())
        tasks = data.get("tasks", [])
    except (json.JSONDecodeError, KeyError):
        return "(tasks.json parse error)"

    pending = [t for t in tasks if t.get("status") in ("committed", "in_progress", "blocked")]
    if not pending:
        return "(no pending tasks)"

    lines = []
    for t in sorted(pending, key=lambda x: x.get("priority", 99)):
        status = t.get("status", "?")
        reason = f" — {t['failure_reason']}" if t.get("failure_reason") else ""
        lines.append(
            f"- [P{t.get('priority', '?')}] [{status}] {t.get('title', '?')}{reason}"
        )
    return "\n".join(lines)


def gather_recent_runs(n: int = 5) -> str:
    """Last N run outcomes from runs.jsonl."""
    if not RUNS_PATH.exists():
        return "(no runs.jsonl found)"

    lines = RUNS_PATH.read_text().strip().split("\n")
    recent = lines[-n:] if len(lines) >= n else lines

    entries = []
    for line in recent:
        try:
            e = json.loads(line)
            retries = f", {e['retry_count']} retries" if e.get("retry_count") else ""
            entries.append(
                f"- [{e.get('outcome', '?')}] {e.get('task_title', '?')} "
                f"({e.get('duration_seconds', 0)}s, {e.get('turns', 0)} turns{retries})"
            )
        except json.JSONDecodeError:
            continue

    return "\n".join(entries) if entries else "(runs.jsonl empty)"


# ── Prompt assembly ──────────────────────────────────────────

BRIEF_PROMPT = """You are Third Brother, the family's project manager. Generate a morning briefing.

## Context

### Git log (since yesterday)
{git_log}

### Recent driver runs (last 5)
{recent_runs}

### Shadow log (last 10 task executions)
{shadow_log}

### Pending tasks
{pending_tasks}

### Current date/time
{now}

## Instructions

Write a concise morning brief with these exact sections:

### Priorities for today
- Top 3 things to focus on, based on pending tasks, recent failures, and momentum

### Stalled work
- Anything blocked, repeatedly failing, or stuck in_progress. If nothing is stalled, say so.

### Suggested focus
- One concrete recommendation for what to do FIRST this morning, with reasoning

### Health check
- Driver reliability: any retries, timeouts, or crashes in recent runs?
- Task throughput: completion rate from shadow log

Keep it under 300 words. Be direct. No fluff."""


def build_context(since: str) -> str:
    """Assemble all context sources into the prompt."""
    return BRIEF_PROMPT.format(
        git_log=gather_git_log(since),
        recent_runs=gather_recent_runs(),
        shadow_log=gather_shadow_log(),
        pending_tasks=gather_pending_tasks(),
        now=datetime.now().strftime("%Y-%m-%d %H:%M (%A)"),
    )


# ── Execution ────────────────────────────────────────────────

def run_claude(prompt: str) -> str:
    """Send prompt to Claude via CLI, return response text."""
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "text",
        "--max-turns", "1",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return f"[CLAUDE ERROR] exit {result.returncode}: {result.stderr[:500]}"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[CLAUDE ERROR] timeout after 120s"
    except FileNotFoundError:
        return "[CLAUDE ERROR] claude CLI not found in PATH"


def save_briefing(content: str, date_str: str) -> Path:
    """Save briefing to .brain/briefings/YYYY-MM-DD.md."""
    BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
    path = BRIEFINGS_DIR / f"{date_str}.md"
    path.write_text(f"# Morning Brief — {date_str}\n\n{content}\n")
    return path


def main():
    parser = argparse.ArgumentParser(description="Morning briefing generator")
    parser.add_argument("--date", default=None, help="Date for briefing (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Print context only, skip Claude")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of file")
    args = parser.parse_args()

    today = args.date or datetime.now().strftime("%Y-%m-%d")
    today_dt = datetime.strptime(today, "%Y-%m-%d")
    # On Monday, look back to Friday (3 days) to cover the weekend gap
    lookback_days = 3 if today_dt.weekday() == 0 else 1
    yesterday = (today_dt - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    prompt = build_context(since=yesterday)

    if args.dry_run:
        print("=== DRY RUN — Context that would be sent to Claude ===\n")
        print(prompt)
        return 0

    print(f"[BRIEF] Generating morning briefing for {today}...")
    brief = run_claude(prompt)

    if args.stdout:
        print(brief)
    else:
        path = save_briefing(brief, today)
        print(f"[BRIEF] Saved to {path}")
        print(brief)

    return 0


if __name__ == "__main__":
    sys.exit(main())
