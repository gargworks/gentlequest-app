#!/usr/bin/env python3
"""
Task Suggestion via Third Brother
===================================
Reads recent git history, completed tasks, and run patterns,
then asks Ollama third-brother for 5 concrete next tasks.

Usage:
    python3 scripts/suggest_tasks.py             # show suggestions
    python3 scripts/suggest_tasks.py --apply     # add to tasks.json
    python3 scripts/suggest_tasks.py --model X   # use different Ollama model
"""

import json
import argparse
import subprocess
import urllib.request
import urllib.error
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DRIVER_DIR = PROJECT_ROOT / ".brain" / "driver"
TASKS_PATH = DRIVER_DIR / "tasks.json"
RUNS_PATH = DRIVER_DIR / "runs.jsonl"

DEFAULT_MODEL = "third-brother"
OLLAMA_URL = "http://localhost:11434/api/generate"


def get_git_log(n: int = 20) -> str:
    """Get recent git log."""
    try:
        result = subprocess.run(
            ["git", "log", f"-{n}", "--oneline", "--no-decorate"],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def get_git_diff_stat() -> str:
    """Get uncommitted changes summary."""
    try:
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD"],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def load_tasks() -> list:
    """Load tasks from tasks.json."""
    if not TASKS_PATH.exists():
        return []
    try:
        data = json.loads(TASKS_PATH.read_text())
        return data.get("tasks", [])
    except (json.JSONDecodeError, OSError):
        return []


def load_runs(limit: int = 20) -> list:
    """Load recent runs."""
    if not RUNS_PATH.exists():
        return []
    entries = []
    for line in RUNS_PATH.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries[-limit:]


def build_prompt(git_log: str, diff_stat: str, tasks: list, runs: list) -> str:
    """Build the suggestion prompt with full context."""
    # Completed tasks summary
    completed = [t for t in tasks if t.get("status") == "completed"]
    committed = [t for t in tasks if t.get("status") == "committed"]

    completed_summary = "\n".join(
        f"  - {t['id']}: {t['title']}" for t in completed[-10:]
    ) or "  (none)"

    committed_summary = "\n".join(
        f"  - {t['id']}: {t['title']}" for t in committed
    ) or "  (none)"

    # Run patterns
    if runs:
        outcomes = {}
        for r in runs:
            o = r.get("outcome", "unknown")
            outcomes[o] = outcomes.get(o, 0) + 1
        run_summary = ", ".join(f"{k}: {v}" for k, v in sorted(outcomes.items()))
    else:
        run_summary = "(no runs yet)"

    return f"""You are Third Brother — a project-aware AI that understands the Nucleus codebase.

Based on the context below, suggest exactly 5 concrete, actionable tasks for the autonomous driver to execute next. Each task should be specific enough for Claude Code to implement in 20-30 turns.

CONTEXT:

Recent git commits:
{git_log or '(no recent commits)'}

Uncommitted changes:
{diff_stat or '(none)'}

Completed tasks (last 10):
{completed_summary}

Queued tasks (committed, not started):
{committed_summary}

Run outcomes (last 20):
{run_summary}

INSTRUCTIONS:
- Suggest tasks that build on completed work, not repeat it
- Each task needs: title (short), description (detailed enough for autonomous execution), scope (file globs), priority (1=critical, 4=low)
- Focus on: tests, hardening, wiring existing components, documentation
- Do NOT suggest tasks already in the queue
- Output valid JSON array of 5 objects with keys: title, description, scope, priority

Respond ONLY with the JSON array, no other text."""


def query_ollama(model: str, prompt: str) -> str:
    """Query Ollama and return the response text."""
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 4096, "temperature": 0.7},
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
            return data.get("response", "")
    except urllib.error.URLError as e:
        print(f"  Error connecting to Ollama: {e}")
        print(f"  Make sure Ollama is running: ollama serve")
        return ""
    except Exception as e:
        print(f"  Ollama query failed: {e}")
        return ""


def parse_suggestions(response: str) -> list:
    """Parse JSON array from model response."""
    # Try direct parse
    text = response.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        suggestions = json.loads(text)
        if isinstance(suggestions, list):
            return suggestions
    except json.JSONDecodeError:
        pass

    # Try to find JSON array in response
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        try:
            suggestions = json.loads(text[start:end + 1])
            if isinstance(suggestions, list):
                return suggestions
        except json.JSONDecodeError:
            pass

    print("  Failed to parse suggestions as JSON.")
    print(f"  Raw response:\n{response[:500]}")
    return []


def display_suggestions(suggestions: list):
    """Pretty-print suggested tasks."""
    print(f"\nSuggested Tasks ({len(suggestions)})")
    print("=" * 60)
    for i, s in enumerate(suggestions, 1):
        title = s.get("title", "?")
        desc = s.get("description", "?")
        scope = s.get("scope", [])
        priority = s.get("priority", 3)
        if isinstance(scope, str):
            scope = [scope]
        print(f"\n  [{i}] {title}")
        print(f"      Priority: {priority}")
        print(f"      Scope:    {', '.join(scope)}")
        # Truncate description for display
        if len(desc) > 200:
            print(f"      Desc:     {desc[:200]}...")
        else:
            print(f"      Desc:     {desc}")
    print()


def apply_suggestions(suggestions: list, tasks: list):
    """Add suggestions to tasks.json."""
    # Find next task ID
    existing_ids = [t.get("id", "") for t in tasks]
    max_num = 0
    for tid in existing_ids:
        try:
            num = int(tid.split("-")[-1])
            max_num = max(max_num, num)
        except (ValueError, IndexError):
            pass

    added = []
    for s in suggestions:
        max_num += 1
        task_id = f"task-{max_num:03d}"
        scope = s.get("scope", [])
        if isinstance(scope, str):
            scope = [scope]

        task = {
            "id": task_id,
            "title": s.get("title", ""),
            "description": s.get("description", ""),
            "scope": scope,
            "priority": s.get("priority", 3),
            "status": "committed",
            "max_turns": 30,
            "plan_file": "",
            "assigned_to": "third-brother-driver-v2",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "failure_reason": None,
        }
        tasks.append(task)
        added.append(task_id)

    # Write back
    data = {
        "tasks": tasks,
        "schema_version": 1,
        "updated_at": datetime.now().isoformat(),
    }
    TASKS_PATH.write_text(json.dumps(data, indent=2))
    print(f"  Added {len(added)} tasks: {', '.join(added)}")


def main():
    parser = argparse.ArgumentParser(description="Task Suggestion via Third Brother")
    parser.add_argument("--apply", action="store_true", help="Add suggestions to tasks.json")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL,
                        help=f"Ollama model (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    print("Gathering context...")
    git_log = get_git_log()
    diff_stat = get_git_diff_stat()
    tasks = load_tasks()
    runs = load_runs()

    prompt = build_prompt(git_log, diff_stat, tasks, runs)
    print(f"  Git commits: {len(git_log.splitlines())}")
    print(f"  Tasks: {len(tasks)} ({sum(1 for t in tasks if t.get('status') == 'completed')} completed)")
    print(f"  Runs: {len(runs)}")

    print(f"\nQuerying {args.model}...")
    response = query_ollama(args.model, prompt)

    if not response:
        print("No response from model.")
        return

    suggestions = parse_suggestions(response)
    if not suggestions:
        return

    display_suggestions(suggestions)

    if args.apply:
        apply_suggestions(suggestions, tasks)
    else:
        print("  Run with --apply to add these tasks to the queue.")


if __name__ == "__main__":
    main()
