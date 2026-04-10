#!/usr/bin/env python3
"""
Third Brother Autonomous Driver v3 — Scout + Classification Architecture
=========================================================================
Third Brother drives Claude Code via `claude -p --resume <session-id>`.
No tmux. No worktrees. No signal parsing. Just structured JSON I/O.

v3 adds: task classification, read-only scout agent for debug tasks,
per-type tool routing, and shadow log enrichment (raft_v3 format).

Design spec: .brain/artifacts/architecture/DRIVER_V2_PHASE0_FINAL.md

Usage:
    python3 scripts/third_brother_driver.py --session <id>            # supervised (default)
    python3 scripts/third_brother_driver.py --session <id> --auto     # autonomous
    python3 scripts/third_brother_driver.py --add-task                # add a task interactively
    python3 scripts/third_brother_driver.py --list-tasks              # show task queue
    python3 scripts/third_brother_driver.py --trust-status            # show trust ladder phase
    python3 scripts/third_brother_driver.py --dry-run --session <id>  # validate pipeline
    python3 scripts/third_brother_driver.py --validate-shadow-log    # audit shadow_log entries
"""

import fnmatch
import json
import re
import subprocess
import sys
import os
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# ── Global flags ─────────────────────────────────────────────
VERBOSE = False  # Set by --verbose; logs every Ollama call's input/output

# Ensure scripts/ is importable for driver_config
sys.path.insert(0, str(Path(__file__).resolve().parent))

# ── Paths (shared via driver_config, re-exported for test patching) ──
from driver_config import (
    PROJECT_ROOT, BRAIN_PATH, DRIVER_DIR, CONFIG_PATH, TASKS_PATH,
    STATE_PATH, STOP_FILE, ALERTS_PATH, RUNS_PATH, VERIFICATION_LOG_PATH,
    MANIFEST_PATH, DEFAULT_CONFIG, load_config as _load_config_shared,
)
SHADOW_LOG_PATH = DRIVER_DIR / "shadow_log.jsonl"
SHADOW_LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOCKS_DIR = DRIVER_DIR / ".locks"
OLLAMA_LOG_PATH = DRIVER_DIR / "ollama_calls.jsonl"

# Add project root for providers import
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "mcp-server-nucleus" / "src"))


# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════

def load_config() -> Dict:
    """Load driver configuration."""
    return _load_config_shared(CONFIG_PATH, DEFAULT_CONFIG)


# ═══════════════════════════════════════════════════════════════
# FLYWHEEL HOOKS — best-effort accountability for every phase
# ═══════════════════════════════════════════════════════════════

def _flywheel_enabled(config: Dict) -> bool:
    """Check if flywheel accountability is on. Defaults to True."""
    return bool(config.get("flywheel_accountability_enabled", True))


def _fw_record_survived(phase: str, step: str, config: Dict) -> None:
    """Phase succeeded — bump CSR. Never raises."""
    if not _flywheel_enabled(config):
        return
    try:
        from mcp_server_nucleus.flywheel import Flywheel
        Flywheel(BRAIN_PATH).record_survived(phase=phase, step=step)
    except Exception as e:
        # Flywheel is best-effort. Log to stderr and move on; never block driver.
        print(f"[FLYWHEEL] survived hook skipped ({phase}/{step}): {e}", file=sys.stderr)


def _fw_file_ticket(phase: str, step: str, error: str, config: Dict,
                    logs: str = "") -> None:
    """Phase failed — file a ticket. Never raises."""
    if not _flywheel_enabled(config):
        return
    try:
        from mcp_server_nucleus.flywheel import Flywheel
        Flywheel(BRAIN_PATH).file_ticket(
            step=step, error=error, logs=logs, phase=phase)
    except Exception as e:
        # See mentor.md: never write the flywheel's own failures back to itself.
        print(f"[FLYWHEEL] ticket hook skipped ({phase}/{step}): {e}", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════
# STATE PERSISTENCE
# ═══════════════════════════════════════════════════════════════

def save_state(phase: str, task: Optional[Dict] = None,
               session_id: str = "", context_metrics: Optional[Dict] = None):
    """Persist current driver state to disk."""
    data = {
        "phase": phase,
        "task_id": task["id"] if task else None,
        "session_id": session_id,
        "updated_at": datetime.now().isoformat(),
    }
    if context_metrics:
        data["session_turns"] = context_metrics.get("turns", 0)
        data["session_bytes"] = context_metrics.get("bytes", 0)
        data["context_pressure_pct"] = context_metrics.get("pressure_pct", 0)
    STATE_PATH.write_text(json.dumps(data, indent=2))


# ═══════════════════════════════════════════════════════════════
# SESSION CONTEXT MANAGEMENT (Auto-Compact)
# ═══════════════════════════════════════════════════════════════

def monitor_session_context(session_id: str) -> dict:
    """Read session JSONL file directly to measure context pressure.

    Returns {"turns": int, "bytes": int, "pressure_pct": int}.
    Safe default on any failure — never crashes the driver.
    """
    if not session_id:
        return {"turns": 0, "bytes": 0, "pressure_pct": 0}
    try:
        claude_projects = Path.home() / ".claude" / "projects"
        if not claude_projects.exists():
            return {"turns": 0, "bytes": 0, "pressure_pct": 0}
        for proj_dir in claude_projects.iterdir():
            if not proj_dir.is_dir():
                continue
            session_file = proj_dir / f"{session_id}.jsonl"
            if session_file.exists():
                file_bytes = session_file.stat().st_size
                turns = sum(1 for _ in open(session_file, "r", errors="ignore"))
                # 5MB of JSONL ≈ 150K tokens — treat as effective ceiling
                pressure_pct = min(100, int(file_bytes / (5 * 1024 * 1024) * 100))
                return {"turns": turns, "bytes": file_bytes, "pressure_pct": pressure_pct}
    except (IOError, OSError, PermissionError):
        pass
    return {"turns": 0, "bytes": 0, "pressure_pct": 0}


def compact_session(session_id: str, branch: str, config: dict) -> str:
    """Run a 1-turn summary call on the session, return handoff text."""
    summary_path = DRIVER_DIR / config.get("compact_summary_path", "session_summary.md")

    # Get git log for concrete work record
    git_log = ""
    try:
        git_log = subprocess.run(
            ["git", "log", "--oneline", "-20"],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT)
        ).stdout.strip()
    except Exception:
        pass

    # Ask Claude to summarize the session
    compact_prompt = (
        f"Summarize everything you've done on branch {branch or 'current'}. "
        "Include: files modified, key decisions made, tests status, what's left to do. "
        "Be concise — 5-10 bullet points max."
    )
    claude_model = config.get("claude_model", "")
    cmd = [
        "claude", "-p", compact_prompt,
        "--output-format", "json",
        "--max-turns", "1",
        "--effort", "low",
    ]
    if claude_model:
        cmd.extend(["--model", claude_model])
    if session_id:
        cmd.extend(["--resume", session_id])

    summary = ""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if result.stdout.strip():
            try:
                parsed = json.loads(result.stdout)
                summary = parsed.get("result", result.stdout.strip())
            except json.JSONDecodeError:
                summary = result.stdout.strip()
    except Exception as e:
        print(f"[COMPACT] Summary call failed: {e}")

    if not summary:
        summary = f"Session {session_id[:12]} — see git log for details"

    # Combine summary + git log
    handoff = f"## Session Summary\n{summary}\n\n## Recent Git Log\n{git_log}"

    # Persist for reference
    try:
        summary_path.write_text(handoff)
    except Exception:
        pass

    return handoff


def rotate_with_handoff(session_id: str, branch: str, config: dict) -> tuple:
    """Compact current session, return ('', handoff_summary)."""
    print(f"[COMPACT] Compacting session {session_id[:12]}...")
    summary = compact_session(session_id, branch, config)

    # Append session state if it exists
    state_path = DRIVER_DIR / config.get("session_state_path", "session_state.md")
    if state_path.exists():
        try:
            state_text = state_path.read_text()
            summary += f"\n\n{state_text}"
        except Exception:
            pass

    print(f"[COMPACT] Handoff ready ({len(summary.split())} words). Rotating to fresh session.")
    return ("", summary)


def write_session_state(session_id: str, branch: str, completed_tasks: list,
                        config: dict):
    """Write persistent session notes for rotation handoff."""
    state_path = DRIVER_DIR / config.get("session_state_path", "session_state.md")
    lines = [f"# Session: {session_id[:12] if session_id else 'fresh'}\n",
             f"Branch: {branch or 'main'}\n\n"]
    for t in completed_tasks[-10:]:
        lines.append(f"- [{t.get('status', '?')}] {t.get('id', '?')}: "
                     f"{t.get('title', 'untitled')}\n")
    content = "".join(lines)
    # Cap at ~2000 words
    words = content.split()
    if len(words) > 2000:
        content = " ".join(words[:2000])
    try:
        state_path.write_text(content)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# TASK MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def load_tasks() -> List[Dict]:
    """Load all tasks from the task file."""
    if not TASKS_PATH.exists():
        return []
    data = json.loads(TASKS_PATH.read_text())
    return data.get("tasks", [])


def save_tasks(tasks: List[Dict]):
    """Write tasks back to the task file."""
    data = {
        "tasks": tasks,
        "schema_version": 1,
        "updated_at": datetime.now().isoformat(),
    }
    TASKS_PATH.write_text(json.dumps(data, indent=2))


def pick_next_task() -> Optional[Dict]:
    """Pick the highest-priority committed task."""
    tasks = load_tasks()
    committed = [t for t in tasks if t.get("status") == "committed"]
    if not committed:
        return None
    # Sort by priority (lower = higher priority), then by creation time
    committed.sort(key=lambda t: (t.get("priority", 99), t.get("created_at", "")))
    return committed[0]


def update_task_status(task_id: str, status: str, **extra):
    """Update a task's status in the task file."""
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = status
            if status == "completed":
                t["completed_at"] = datetime.now().isoformat()
            for k, v in extra.items():
                t[k] = v
            break
    save_tasks(tasks)


def add_task(title: str, description: str, scope: List[str],
             priority: int = 5, max_turns: int = 30,
             plan_file: str = "") -> Dict:
    """Add a new task to the queue."""
    tasks = load_tasks()

    # Generate ID
    existing_ids = [t["id"] for t in tasks]
    n = 1
    while f"task-{n:03d}" in existing_ids:
        n += 1
    task_id = f"task-{n:03d}"

    task = {
        "id": task_id,
        "title": title,
        "description": description,
        "scope": scope,
        "priority": priority,
        "status": "committed",
        "max_turns": max_turns,
        "plan_file": plan_file,
        "assigned_to": "third-brother-driver-v2",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "failure_reason": None,
    }
    tasks.append(task)
    save_tasks(tasks)
    return task


# ═══════════════════════════════════════════════════════════════
# KILL SWITCH
# ═══════════════════════════════════════════════════════════════

def check_kill_switch() -> bool:
    """Check if the kill switch file exists."""
    return STOP_FILE.exists()


# ═══════════════════════════════════════════════════════════════
# LOCKING (BrainLock from Nucleus)
# ═══════════════════════════════════════════════════════════════

def get_driver_lock():
    """Get a BrainLock for the driver session."""
    try:
        from mcp_server_nucleus.daemon.safety.lock import BrainLock
        lock_file = str(LOCKS_DIR / "driver_session.lock")
        return BrainLock(lock_file, timeout=2)
    except ImportError:
        # Fallback: simple fcntl lock if mcp-server-nucleus not importable
        return _FallbackLock(str(LOCKS_DIR / "driver_session.lock"))


class _FallbackLock:
    """Minimal fcntl lock if BrainLock import fails."""

    def __init__(self, lock_file: str):
        import fcntl
        self.lock_file = lock_file
        self.fd = None
        self._fcntl = fcntl
        os.makedirs(os.path.dirname(lock_file), exist_ok=True)

    def acquire(self) -> bool:
        try:
            self.fd = open(self.lock_file, 'w')
            self._fcntl.flock(self.fd, self._fcntl.LOCK_EX | self._fcntl.LOCK_NB)
            self.fd.write(str(os.getpid()))
            self.fd.flush()
            return True
        except (IOError, OSError):
            if self.fd:
                self.fd.close()
                self.fd = None
            return False

    def release(self):
        if self.fd:
            self._fcntl.flock(self.fd, self._fcntl.LOCK_UN)
            self.fd.close()
            self.fd = None

    def guard(self):
        from contextlib import contextmanager

        @contextmanager
        def _guard():
            if not self.acquire():
                raise TimeoutError("Could not acquire driver lock")
            try:
                yield
            finally:
                self.release()

        return _guard()


# ═══════════════════════════════════════════════════════════════
# GIT HELPERS
# ═══════════════════════════════════════════════════════════════

def git(*args) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT), timeout=30,
    )
    return result.stdout.strip()


def snapshot_working_tree() -> set:
    """Capture current file modification state for diffing."""
    status = git("status", "--porcelain")
    return set(status.strip().splitlines()) if status.strip() else set()


def capture_staged_files() -> set:
    """Return filenames currently in the git staging area."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True, timeout=10,
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode == 0 and result.stdout.strip():
        return set(result.stdout.strip().splitlines())
    return set()


def _file_matches_scope(filepath: str, scope: List[str]) -> bool:
    """Check if a filepath matches any of the task's scope globs."""
    for pattern in scope:
        if pattern == "**":
            return True
        if fnmatch.fnmatch(filepath, pattern):
            return True
        # Support directory prefixes: "backend/app/**" matches "backend/app/main.py"
        if pattern.endswith("/**") and filepath.startswith(pattern[:-3]):
            return True
        # Support bare directory: "backend/app" matches "backend/app/main.py"
        if not any(c in pattern for c in "*?[") and filepath.startswith(pattern.rstrip("/") + "/"):
            return True
    return False


def check_scope_violations(git_diff: str, scope: List[str]) -> List[str]:
    """Parse git diff --stat output and return files outside scope."""
    if not git_diff or scope == ["**"]:
        return []
    violations = []
    for line in git_diff.strip().splitlines():
        # git diff --stat format: " path/to/file | 5 ++-"
        line = line.strip()
        if "|" not in line:
            continue
        filepath = line.split("|")[0].strip()
        if not filepath or filepath.startswith("("):
            continue
        if not _file_matches_scope(filepath, scope):
            violations.append(filepath)
    return violations


def auto_commit(task: Dict, pre_snapshot: set = None, pre_staged: set = None):
    """Commit only files changed by the Claude Code session."""
    post = snapshot_working_tree()
    if pre_snapshot is None:
        pre_snapshot = set()

    # Files that appeared or changed AFTER the session ran
    new_changes = post - pre_snapshot
    if not new_changes:
        print("[DRIVER] No changes to commit.")
        return

    # Extract filenames from porcelain output (format: "XY filename" or "XY old -> new")
    files_to_stage = []
    for line in new_changes:
        parts = line.strip().split(None, 1)
        if len(parts) >= 2:
            fname = parts[1].split(" -> ")[-1].strip('"')
            files_to_stage.append(fname)

    if not files_to_stage:
        print("[DRIVER] No changes to commit.")
        return

    # Scope-filter: only stage files within task scope
    scope = task.get("scope", ["**"])
    if scope != ["**"]:
        in_scope = [f for f in files_to_stage if _file_matches_scope(f, scope)]
        out_of_scope = [f for f in files_to_stage if f not in in_scope]
        if out_of_scope:
            print(f"[DRIVER] Scope filter: skipping {len(out_of_scope)} out-of-scope file(s): "
                  f"{', '.join(out_of_scope[:5])}")
        files_to_stage = in_scope
        if not files_to_stage:
            print("[DRIVER] No in-scope changes to commit.")
            return

    for f in files_to_stage:
        subprocess.run(["git", "add", f], capture_output=True, cwd=str(PROJECT_ROOT))
    print(f"[DRIVER] Staged {len(files_to_stage)} file(s): {', '.join(files_to_stage[:5])}")

    # ── GROUND coherence: unstage pre-existing files ──
    # The model or prior work may have left files staged. We must not
    # include them in this task's commit.
    if pre_staged is None:
        try:
            manifest = json.loads(MANIFEST_PATH.read_text())
            pre_staged = set(manifest.get("pre_staged_files", []))
        except Exception:
            pre_staged = set()

    if pre_staged:
        staged_now_result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        staged_now = set(staged_now_result.stdout.strip().splitlines()) if staged_now_result.stdout.strip() else set()
        contaminants = (pre_staged & staged_now) - set(files_to_stage)
        if contaminants:
            print(f"[GROUND] Unstaging {len(contaminants)} pre-existing file(s) to prevent commit contamination")
            for f in sorted(contaminants):
                subprocess.run(["git", "restore", "--staged", f],
                               capture_output=True, cwd=str(PROJECT_ROOT))

    msg = f"tb: {task['title']}\n\nTask: {task['id']}\nDriver: third-brother-v2"
    result = subprocess.run(
        ["git", "commit", "-m", msg],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT), timeout=30,
    )
    if result.returncode == 0:
        short_hash = git("log", "--oneline", "-1")
        print(f"[DRIVER] Committed: {short_hash}")
        # Clean up session manifest after successful commit
        try:
            MANIFEST_PATH.unlink(missing_ok=True)
        except Exception:
            pass
    else:
        print(f"[DRIVER] Commit failed: {result.stderr[:200]}")


# ═══════════════════════════════════════════════════════════════
# CRASH RECOVERY
# ═══════════════════════════════════════════════════════════════

def recover_stale_tasks():
    """Reset in_progress tasks from a crashed run."""
    tasks = load_tasks()
    recovered = 0
    for task in tasks:
        if task["status"] == "in_progress":
            # Did the auto-commit happen?
            recent_log = git("log", "--oneline", "-10", "--grep", f"tb: {task['title']}")
            if recent_log.strip():
                update_task_status(task["id"], "completed")
                print(f"[RECOVERY] {task['id']} — commit found, marking completed")
            else:
                update_task_status(task["id"], "committed")
                print(f"[RECOVERY] {task['id']} — no commit, resetting to retry")
            recovered += 1
    if recovered:
        print(f"[RECOVERY] Recovered {recovered} stale task(s).")


# ═══════════════════════════════════════════════════════════════
# TASK TEMPLATE
# ═══════════════════════════════════════════════════════════════

TASK_TEMPLATE = """## Task: {title}

{description}

## Context from .brain
{context}

## Constraints
- Write code directly. No need to create branches or PRs.
- Only modify files in: {scope}
- Run tests if applicable before considering the task done.
- When done, output a brief summary starting with which context documents above were relevant (quote key passages), then describe what you changed and why.
- If you're stuck, describe the blocker clearly.

## Scope
{scope_list}
"""

SCOUT_TEMPLATE = """## Investigation: {title}

{description}

## Context from .brain
{context}

## Instructions
You are a scout. Investigate this issue thoroughly but do NOT fix it.

Find:
1. Affected files with exact line numbers
2. Root cause (trace through the code, don't guess)
3. Error traces or reproduction steps
4. Related code patterns that might be affected

Return your findings as a structured summary with:
- FILES: list of file:line references
- ROOT_CAUSE: one paragraph explaining the root cause
- HYPOTHESES: 2-3 approaches to fix this
- ERROR_TRACE: relevant error output or stack traces

Be specific. File paths and line numbers matter more than explanations.
"""


# ═══════════════════════════════════════════════════════════════
# TASK CLASSIFICATION (v3 Phase A)
# ═══════════════════════════════════════════════════════════════

# Keywords that signal task type
_DEBUG_KEYWORDS = frozenset({"fix", "bug", "error", "broken", "failing", "crash",
                              "debug", "issue", "regression", "wrong", "incorrect"})
_INVESTIGATE_KEYWORDS = frozenset({"investigate", "trace", "why", "understand",
                                    "diagnose", "analyze", "root cause", "find out"})
_REFACTOR_KEYWORDS = frozenset({"refactor", "reorganize", "restructure", "clean up",
                                 "simplify", "extract", "consolidate", "rename"})

# Tool sets per task type
_TOOLS_BY_TYPE = {
    "build":       "Bash,Read,Edit,Write,Glob,Grep",
    "debug":       "Bash,Read,Edit,Write,Glob,Grep,Agent",
    "investigate": "Bash,Read,Glob,Grep,WebSearch",
    "refactor":    "Bash,Read,Edit,Write,Glob,Grep",
}

# Max turns per task type
_TURNS_BY_TYPE = {
    "build": 30,
    "debug": 40,
    "investigate": 20,
    "refactor": 30,
}


def classify_task(task: Dict, config: Dict) -> Dict:
    """Classify a task by type and determine tools/turns/scout needs.

    Phase A: rule-based heuristic using keywords.
    Phase E (future): Ollama classification.

    Returns:
        {"type": "build|debug|investigate|refactor",
         "needs_scout": bool,
         "max_turns": int,
         "tools": str,
         "confidence": float}
    """
    v3 = config.get("v3_features", {})
    if not v3.get("classification_enabled", False):
        # v3 disabled — return v2 defaults
        return {
            "type": "build",
            "needs_scout": False,
            "max_turns": task.get("max_turns", config.get("claude_max_turns", 30)),
            "tools": "Bash,Read,Edit,Write,Glob,Grep",
            "confidence": 1.0,
        }

    text = f"{task.get('title', '')} {task.get('description', '')}".lower()
    words = set(text.split())

    # Check keywords (order matters: debug > investigate > refactor > build)
    task_type = "build"
    confidence = 0.6  # default for build (most common)

    if words & _DEBUG_KEYWORDS or any(kw in text for kw in _DEBUG_KEYWORDS):
        task_type = "debug"
        confidence = 0.8
    elif words & _INVESTIGATE_KEYWORDS or any(kw in text for kw in _INVESTIGATE_KEYWORDS):
        task_type = "investigate"
        confidence = 0.8
    elif words & _REFACTOR_KEYWORDS or any(kw in text for kw in _REFACTOR_KEYWORDS):
        task_type = "refactor"
        confidence = 0.7

    # Scout needed for debug and investigate tasks
    needs_scout = task_type in ("debug", "investigate") and v3.get("scout_enabled", False)

    # Scout turns scaled by scope breadth:
    #   narrow scope (1 file/dir) = fewer turns, bug is localized
    #   broad scope (3+ dirs or **) = more turns, need to trace across boundaries
    scope = task.get("scope", ["**"])
    scope_breadth = len(scope)
    if scope_breadth <= 1 and scope != ["**"]:
        scout_turns = v3.get("scout_max_turns_narrow", 8)
    elif scope_breadth <= 3:
        scout_turns = v3.get("scout_max_turns", 12)
    else:
        scout_turns = v3.get("scout_max_turns_wide", 18)

    # Override tools from config if present
    tools_key = f"executor_tools_{task_type}"
    tools = v3.get(tools_key, _TOOLS_BY_TYPE.get(task_type, _TOOLS_BY_TYPE["build"]))

    # Override max_turns from task or config
    max_turns = task.get("max_turns") or _TURNS_BY_TYPE.get(task_type, 30)

    result = {
        "type": task_type,
        "needs_scout": needs_scout,
        "max_turns": max_turns,
        "tools": tools,
        "confidence": confidence,
        "scout_turns": scout_turns,
    }
    print(f"[CLASSIFY] {task.get('id', '?')}: type={task_type}, "
          f"needs_scout={needs_scout}, scout_turns={scout_turns}, tools={tools}")
    return result


# ═══════════════════════════════════════════════════════════════
# SCOUT AGENT (v3 Phase B)
# ═══════════════════════════════════════════════════════════════

INVESTIGATION_LOG_PATH = DRIVER_DIR / "investigation_log.jsonl"


def run_scout_agent(task: Dict, context: str, config: Dict,
                    scout_turns_override: Optional[int] = None,
                    session_id: str = "") -> Dict:
    """Dispatch a read-only Claude Code agent to investigate a task.

    When session_id is provided and scout_on_main_session is enabled,
    scout runs on the main session — findings stay in conversation history.
    Returns structured findings dict. Returns empty dict on failure.
    """
    v3 = config.get("v3_features", {})
    scout_max_turns = scout_turns_override or v3.get("scout_max_turns", 12)
    scout_timeout = v3.get("scout_timeout_minutes", 5) * 60
    scout_tools = v3.get("scout_tools", "Bash,Read,Glob,Grep")
    effort = config.get("claude_effort", "max")

    scope_str = ", ".join(task.get("scope", ["**"]))
    scout_prompt = SCOUT_TEMPLATE.format(
        title=task["title"],
        description=task["description"],
        context=context or "(no RAG context available)",
        scope=scope_str,
    )

    scout_on_main = bool(session_id and config.get("scout_on_main_session", True))
    cmd = [
        "claude", "-p", scout_prompt,
        "--output-format", "json",
        "--max-turns", str(scout_max_turns),
        "--effort", effort,
        "--allowedTools", scout_tools,
    ]
    if scout_on_main:
        cmd.extend(["--resume", session_id])

    print(f"[SCOUT] Investigating {task.get('id', '?')} (max {scout_max_turns} turns, "
          f"timeout {scout_timeout}s)...")
    t0 = time.time()

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=scout_timeout,
        )
        duration_ms = int((time.time() - t0) * 1000)

        findings = {}
        if result.stdout.strip():
            try:
                parsed = json.loads(result.stdout)
                # Extract result text from Claude's JSON output
                result_text = parsed.get("result", result.stdout)
                findings = {
                    "raw": result_text[:3000] if isinstance(result_text, str) else str(result_text)[:3000],
                    "turns": parsed.get("num_turns", 0),
                }
            except json.JSONDecodeError:
                findings = {"raw": result.stdout[:3000], "turns": 0}

        findings["duration_ms"] = duration_ms
        findings["task_id"] = task.get("id", "")

        print(f"[SCOUT] Done: {duration_ms}ms, {findings.get('turns', 0)} turns")

        # Log investigation
        log_entry = {
            "ts": datetime.now().isoformat(),
            "task_id": task.get("id", ""),
            "scout_duration_ms": duration_ms,
            "scout_turns": findings.get("turns", 0),
            "findings_length": len(findings.get("raw", "")),
        }
        with open(INVESTIGATION_LOG_PATH, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        return findings

    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - t0) * 1000)
        print(f"[SCOUT] Timeout after {duration_ms}ms")
        return {"raw": "", "turns": 0, "duration_ms": duration_ms, "error": "timeout"}
    except Exception as e:
        print(f"[SCOUT] Error: {e}")
        return {"raw": "", "turns": 0, "duration_ms": 0, "error": str(e)}


# ═══════════════════════════════════════════════════════════════
# OLLAMA HTTP API
# ═══════════════════════════════════════════════════════════════

OLLAMA_API_URL = "http://localhost:11434/api/generate"


def _ollama_generate(prompt: str, model: str, timeout: int = 60,
                     num_predict: int = 300, temperature: float = 0.7) -> tuple:
    """Call Ollama via HTTP API (not CLI subprocess). Returns (response_text, duration_ms).

    Uses the same pattern proven in tb_sparring.py. HTTP API is faster than
    subprocess (no process fork) and doesn't include model loading in timeout.
    """
    import urllib.request

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": num_predict, "temperature": temperature},
    }).encode()

    req = urllib.request.Request(
        OLLAMA_API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            duration_ms = int((time.time() - t0) * 1000)
            return data.get("response", "").strip(), duration_ms
    except Exception as e:
        duration_ms = int((time.time() - t0) * 1000)
        print(f"[OLLAMA] Error after {duration_ms}ms: {type(e).__name__}: {e}")
        return None, duration_ms


def _ollama_warmup(model: str):
    """Send a trivial prompt to force model loading before real work."""
    text, ms = _ollama_generate("Reply OK", model, timeout=30, num_predict=5)
    if text:
        print(f"[OLLAMA] Model {model} warmed up ({ms}ms)")
    else:
        print(f"[OLLAMA] Warmup failed — cold starts may cause timeouts")


# ═══════════════════════════════════════════════════════════════
# TB PROMPT WRITER (v3 Phase C)
# ═══════════════════════════════════════════════════════════════

def tb_write_enriched_prompt(task: Dict, context: str,
                              scout_findings: Dict, config: Dict) -> Optional[str]:
    """Call TB via Ollama to write an enriched executor prompt.

    Returns the enriched prompt string, or None if TB is unavailable/fails
    (caller should fall back to TASK_TEMPLATE).
    """
    v3 = config.get("v3_features", {})
    if not v3.get("tb_prompt_writer_enabled", False):
        return None

    tb_model = os.environ.get("TB_MODEL") or v3.get("tb_model", "third-brother:latest")
    timeout = v3.get("tb_prompt_timeout_seconds", 180)

    scout_text = scout_findings.get("raw", "") if scout_findings else ""

    ollama_prompt = f"""You are Third Brother, the project manager for the Nucleus codebase.
Write a detailed instruction (300-500 words) for Claude Code to execute this task.

Task: {task.get('title', '')}
Description: {task.get('description', '')}

Brain Context (from RAG):
{context[:2000]}

Scout Investigation Findings:
{scout_text[:2000] if scout_text else '(no scout run)'}

Your instruction must include:
- Specific file paths and line numbers from scout findings
- Root cause analysis (what is broken and why)
- Recommended approach (not just "fix it")
- Constraints (scope, files to modify, files NOT to modify)
- How to verify the fix works

Write the instruction now:"""

    task_id = task.get("id", "")
    print(f"[TB] Generating enriched prompt via {tb_model}...")

    response_text, duration_ms = _ollama_generate(
        ollama_prompt, tb_model, timeout=600, num_predict=300)

    log_ollama_call("TB", tb_model, ollama_prompt, response_text or "",
                    0 if response_text else -1, duration_ms, "", task_id)

    if not response_text:
        print(f"[TB] Ollama failed after {duration_ms}ms, falling back to template")
        return None

    if len(response_text) < 50:
        print(f"[TB] Prompt too short ({len(response_text)} chars), falling back to template")
        return None

    word_count = len(response_text.split())
    print(f"[TB] Generated {word_count}-word enriched prompt ({duration_ms}ms)")
    return response_text


# ═══════════════════════════════════════════════════════════════
# INLINE SPARRING (live training data from real work)
# ═══════════════════════════════════════════════════════════════

SPARRING_DPO_PATH = Path(__file__).resolve().parent.parent / ".brain" / "training" / "inbox" / "sparring_dpo.jsonl"
SPARRING_SFT_PATH = Path(__file__).resolve().parent.parent / ".brain" / "training" / "inbox" / "sparring_sft.jsonl"


def _spar_phase_cd(task: Dict, executor_result: Dict, review: Dict, config: Dict):
    """Score TB's Phase C prompt and Phase D review — produce DPO pairs from real work.

    This runs inline during branch mode. Every task TB works on
    becomes training data regardless of outcome.
    """
    try:
        # Get TB's prompt from the executor result (if it was stored)
        tb_prompt_used = executor_result.get("tb_prompt", "")
        if not tb_prompt_used:
            # Fallback: evaluate the template-assembled prompt (weaker signal but non-zero)
            tb_prompt_used = executor_result.get("message", "")
            if not tb_prompt_used:
                return

        task_desc = f"{task.get('title', '')} — {task.get('description', '')}"

        # Load verification stats for calibration context
        _cal_window = config.get("calibration_window_size", 50)
        _vstats = load_verification_stats(_cal_window)
        _cal_block = ""
        if _vstats["total"] > 0:
            _cal_block = (
                f"\nCALIBRATION: In last {_vstats['total']} tasks, GROUND verification passed "
                f"{_vstats['accuracy']:.0%} of the time. {_vstats['calibration_dpo_count']} calibration "
                f"DPO pairs were generated from false \"done\" declarations.\n"
                f"Penalize overcalibrated confidence. TB should learn honest uncertainty.\n"
            )

        git_diff = executor_result.get("git_diff", "")
        eval_prompt = f"""Score Third Brother's instruction. DO NOT read any files.

TASK: {task_desc[:500]}

TB OUTPUT: {tb_prompt_used[:800]}

TB REVIEW VERDICT: {review.get('verdict', '?')} — {review.get('reason', '')[:200]}

EXECUTOR RESULT: {str(executor_result.get('result', ''))[:500]}

GIT DIFF: {git_diff[:500]}
{_cal_block}
Reply with ONLY this JSON:
{{"score": 1-5, "hallucinations": ["items"], "confidence_correct": true/false, "reason": "one sentence", "correction": "DO: ...\\nWHERE: ...\\nDONT TOUCH: ...\\nVERIFY: ...\\nCONFIDENCE: ..."}}"""

        result = subprocess.run(
            ["claude", "-p", eval_prompt,
             "--output-format", "text",
             "--max-turns", "1",
             "--allowedTools", ""],
            capture_output=True, text=True, timeout=90,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return

        # Parse JSON from response
        raw = result.stdout.strip()
        idx = raw.find('{')
        if idx < 0:
            return
        brace_count = 0
        for i in range(idx, len(raw)):
            if raw[i] == '{':
                brace_count += 1
            elif raw[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    try:
                        eval_data = json.loads(raw[idx:i + 1])
                    except json.JSONDecodeError:
                        return
                    break
        else:
            return

        score = eval_data.get("score", 0)
        correction = eval_data.get("correction", "")
        confidence_correct = eval_data.get("confidence_correct")

        sys_msg = ("You are Third Brother, project manager for the Nucleus codebase. "
                   "When given a task, write a short, actionable instruction for Claude Code "
                   "in structured format: DO, WHERE, DONT TOUCH, VERIFY, CONFIDENCE.")

        prompt_msgs = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": f"Task: {task_desc}"},
        ]

        if score < 4 and correction:
            # DPO pair: TB output rejected, Claude correction chosen
            dpo_entry = {
                "prompt": prompt_msgs,
                "chosen": [{"role": "assistant", "content": correction}],
                "rejected": [{"role": "assistant", "content": tb_prompt_used[:1000]}],
                "metadata": {
                    "source": "tb_sparring_live",
                    "task_id": task.get("id", ""),
                    "score": score,
                    "confidence_correct": confidence_correct,
                    "ts": datetime.now().isoformat(),
                }
            }
            with open(SPARRING_DPO_PATH, "a") as f:
                f.write(json.dumps(dpo_entry) + "\n")

        # SFT entry: best available response
        best_response = correction if (score < 4 and correction) else tb_prompt_used
        sft_entry = {
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": f"Task: {task_desc}"},
                {"role": "assistant", "content": best_response[:1500]},
            ],
            "metadata": {
                "source": "tb_sparring_live",
                "task_id": task.get("id", ""),
                "original_score": score,
                "category": "instruction_writing",
                "quality": "gold" if score >= 4 else "silver",
                "ts": datetime.now().isoformat(),
            }
        }
        with open(SPARRING_SFT_PATH, "a") as f:
            f.write(json.dumps(sft_entry) + "\n")

        print(f"[SPARRING] Phase C scored {score}/5 — "
              f"{'DPO pair' if score < 4 else 'positive SFT'} saved")

        # ── Phase D: Review quality sparring ──
        # Score TB's review verdict — does it catch real issues or rubber-stamp?
        if config.get("training_capture_review_dpo", True) and review.get("verdict"):
            tb_review_text = (f"VERDICT: {review.get('verdict', '?')}\n"
                              f"REASON: {review.get('reason', '')}\n"
                              f"NOTES: {review.get('deepen_notes', '')}")

            review_eval_prompt = f"""Score Third Brother's REVIEW quality. DO NOT read any files.

TASK: {task_desc[:500]}

EXECUTOR RESULT: {str(executor_result.get('result', ''))[:500]}

GIT DIFF: {git_diff[:500]}

TB REVIEW: {tb_review_text}
{_cal_block}
Was the review correct? Did TB catch real issues or rubber-stamp?
Reply with ONLY this JSON:
{{"review_score": 1-5, "verdict_correct": true, "should_be": "ACCEPT/DEEPEN/ESCALATE", "reason": "one sentence", "better_review": "VERDICT: ...\\nREASON: ...\\nNOTES: ..."}}"""

            review_eval_result = subprocess.run(
                ["claude", "-p", review_eval_prompt,
                 "--output-format", "text",
                 "--max-turns", "1",
                 "--allowedTools", ""],
                capture_output=True, text=True, timeout=90,
            )

            if review_eval_result.returncode == 0 and review_eval_result.stdout.strip():
                raw_d = review_eval_result.stdout.strip()
                idx_d = raw_d.find('{')
                if idx_d >= 0:
                    brace_d = 0
                    for i_d in range(idx_d, len(raw_d)):
                        if raw_d[i_d] == '{':
                            brace_d += 1
                        elif raw_d[i_d] == '}':
                            brace_d -= 1
                            if brace_d == 0:
                                try:
                                    rd = json.loads(raw_d[idx_d:i_d + 1])
                                except json.JSONDecodeError:
                                    rd = None
                                break
                    else:
                        rd = None

                    if rd:
                        review_score = rd.get("review_score", 0)
                        better_review = rd.get("better_review", "")
                        verdict_correct = rd.get("verdict_correct")

                        review_sys = ("You are Third Brother, reviewing work done by Claude Code. "
                                      "Respond with VERDICT, REASON, and NOTES.")
                        review_user = (f"Task: {task_desc[:300]}\n"
                                       f"Executor result: {str(executor_result.get('result', ''))[:300]}\n"
                                       f"Git diff: {git_diff[:300]}")

                        if review_score < 4 and better_review:
                            # DPO pair: TB's review rejected, Claude's correction chosen
                            review_dpo = {
                                "prompt": [
                                    {"role": "system", "content": review_sys},
                                    {"role": "user", "content": review_user},
                                ],
                                "chosen": [{"role": "assistant", "content": better_review}],
                                "rejected": [{"role": "assistant", "content": tb_review_text}],
                                "metadata": {
                                    "source": "tb_review_sparring",
                                    "task_id": task.get("id", ""),
                                    "review_score": review_score,
                                    "verdict_correct": verdict_correct,
                                    "category": "review_quality",
                                    "ts": datetime.now().isoformat(),
                                }
                            }
                            with open(SPARRING_DPO_PATH, "a") as f:
                                f.write(json.dumps(review_dpo) + "\n")

                        # SFT entry for review quality
                        best_review = better_review if (review_score < 4 and better_review) else tb_review_text
                        review_sft = {
                            "messages": [
                                {"role": "system", "content": review_sys},
                                {"role": "user", "content": review_user},
                                {"role": "assistant", "content": best_review[:1500]},
                            ],
                            "metadata": {
                                "source": "tb_review_sparring",
                                "task_id": task.get("id", ""),
                                "original_score": review_score,
                                "category": "review_quality",
                                "quality": "gold" if review_score >= 4 else "silver",
                                "ts": datetime.now().isoformat(),
                            }
                        }
                        with open(SPARRING_SFT_PATH, "a") as f:
                            f.write(json.dumps(review_sft) + "\n")

                        print(f"[SPARRING] Phase D review scored {review_score}/5 — "
                              f"{'DPO pair' if review_score < 4 else 'positive SFT'} saved")

    except Exception as e:
        print(f"[SPARRING] Error (non-fatal): {e}")


SPARRING_TASK_BANK_PATH = Path(__file__).resolve().parent.parent / ".brain" / "training" / "sparring_task_bank.json"


# ── Verification metadata helpers (Frontier 1: GROUND) ──
def _verification_flag(response: Dict):
    """Extract execution_verified from response, or None."""
    v = response.get("verification")
    return v.get("verified") if v else None

def _verification_tier(response: Dict):
    """Extract highest verification tier reached, or None."""
    v = response.get("verification")
    return v.get("tier_reached") if v else None

def _verification_quality(response: Dict, base_quality: str) -> str:
    """Upgrade/downgrade quality based on verification result."""
    v = response.get("verification")
    if not v:
        return base_quality  # no verification ran
    if v.get("verified"):
        # Verified pass → promote to gold (if was silver or better)
        return "gold" if base_quality in ("gold", "silver") else base_quality
    else:
        # Verified fail → demote to copper
        return "copper"


def _capture_execution_dpo(task: Dict, response: Dict, git_diff_text: str, config: Dict):
    """Capture A: execution-grounded DPO pair.

    TB's raw instruction (rejected) vs a grounded instruction
    synthesized from what Claude actually did (chosen).
    """
    if not config.get("training_capture_execution_dpo", True):
        return
    try:
        tb_prompt = response.get("tb_prompt", "")
        result_text = response.get("result", "")
        # Need tb_prompt (what TB said) plus at least one evidence source
        if not tb_prompt:
            return
        if not git_diff_text.strip() and not result_text:
            return

        # Extract what Claude actually did from diff + result
        files_touched = [l.split("|")[0].strip()
                         for l in git_diff_text.split("\n")
                         if "|" in l and l.strip()]
        files_str = ", ".join(files_touched[:10]) if files_touched else "unknown"

        # Build grounded instruction from execution evidence
        evidence = result_text[:300] if result_text else f"Modified: {files_str}"
        grounded = (f"DO: {evidence}\n"
                    f"WHERE: {files_str}\n"
                    f"VERIFY: Check git diff confirms changes are correct\n"
                    f"CONFIDENCE: 0.9")

        sys_msg = ("You are Third Brother, project manager for the Nucleus codebase. "
                   "When given a task, write a short, actionable instruction for Claude Code "
                   "in structured format: DO, WHERE, DONT TOUCH, VERIFY, CONFIDENCE.")
        task_desc = f"{task.get('title', '')} — {task.get('description', '')}"

        dpo_entry = {
            "prompt": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": f"Task: {task_desc[:500]}"},
            ],
            "chosen": [{"role": "assistant", "content": grounded}],
            "rejected": [{"role": "assistant", "content": tb_prompt[:1000]}],
            "metadata": {
                "source": "driver_execution",
                "task_id": task.get("id", ""),
                "quality": _verification_quality(response, "silver"),
                "files_touched": files_touched[:5],
                "execution_verified": _verification_flag(response),
                "verification_tier_reached": _verification_tier(response),
                "ts": datetime.now().isoformat(),
            }
        }
        with open(SPARRING_DPO_PATH, "a") as f:
            f.write(json.dumps(dpo_entry) + "\n")
        print(f"[TRAINING] Capture A: execution-grounded DPO pair saved")

    except Exception as e:
        print(f"[TRAINING] Capture A error (non-fatal): {e}")


def _capture_deepen_dpo(task: Dict, pre_result: str, post_result: str,
                        deepen_notes: str, deepen_round: int):
    """Capture B: DEEPEN DPO pair.

    Pre-deepen output (rejected) vs post-deepen output (chosen).
    The deepen_notes ARE the preference signal.
    """
    try:
        if not pre_result or not post_result:
            return

        sys_msg = ("You are Third Brother, project manager for the Nucleus codebase. "
                   "Execute the task and address all review feedback.")
        task_desc = f"{task.get('title', '')} — {task.get('description', '')}"

        dpo_entry = {
            "prompt": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": f"Task: {task_desc[:500]}\n\nReview feedback: {deepen_notes[:300]}"},
            ],
            "chosen": [{"role": "assistant", "content": post_result[:1500]}],
            "rejected": [{"role": "assistant", "content": pre_result[:1500]}],
            "metadata": {
                "source": "driver_deepen",
                "task_id": task.get("id", ""),
                "deepen_round": deepen_round,
                "deepen_notes": deepen_notes[:200],
                "ts": datetime.now().isoformat(),
            }
        }
        with open(SPARRING_DPO_PATH, "a") as f:
            f.write(json.dumps(dpo_entry) + "\n")
        print(f"[TRAINING] Capture B: DEEPEN DPO pair (round {deepen_round}) saved")

    except Exception as e:
        print(f"[TRAINING] Capture B error (non-fatal): {e}")


def _capture_outcome_sft(task: Dict, response: Dict, outcome: str, config: Dict):
    """Capture D: outcome SFT entry — fires for ALL outcomes including failures."""
    if not config.get("training_capture_outcome_sft", True):
        return
    try:
        instruction = response.get("message", response.get("tb_prompt", ""))
        result_text = response.get("result", "")
        if not instruction or not result_text:
            return

        quality_map = {
            "completed": "gold" if response.get("tb_review", {}).get("verdict") == "ACCEPT" else "silver",
            "timeout": "copper",
            "error": "copper",
            "blocked": "copper",
            "session_exhausted": "copper",
        }

        sft_entry = {
            "messages": [
                {"role": "system", "content": "You are Third Brother, project manager for the Nucleus codebase."},
                {"role": "user", "content": instruction[:1500]},
                {"role": "assistant", "content": result_text[:2000]},
            ],
            "metadata": {
                "source": "driver_outcome",
                "task_id": task.get("id", ""),
                "outcome": outcome,
                "quality": _verification_quality(response, quality_map.get(outcome, "copper")),
                "category": "task_execution",
                "execution_verified": _verification_flag(response),
                "verification_tier_reached": _verification_tier(response),
                "ts": datetime.now().isoformat(),
            }
        }
        with open(SPARRING_SFT_PATH, "a") as f:
            f.write(json.dumps(sft_entry) + "\n")
        print(f"[TRAINING] Capture D: outcome SFT ({outcome}, {quality_map.get(outcome, 'copper')}) saved")

    except Exception as e:
        print(f"[TRAINING] Capture D error (non-fatal): {e}")


def _log_hard_negative(task: Dict, failure_mode: str, notes: str):
    """Log failed tasks as hard negatives in the sparring task bank."""
    try:
        entry = {
            "task": f"{task.get('description', '')}\n\nPrevious failure: {notes[:300]}",
            "has_file": bool(task.get("scope")),
            "source": "hard_negative",
            "original_task_id": task.get("id", ""),
            "failure_mode": failure_mode,
            "added_at": datetime.now().isoformat(),
        }
        with open(SPARRING_TASK_BANK_PATH, "r") as f:
            bank = json.load(f)
        bank.append(entry)
        with open(SPARRING_TASK_BANK_PATH, "w") as f:
            json.dump(bank, f, indent=2)
        print(f"[TRAINING] Hard negative added to task bank: {failure_mode}")
    except Exception as e:
        print(f"[TRAINING] Hard negative log error (non-fatal): {e}")


# ═══════════════════════════════════════════════════════════════
# TB REVIEWER (v3 Phase D)
# ═══════════════════════════════════════════════════════════════

REVIEW_LOG_PATH = DRIVER_DIR / "review_log.jsonl"


def deepen_follow_up(task: Dict, review_notes: str, session_id: str,
                     config: Dict) -> tuple:
    """Inline follow-up on same session after DEEPEN verdict.

    Instead of re-queuing (losing context), immediately sends review feedback
    to the same Claude session and re-reviews the result.

    Returns (response_dict, review_dict).
    """
    follow_up_prompt = (
        f"TB review feedback on your previous work:\n{review_notes}\n\n"
        "Address these issues and continue. When done, summarize what you fixed."
    )
    max_turns = config.get("deepen_followup_max_turns", 15)
    effort = config.get("claude_effort", "max")
    claude_model = config.get("claude_model", "")
    allowed_tools = config.get("v3_features", {}).get(
        "executor_tools_debug", "Bash,Read,Edit,Write,Glob,Grep")

    cmd = [
        "claude", "-p", follow_up_prompt,
        "--output-format", "json",
        "--max-turns", str(max_turns),
        "--effort", effort,
        "--allowedTools", allowed_tools,
    ]
    if claude_model:
        cmd.extend(["--model", claude_model])
    if session_id:
        cmd.extend(["--resume", session_id])

    timeout_sec = config.get("session_timeout_minutes", 120) * 60
    print(f"[DEEPEN] Follow-up on session {session_id[:12] if session_id else 'fresh'}... "
          f"(max {max_turns} turns)")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        response = {}
        if result.stdout.strip():
            try:
                response = json.loads(result.stdout)
            except json.JSONDecodeError:
                response = {"result": result.stdout.strip()}
        if not response:
            response = {"result": result.stderr.strip() if result.stderr else "no output"}
    except subprocess.TimeoutExpired:
        response = {"result": "follow-up timed out", "outcome": "timeout"}
    except Exception as e:
        response = {"result": f"follow-up error: {e}", "outcome": "error"}

    # Re-capture git diff for the follow-up review (check unstaged + staged + committed)
    git_diff_text = ""
    try:
        for diff_cmd in [
            ["git", "diff", "--stat"],
            ["git", "diff", "--cached", "--stat"],
        ]:
            diff_result = subprocess.run(
                diff_cmd, capture_output=True, text=True, timeout=10, cwd=str(PROJECT_ROOT))
            if diff_result.stdout.strip():
                git_diff_text = diff_result.stdout[:3000]
                break
    except Exception:
        pass

    # Re-review the follow-up result
    review = tb_review_output(task, response, git_diff_text, config)
    return (response, review)


def tb_review_output(task: Dict, executor_result: Dict,
                     git_diff: str, config: Dict) -> Dict:
    """Call TB via Ollama to review executor output.

    Returns:
        {"verdict": "ACCEPT|DEEPEN|ESCALATE",
         "reason": str,
         "deepen_notes": str,  # only if DEEPEN
         "confidence": float}

    Returns ACCEPT with confidence=1.0 if reviewer is disabled.
    """
    v3 = config.get("v3_features", {})
    if not v3.get("tb_reviewer_enabled", False):
        return {"verdict": "ACCEPT", "reason": "reviewer disabled", "confidence": 1.0}

    tb_model = os.environ.get("TB_MODEL") or v3.get("tb_model", "third-brother:latest")
    timeout = v3.get("tb_review_timeout_seconds", 180)

    result_text = executor_result.get("result", "")
    if isinstance(result_text, dict):
        result_text = json.dumps(result_text)

    scope = task.get("scope", ["**"])
    scope_str = ", ".join(scope)

    review_prompt = f"""You are Third Brother, reviewing work done by Claude Code.

Task: {task.get('title', '')}
Description: {task.get('description', '')}
Allowed file scope: {scope_str}

Executor Output (last 1500 chars):
{str(result_text)[-1500:]}

Git Diff (last 2000 chars):
{git_diff[-2000:] if git_diff else '(no changes detected)'}

Review the work and respond with EXACTLY one of:
ACCEPT - The task is done correctly. Changes match the task requirements.
DEEPEN - The task is partially done or needs more work. Explain what is missing.
ESCALATE - Something is wrong or risky. Needs human review.

IMPORTANT: If the git diff shows files modified OUTSIDE the allowed file scope, you MUST ESCALATE.
If the executor claims work was "already done" but the diff shows no relevant code changes, DEEPEN.

Format your response as:
VERDICT: [ACCEPT/DEEPEN/ESCALATE]
REASON: [one sentence]
NOTES: [if DEEPEN, what additional work is needed]

Respond now:"""

    task_id = task.get("id", "")
    print(f"[REVIEW] Reviewing {task_id or '?'} via {tb_model}...")

    try:
        output, duration_ms = _ollama_generate(
            review_prompt, tb_model, timeout=600, num_predict=200)

        log_ollama_call("REVIEW", tb_model, review_prompt, output or "",
                        0 if output else -1, duration_ms, "", task_id)

        if not output:
            print(f"[REVIEW] Ollama failed after {duration_ms}ms, defaulting to ACCEPT")
            return {"verdict": "ACCEPT", "reason": "ollama error", "confidence": 0.5}

        # Parse verdict from TB's response — structured parsing with fallbacks
        verdict = None
        reason = output[:200]
        deepen_notes = ""
        parse_method = "fallback"

        # Strategy 1: Parse explicit VERDICT: line (matches prompted format)
        for line in output.split("\n"):
            stripped = line.strip().upper()
            if stripped.startswith("VERDICT:"):
                token = stripped.split(":", 1)[1].strip().split()[0] if ":" in stripped else ""
                if token in ("ACCEPT", "DEEPEN", "ESCALATE"):
                    verdict = token
                    parse_method = "verdict_line"
                    break

        # Strategy 2: Substring match (original approach)
        if not verdict:
            output_upper = output.upper()
            if "ESCALATE" in output_upper:
                verdict = "ESCALATE"
                parse_method = "substring"
            elif "DEEPEN" in output_upper:
                verdict = "DEEPEN"
                parse_method = "substring"

        # Strategy 3: Negative-sentiment detection (catch rubber-stamp failures)
        if not verdict:
            output_lower = output.lower()
            negative_phrases = [
                "not completed", "incorrect", "wrong", "failed", "missing",
                "broken", "does not", "doesn't", "no visible", "not found",
                "not implemented", "incomplete", "risky", "dangerous",
            ]
            if any(phrase in output_lower for phrase in negative_phrases):
                verdict = "ESCALATE"
                parse_method = "negative_sentiment"

        # Strategy 4: No signal — uncertain ACCEPT (not confident rubber-stamp)
        if not verdict:
            verdict = "ACCEPT"
            parse_method = "fallback"

        # Confidence reflects parse certainty, not hardcoded
        confidence_map = {
            "verdict_line": 0.8,
            "substring": 0.7,
            "negative_sentiment": 0.6,
            "fallback": 0.5,
        }
        confidence = confidence_map[parse_method]

        # Extract DEEPEN notes
        if verdict == "DEEPEN":
            for line in output.split("\n"):
                if line.strip().upper().startswith("NOTES:"):
                    deepen_notes = line.split(":", 1)[1].strip()
                    break
            if not deepen_notes:
                deepen_notes = output[-500:]

        # Extract reason from REASON: line
        for line in output.split("\n"):
            if line.strip().upper().startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()
                break

        review_result = {
            "verdict": verdict,
            "reason": reason,
            "confidence": confidence,
        }
        if deepen_notes:
            review_result["deepen_notes"] = deepen_notes

        print(f"[REVIEW] {task.get('id', '?')}: {verdict} (confidence: {confidence}, "
              f"parse: {parse_method}) — {reason[:80]}")

        # Log review
        log_entry = {
            "ts": datetime.now().isoformat(),
            "task_id": task.get("id", ""),
            "verdict": verdict,
            "confidence": confidence,
            "reason": reason,
            "parse_method": parse_method,
            "reviewer_model": tb_model,
            "duration_ms": duration_ms,
        }
        with open(REVIEW_LOG_PATH, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        return review_result

    except Exception as e:
        print(f"[REVIEW] Error: {e}, defaulting to ACCEPT")
        return {"verdict": "ACCEPT", "reason": f"error: {e}", "confidence": 0.5}


# ═══════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════

def log_ollama_call(caller: str, model: str, prompt: str, response: str,
                    exit_code: int, duration_ms: int, stderr: str = "",
                    task_id: str = ""):
    """Log an Ollama call to ollama_calls.jsonl — always persists, VERBOSE controls stdout."""
    entry = {
        "ts": datetime.now().isoformat(),
        "caller": caller,
        "model": model,
        "task_id": task_id,
        "prompt_chars": len(prompt),
        "response_chars": len(response),
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "stderr": stderr[:500] if stderr else "",
    }
    if VERBOSE:
        entry["prompt"] = prompt
        entry["response"] = response
        print(f"[VERBOSE][{caller}] ── Ollama {model} (exit={exit_code}, {duration_ms}ms) ──")
        print(f"[VERBOSE][{caller}] prompt: {prompt[:500]}...")
        print(f"[VERBOSE][{caller}] response: {response[:500]}...")
        if stderr:
            print(f"[VERBOSE][{caller}] stderr: {stderr[:500]}")
        print(f"[VERBOSE][{caller}] ── end ──")
    try:
        with open(OLLAMA_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def log_alert(rule: str, task_id: str, action: str, detail: str = "",
              severity: str = "INFO"):
    """Log a guardrail alert."""
    entry = {
        "ts": datetime.now().isoformat(),
        "rule": rule,
        "task_id": task_id,
        "action": action,
        "detail": detail,
        "severity": severity,
    }
    with open(ALERTS_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def log_run(task: Dict, outcome: str, turns: int = 0,
            duration_seconds: int = 0, failure_reason: str = "",
            retry_count: int = 0, session_id: str = "",
            eval_score: Optional[float] = None):
    """Log a completed run."""
    entry = {
        "ts": datetime.now().isoformat(),
        "task_id": task["id"],
        "task_title": task["title"],
        "outcome": outcome,
        "turns": turns,
        "duration_seconds": duration_seconds,
        "failure_reason": failure_reason,
        "retry_count": retry_count,
        "driver_version": "v2",
        "session_id": session_id,
    }
    if eval_score is not None:
        entry["eval_score"] = eval_score
    with open(RUNS_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _load_recent_run_durations(n: int = 10) -> List[int]:
    """Return duration_seconds from the last N runs in runs.jsonl."""
    if not RUNS_PATH.exists():
        return []
    durations = []
    with open(RUNS_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line).get("duration_seconds", 0)
                if d > 0:
                    durations.append(d)
            except json.JSONDecodeError:
                continue
    return durations[-n:]


def _check_duration_alerts(task: Dict, duration: int, config: Dict):
    """Emit alerts for timeout-proximity and slow-task conditions."""
    task_id = task.get("id", "?")

    # 1) Timeout proximity: warn if task used >= 80% of session_timeout
    timeout_sec = config.get("session_timeout_minutes", 120) * 60
    if timeout_sec > 0 and duration >= timeout_sec * 0.8:
        pct = round(duration / timeout_sec * 100)
        log_alert(
            rule="timeout_proximity",
            task_id=task_id,
            action="warn",
            detail=f"duration={duration}s used {pct}% of {timeout_sec}s timeout",
            severity="WARNING",
        )

    # 2) Slow task: warn if duration > 2x rolling average of last 10 runs
    recent = _load_recent_run_durations(10)
    if recent:
        avg = sum(recent) / len(recent)
        if avg > 0 and duration > avg * 2:
            log_alert(
                rule="slow_task",
                task_id=task_id,
                action="warn",
                detail=f"duration={duration}s > 2x rolling avg={round(avg)}s "
                       f"(last {len(recent)} runs)",
                severity="WARNING",
            )


def _log_shadow_alert(details: str):
    """Write a validation-failure alert to alerts.jsonl."""
    alert = {
        "ts": datetime.now().isoformat(),
        "severity": "warning",
        "type": "shadow_log_validation",
        "details": details,
    }
    ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERTS_PATH, "a") as f:
        f.write(json.dumps(alert) + "\n")


def _rotate_shadow_log_if_needed():
    """Rotate shadow_log.jsonl to shadow_log_YYYYMMDD.jsonl when it exceeds 10 MB."""
    if not SHADOW_LOG_PATH.exists():
        return
    try:
        if SHADOW_LOG_PATH.stat().st_size < SHADOW_LOG_MAX_BYTES:
            return
    except OSError:
        return
    stamp = datetime.now().strftime("%Y%m%d")
    rotated = SHADOW_LOG_PATH.parent / f"shadow_log_{stamp}.jsonl"
    # Avoid overwriting a same-day rotation
    if rotated.exists():
        suffix = 1
        while rotated.exists():
            rotated = SHADOW_LOG_PATH.parent / f"shadow_log_{stamp}_{suffix}.jsonl"
            suffix += 1
    SHADOW_LOG_PATH.rename(rotated)


def _shadow_log_is_dup(task_id: str, instruction: str) -> bool:
    """Check last 50 lines of shadow_log for duplicate task_id+instruction."""
    if not SHADOW_LOG_PATH.exists():
        return False
    try:
        lines = SHADOW_LOG_PATH.read_text().strip().split("\n")
    except Exception:
        return False
    for line in lines[-50:]:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            if entry.get("task_id") == task_id and entry.get("query") == instruction:
                return True
        except json.JSONDecodeError:
            continue
    return False


def log_shadow_raft(task: Dict, instruction: str, response: str,
                    session_id: str, rag_results: List,
                    context: str, turn_count: int, outcome: str,
                    duration_ms: int = 0,
                    classification: Optional[Dict] = None,
                    scout_findings: Optional[Dict] = None,
                    tb_review: Optional[Dict] = None):
    """Write RAFT-format shadow log entry for future fine-tuning.

    v3: includes task_type, scout_used fields when classification is provided.
    """
    # ── Validate required fields ──
    task_id = task.get("id", "")
    if not task_id:
        _log_shadow_alert(f"Missing task_id, instruction={instruction[:80]!r}")
        return
    if not instruction:
        _log_shadow_alert(f"Empty instruction for task_id={task_id}")
        return
    if not response:
        _log_shadow_alert(f"Empty response for task_id={task_id}")
        return
    if not outcome:
        _log_shadow_alert(f"Missing outcome for task_id={task_id}")
        return

    # ── Dedup: skip if same task_id+instruction already in recent log ──
    if _shadow_log_is_dup(task_id, instruction):
        _log_shadow_alert(f"Duplicate entry skipped: task_id={task_id}, instruction={instruction[:80]!r}")
        return

    oracle_chunks = []
    distractor_chunks = []
    if rag_results:
        for i, r in enumerate(rag_results):
            chunk = None
            if isinstance(r, dict):
                chunk = {
                    "source": r.get("source", r.get("file_path", "")),
                    "score": round(r.get("score", 0), 4),
                    "content": (r.get("content", r.get("chunk", r.get("text", ""))))[:500],
                }
            elif isinstance(r, str):
                chunk = {"source": "", "score": 0, "content": r[:500]}
            if chunk:
                if i < 3:
                    oracle_chunks.append(chunk)
                else:
                    distractor_chunks.append(chunk)

    # Determine format version based on v3 metadata presence
    has_v3 = classification is not None and classification.get("type")
    fmt = "raft_v3" if has_v3 else "raft_v2"

    # Clean response: strip terminal noise (ANSI, box-drawing, control chars)
    clean_resp = response or ""
    clean_resp = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', clean_resp)  # ANSI escapes
    clean_resp = re.sub(r'[\u2500-\u259f\u2580-\u259f]', '', clean_resp)  # box-drawing
    clean_resp = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', clean_resp)  # control chars
    clean_resp = re.sub(r'\n{3,}', '\n\n', clean_resp).strip()

    entry = {
        "ts": datetime.now().isoformat(),
        "session_id": session_id,
        "task_id": task_id,
        "task_title": task.get("title", ""),
        "phase": "instruction",
        "query": instruction,
        "response": clean_resp[-4000:] if clean_resp else "",
        "model_outer": "template",
        "model_inner": "claude-opus-4-6",
        "oracle_chunks": oracle_chunks,
        "distractor_chunks": distractor_chunks,
        "rag_context_words": len(context.split()) if context else 0,
        "turn_number": 1,
        "total_turns": turn_count,
        "outcome": outcome,
        "latency_ms": duration_ms,
        "format": fmt,
    }

    # v3 enrichment fields
    if has_v3:
        entry["task_type"] = classification.get("type", "build")
        entry["scout_used"] = bool(scout_findings and scout_findings.get("raw"))
        entry["classification_confidence"] = classification.get("confidence", 0)
        if tb_review:
            entry["tb_review"] = tb_review.get("verdict", "")

    _rotate_shadow_log_if_needed()
    with open(SHADOW_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ═══════════════════════════════════════════════════════════════
# TRUST LADDER (spec section 12)
# ═══════════════════════════════════════════════════════════════

PHASE_MODES = {
    1: "supervised",
    2: "autonomous",   # safe tasks only (tests, docs)
    3: "autonomous",   # committed tasks
    4: "autonomous",   # overnight batches
}


def load_runs() -> List[Dict]:
    """Load all run entries from runs.jsonl."""
    if not RUNS_PATH.exists():
        return []
    entries = []
    for line in RUNS_PATH.read_text().strip().split('\n'):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def load_alerts() -> List[Dict]:
    """Load all alert entries from alerts.jsonl."""
    if not ALERTS_PATH.exists():
        return []
    entries = []
    for line in ALERTS_PATH.read_text().strip().split('\n'):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def load_verification_stats(window_size: int = 50) -> dict:
    """Compute rolling verification accuracy from verification_log.jsonl."""
    entries = []
    if VERIFICATION_LOG_PATH.exists():
        for line in VERIFICATION_LOG_PATH.read_text().strip().split('\n'):
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    window = entries[-window_size:] if entries else []
    total = len(window)
    verified_true = sum(1 for e in window if e.get("verified"))
    verified_false = total - verified_true
    accuracy = verified_true / total if total else 0.0

    recent_failures = [
        {"task_id": e.get("task_id", ""), "tiers_failed": e.get("tiers_failed", []), "ts": e.get("ts", "")}
        for e in window if not e.get("verified")
    ][-5:]  # last 5 failures

    # Count calibration DPO pairs in window (written to sparring_dpo.jsonl with source=calibration_dpo)
    calibration_dpo_count = 0
    if SPARRING_DPO_PATH.exists():
        for line in SPARRING_DPO_PATH.read_text().strip().split('\n'):
            if line.strip():
                try:
                    entry = json.loads(line)
                    if entry.get("metadata", {}).get("source") == "calibration_dpo":
                        calibration_dpo_count += 1
                except json.JSONDecodeError:
                    pass

    return {
        "total": total,
        "verified_true": verified_true,
        "verified_false": verified_false,
        "accuracy": round(accuracy, 3),
        "recent_failures": recent_failures,
        "calibration_dpo_count": calibration_dpo_count,
    }


def evaluate_trust_ladder(config: Dict) -> Tuple[int, int, str]:
    """Evaluate trust ladder and return (current_phase, new_phase, reason).

    Promotion:
      Phase 1->2: 15/20 instructions sent without edit (unedited_ratio >= 0.75)
      Phase 2->3: Completion rate > 70% over 30 runs
      Phase 3->4: 0 CRITICAL guardrail triggers for 20 consecutive runs

    Demotion:
      3 consecutive failed tasks -> demote one phase
      Any CRITICAL guardrail trigger -> demote to Phase 1 (supervised)
    """
    ladder = config.get("trust_ladder", {})
    current_phase = ladder.get("current_phase", 1)
    thresholds = ladder.get("thresholds", {})

    runs = load_runs()
    alerts = load_alerts()

    if not runs:
        return current_phase, current_phase, "no runs yet"

    # ── DEMOTION checks (always evaluated first) ──

    critical_alerts = [a for a in alerts if a.get("severity") == "CRITICAL"]
    if critical_alerts and current_phase > 1:
        return current_phase, 1, f"CRITICAL trigger: {critical_alerts[-1].get('rule', '?')}"

    consec_fail_limit = thresholds.get("demotion_consecutive_failures", 3)
    if len(runs) >= consec_fail_limit:
        recent = runs[-consec_fail_limit:]
        if all(r.get("outcome") in ("blocked", "error") for r in recent):
            new_phase = max(1, current_phase - 1)
            if new_phase != current_phase:
                return current_phase, new_phase, f"{consec_fail_limit} consecutive failures"

    # Verification accuracy demotion: if accuracy < 60%, demote regardless
    _vwindow = config.get("calibration_window_size", 50)
    _vstats = load_verification_stats(_vwindow)
    if _vstats["total"] >= 5 and _vstats["accuracy"] < 0.60 and current_phase > 1:
        new_phase = max(1, current_phase - 1)
        return current_phase, new_phase, (
            f"verification accuracy {_vstats['accuracy']:.0%} < 60% "
            f"({_vstats['verified_false']}/{_vstats['total']} failures)")

    # ── PROMOTION checks ──
    # Non-actionable outcomes (infrastructure issues, not task failures)
    _NON_ACTIONABLE = {"session_exhausted", "timeout", "session_busy", "completed_no_pr"}

    if current_phase == 1:
        cfg = thresholds.get("phase_1_to_2", {})
        min_runs = cfg.get("min_runs", 20)
        unedited_ratio = cfg.get("unedited_ratio", 0.75)
        if len(runs) >= min_runs:
            recent = runs[-min_runs:]
            actionable = [r for r in recent if r.get("outcome") not in _NON_ACTIONABLE]
            completed = sum(1 for r in actionable if r.get("outcome") == "completed")
            denom = len(actionable) or 1
            ratio = completed / denom
            if ratio >= unedited_ratio:
                return current_phase, 2, f"Phase 1->2: {completed}/{denom} ({ratio:.0%} >= {unedited_ratio:.0%})"

    elif current_phase == 2:
        cfg = thresholds.get("phase_2_to_3", {})
        min_runs = cfg.get("min_runs", 30)
        acceptance_ratio = cfg.get("acceptance_ratio", 0.70)
        if len(runs) >= min_runs:
            recent = runs[-min_runs:]
            actionable = [r for r in recent if r.get("outcome") not in _NON_ACTIONABLE]
            accepted = sum(1 for r in actionable if r.get("outcome") == "completed")
            denom = len(actionable) or 1
            ratio = accepted / denom
            if ratio >= acceptance_ratio:
                # Gate: verification accuracy must be >= 80% for Phase 2->3
                if _vstats["total"] >= 5 and _vstats["accuracy"] < 0.80:
                    pass  # block promotion — verification accuracy too low
                else:
                    return current_phase, 3, f"Phase 2->3: {accepted}/{denom} ({ratio:.0%} >= {acceptance_ratio:.0%}), verify={_vstats['accuracy']:.0%}"

    elif current_phase == 3:
        cfg = thresholds.get("phase_3_to_4", {})
        consec_needed = cfg.get("zero_critical_consecutive", 20)
        if len(runs) >= consec_needed:
            recent_runs = runs[-consec_needed:]
            earliest_ts = recent_runs[0].get("ts", "")
            critical_in_window = [
                a for a in critical_alerts
                if a.get("ts", "") >= earliest_ts
            ]
            if not critical_in_window:
                # Gate: verification accuracy must be >= 90% for Phase 3->4
                if _vstats["total"] >= 5 and _vstats["accuracy"] < 0.90:
                    pass  # block promotion — verification accuracy too low
                else:
                    return current_phase, 4, f"Phase 3->4: {consec_needed} runs, 0 CRITICALs, verify={_vstats['accuracy']:.0%}"

    return current_phase, current_phase, "no phase change"


def apply_trust_ladder(config: Dict) -> int:
    """Evaluate and apply trust ladder changes. Returns new phase."""
    old_phase, new_phase, reason = evaluate_trust_ladder(config)

    if old_phase != new_phase:
        direction = "PROMOTED" if new_phase > old_phase else "DEMOTED"
        print(f"[TRUST] {direction}: Phase {old_phase} -> Phase {new_phase}")
        print(f"[TRUST] Reason: {reason}")

        config.setdefault("trust_ladder", {})["current_phase"] = new_phase
        CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")

        log_alert(
            f"trust_ladder_{direction.lower()}",
            "system",
            f"phase_{old_phase}_to_{new_phase}",
            reason,
        )

    return new_phase


# ═══════════════════════════════════════════════════════════════
# SUPPORT RINGS (Phases 1-9) — each fails silently
# ═══════════════════════════════════════════════════════════════

STALE_SESSION_MINUTES = 90


def check_stale_session(session_id: str, config: Dict) -> bool:
    """Detect sessions running >90min without output. Returns True if stale."""
    if not STATE_PATH.exists():
        return False
    try:
        state = json.loads(STATE_PATH.read_text())
        updated_at = state.get("updated_at")
        if not updated_at:
            return False
        last_update = datetime.fromisoformat(updated_at)
        elapsed = (datetime.now() - last_update).total_seconds() / 60
        threshold = config.get("stale_session_minutes", STALE_SESSION_MINUTES)
        if elapsed > threshold:
            print(f"[WARNING] Stale session detected: {elapsed:.0f}min since last state update (threshold: {threshold}min)")
            log_alert(
                rule="stale_session",
                task_id=state.get("task_id", "unknown"),
                action="warning",
                detail=f"Session {session_id[:12]}... idle for {elapsed:.0f}min (>{threshold}min threshold)",
                severity="WARNING",
            )
            return True
    except Exception as e:
        print(f"[WARNING] Stale session check failed: {e}")
    return False


def ring_heartbeat_check():
    """RING 1: Check heartbeat triggers between tasks."""
    try:
        from mcp_server_nucleus.runtime.heartbeat_ops import _evaluate_context_triggers
        brain = {"path": str(BRAIN_PATH)}
        triggers = _evaluate_context_triggers(brain)
        if triggers:
            names = [t.get("type", "?") for t in triggers] if isinstance(triggers, list) else [str(triggers)]
            print(f"[RING 1] Heartbeat triggers: {', '.join(names)}")
            return triggers
    except Exception as e:
        print(f"[RING 1] Heartbeat: skip ({e.__class__.__name__})")
    return []


def ring_load_agent_prompt(task: Dict) -> str:
    """RING 1: Load relevant agent prompt for task context."""
    try:
        agents_dir = BRAIN_PATH / "agents"
        if not agents_dir.exists():
            return ""
        # Map task scope to agent role
        scope = " ".join(task.get("scope", []))
        title = task.get("title", "").lower()
        desc = task.get("description", "").lower()
        combined = f"{title} {desc} {scope}"

        role = "developer"  # default
        if any(w in combined for w in ("test", "pytest", "spec")):
            role = "critic"
        elif any(w in combined for w in ("architect", "design", "refactor")):
            role = "architect"
        elif any(w in combined for w in ("research", "investigate", "explore")):
            role = "researcher"
        elif any(w in combined for w in ("document", "readme", "docs")):
            role = "librarian"

        prompt_file = agents_dir / f"{role}.md"
        if prompt_file.exists():
            content = prompt_file.read_text()
            # Trim to first 500 words to stay within context budget
            words = content.split()
            trimmed = " ".join(words[:500])
            print(f"[RING 1] Agent prompt: {role} ({len(words)} words)")
            return f"\n## Agent Role: {role}\n{trimmed}\n"
    except Exception as e:
        print(f"[RING 1] Agent prompt: skip ({e.__class__.__name__})")
    return ""


def ring_knowledge_rules(task: Dict) -> str:
    """RING 2: Check knowledge index for applicable brain files."""
    try:
        index_path = BRAIN_PATH / "knowledge_index.json"
        if not index_path.exists():
            return ""
        index = json.loads(index_path.read_text())
        files = index.get("files", [])
        if not files:
            return ""

        # Match brain files by keyword overlap with task
        task_words = set(w.lower() for w in
                        (task.get("title", "") + " " + task.get("description", "")).split()
                        if len(w) > 3)
        matched = []
        for f in files:
            summary = f.get("summary", "")
            title = f.get("title", "")
            text = f"{title} {summary}".lower()
            text_words = set(text.split())
            overlap = task_words & text_words
            if len(overlap) >= 2:
                matched.append((len(overlap), f.get("path", ""), summary[:200]))

        matched.sort(reverse=True)
        if matched:
            print(f"[RING 2] Knowledge: {len(matched)} brain files matched")
            top = matched[:5]
            lines = [f"- `{path}`: {summary}" for _, path, summary in top]
            return "\n## Relevant Brain Files\n" + "\n".join(lines) + "\n"
    except Exception as e:
        print(f"[RING 2] Knowledge: skip ({e.__class__.__name__})")
    return ""


def ring_emit_event(event_type: str, task: Dict, payload: Dict = None):
    """RING 3: Emit event to brain event stream."""
    try:
        from mcp_server_nucleus.runtime.event_stream import emit_event
        emit_event(
            brain_path=str(BRAIN_PATH),
            event_type=event_type,
            emitter="third-brother-driver-v2",
            payload=payload or {"task_id": task["id"], "task_title": task["title"]},
            severity="ROUTINE",
        )
    except Exception as e:
        print(f"[RING 3] Event emit: skip ({e.__class__.__name__})")


def fire_task_webhook(task: Dict, outcome: str, duration: float, turns: int, config: Dict):
    """Fire webhook on task completion. Non-blocking — failures are logged, never fatal."""
    wh = config.get("webhook", {})
    if not wh.get("enabled") or not wh.get("url"):
        return
    import hashlib, hmac, urllib.request, urllib.error
    payload = json.dumps({
        "event": "task_completed",
        "task_id": task["id"],
        "title": task.get("title", ""),
        "outcome": outcome,
        "duration_seconds": duration,
        "turns": turns,
        "branch": task.get("branch", ""),
        "timestamp": datetime.now().isoformat(),
    }, separators=(",", ":"))
    headers = {"Content-Type": "application/json"}
    secret = wh.get("secret", "")
    if secret:
        sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        headers["X-TB-Signature"] = f"sha256={sig}"
    try:
        req = urllib.request.Request(
            wh["url"], data=payload.encode(), headers=headers, method="POST")
        timeout = wh.get("timeout_seconds", 10)
        urllib.request.urlopen(req, timeout=timeout)
        print(f"[WEBHOOK] Fired for {task['id']} → {outcome}")
    except (urllib.error.URLError, OSError) as e:
        print(f"[WEBHOOK] Failed for {task['id']}: {e}")
    except Exception as e:
        print(f"[WEBHOOK] Error: {e}")


def ring_depth_push(task: Dict):
    """RING 4: Push depth tracking for task execution."""
    try:
        from mcp_server_nucleus.runtime.depth_ops import _depth_push
        _depth_push(f"driver-task:{task['id']}")
        print(f"[RING 4] Depth push: {task['id']}")
    except Exception as e:
        print(f"[RING 4] Depth push: skip ({e.__class__.__name__})")


def ring_depth_pop():
    """RING 4: Pop depth tracking after task execution."""
    try:
        from mcp_server_nucleus.runtime.depth_ops import _depth_pop
        _depth_pop()
    except Exception:
        pass


def ring_commitment_score(task: Dict) -> Dict:
    """RING 5: Score task commitment context."""
    try:
        from mcp_server_nucleus.commitment_ledger import analyze_context
        scores = analyze_context(task.get("description", ""), "driver")
        if scores:
            print(f"[RING 5] Commitment: novelty={scores.get('novelty', '?')}, "
                  f"urgency={scores.get('urgency', '?')}")
            return scores
    except Exception as e:
        print(f"[RING 5] Commitment score: skip ({e.__class__.__name__})")
    return {}


def ring_consolidation():
    """RING 6: Run consolidation between task batches."""
    try:
        from mcp_server_nucleus.runtime.consolidation_ops import (
            _archive_resolved_files,
            _garbage_collect_tasks,
        )
        archived = _archive_resolved_files()
        gc_count = _garbage_collect_tasks(max_age_hours=72)
        if archived or gc_count:
            print(f"[RING 6] Consolidation: {archived} archived, {gc_count} GC'd")
    except Exception as e:
        print(f"[RING 6] Consolidation: skip ({e.__class__.__name__})")


def ring_checkpoint_save(task: Dict, progress: int = 50):
    """RING 7: Save task checkpoint mid-execution."""
    try:
        from mcp_server_nucleus.runtime.checkpoint_ops import _brain_checkpoint_task_impl
        _brain_checkpoint_task_impl(
            task_id=task["id"],
            step=f"driver-executing-{task['title'][:30]}",
            progress_percent=progress,
            context=f"Driver v2 executing task {task['id']}",
            artifacts=[],
            resumable=True,
        )
    except Exception as e:
        print(f"[RING 7] Checkpoint: skip ({e.__class__.__name__})")


def ring_archive_turn(task: Dict, outcome: str, response: Dict, duration: int):
    """RING 8: Record turn in archive pipeline for training data."""
    try:
        from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline
        pipeline = ArchivePipeline()
        pipeline.record_turn(
            brother="third-brother-driver-v2",
            intent=task.get("description", "")[:500],
            outcome=outcome,
            decisions=[f"task:{task['id']}"],
            actions=["claude-p-resume"],
            tools_used=["claude-code"],
            context=f"session-resume, {task.get('scope', ['**'])}",
            confidence=0.8 if outcome == "completed" else 0.3,
            conversation=response.get("result", "")[:2000],
        )
        print(f"[RING 8] Archive: turn recorded")
    except Exception as e:
        print(f"[RING 8] Archive: skip ({e.__class__.__name__})")


def ring_selfheal_on_failure(task: Dict, error: str) -> str:
    """RING 9: Capture 4D context on failure for self-healing."""
    try:
        from mcp_server_nucleus.selfhealer import (
            _get_intent_context,
            _get_recent_changes,
        )
        intent = _get_intent_context(str(BRAIN_PATH))
        changes = _get_recent_changes(str(PROJECT_ROOT))
        diagnosis = f"Task {task['id']} failed: {error[:200]}\nIntent: {intent[:300]}\nRecent changes: {changes[:300]}"
        print(f"[RING 9] Self-heal: 4D context captured ({len(diagnosis)} chars)")
        return diagnosis
    except Exception as e:
        print(f"[RING 9] Self-heal: skip ({e.__class__.__name__})")
    return ""


def ring_engram_lookup(task: Dict) -> str:
    """RING 3+: Query engrams for task-relevant memory."""
    try:
        from mcp_server_nucleus.runtime.engram_ops import _brain_query_engrams_impl
        results = _brain_query_engrams_impl(
            context=task.get("title", ""),
            min_intensity=0.5,
            limit=5,
        )
        if results and isinstance(results, dict):
            engrams = results.get("engrams", [])
            if engrams:
                print(f"[RING 3+] Engrams: {len(engrams)} found")
                lines = []
                for e in engrams[:3]:
                    key = e.get("key", "?")
                    val = str(e.get("value", ""))[:150]
                    lines.append(f"- {key}: {val}")
                return "\n## Engram Memory\n" + "\n".join(lines) + "\n"
    except Exception as e:
        print(f"[RING 3+] Engrams: skip ({e.__class__.__name__})")
    return ""


def ring_export_training():
    """RING 8+: Export training data in multiple formats."""
    try:
        from scripts.export_raft_training import load_shadow_log, build_sft_examples, build_dpo_pairs, export, compute_stats
        entries = load_shadow_log(SHADOW_LOG_PATH)
        if entries:
            sft = build_sft_examples(entries)
            dpo = build_dpo_pairs(entries)
            stats = compute_stats(entries, sft, dpo)
            out_dir = BRAIN_PATH / "training"
            export(out_dir, sft, dpo, stats)
            print(f"[RING 8+] Training export: {len(sft)} SFT, {len(dpo)} DPO")
    except Exception as e:
        print(f"[RING 8+] Training export: skip ({e.__class__.__name__})")

    # Also try archive pipeline multi-format export
    try:
        from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline
        pipeline = ArchivePipeline()
        out_dir = str(BRAIN_PATH / "training")
        pipeline.export_gemini(out_dir + "/archive_gemini.jsonl")
        pipeline.export_openai(out_dir + "/archive_openai.jsonl")
        print(f"[RING 8+] Archive export: gemini + openai formats")
    except Exception as e:
        print(f"[RING 8+] Archive export: skip ({e.__class__.__name__})")


def archive_session_transcript(session_id: str, task: Dict, outcome: str):
    """Archive full Claude Code session JSONL — platinum training data.

    The full session transcript captures every turn, correction, decision,
    and tool use. This is the highest-value training signal: it shows HOW
    problems get solved, not just the final answer.
    """
    if not session_id:
        return
    try:
        # Claude Code stores session transcripts in the project directory
        project_dir = PROJECT_ROOT
        claude_projects = Path.home() / ".claude" / "projects"
        # Find the session file — it's named [session-id].jsonl
        # under a project-specific directory
        for proj_dir in claude_projects.iterdir():
            if not proj_dir.is_dir():
                continue
            session_file = proj_dir / f"{session_id}.jsonl"
            if session_file.exists():
                # Copy to training archive
                archive_dir = BRAIN_PATH / "training" / "session_transcripts"
                archive_dir.mkdir(parents=True, exist_ok=True)
                dest = archive_dir / f"{task['id']}_{session_id[:12]}_{outcome}.jsonl"
                if not dest.exists():
                    import shutil
                    shutil.copy2(session_file, dest)
                    size_kb = dest.stat().st_size / 1024
                    print(f"[ARCHIVE] Session transcript: {dest.name} ({size_kb:.0f} KB)")
                return
    except Exception as e:
        pass  # Silent — don't break the driver for archiving


def ring_eval_quick(task_id: str) -> Optional[float]:
    """RING 10: Run quick eval (5 random prompts) and return overall_rate or None on failure."""
    try:
        eval_script = BRAIN_PATH / "training" / "run_evals.py"
        if not eval_script.exists():
            print(f"[RING 10] Eval: skip (script not found)")
            return None
        result = subprocess.run(
            [sys.executable, str(eval_script), "--quick", "--json"],
            capture_output=True, text=True,
            cwd=str(PROJECT_ROOT), timeout=300,
        )
        if result.returncode not in (0, 1):  # 0=pass, 1=below threshold, both valid
            print(f"[RING 10] Eval: failed (exit {result.returncode})")
            return None
        # --json prints JSON object to stdout
        output = json.loads(result.stdout.strip())
        score = output.get("overall_rate")
        grade = output.get("grade", "?")
        print(f"[RING 10] Eval: {score}% ({grade})")
        return score
    except subprocess.TimeoutExpired:
        print(f"[RING 10] Eval: timeout")
        return None
    except (json.JSONDecodeError, Exception) as e:
        print(f"[RING 10] Eval: skip ({e.__class__.__name__})")
        return None


def check_eval_regression(score: float) -> bool:
    """Check if eval score dropped >10% from rolling 3-run average.

    Returns True if regression detected (alert emitted).
    """
    runs = load_runs()
    # Collect last 3 runs that have an eval_score
    recent_scores = []
    for r in reversed(runs):
        s = r.get("eval_score")
        if s is not None:
            recent_scores.append(s)
        if len(recent_scores) >= 3:
            break

    if len(recent_scores) < 3:
        return False  # not enough history

    rolling_avg = sum(recent_scores) / len(recent_scores)
    if rolling_avg <= 0:
        return False

    drop_pct = (rolling_avg - score) / rolling_avg * 100
    if drop_pct > 10:
        detail = (f"score={score:.1f}%, rolling_avg={rolling_avg:.1f}%, "
                  f"drop={drop_pct:.1f}%")
        print(f"[EVAL] REGRESSION DETECTED: {detail}")
        log_alert(
            rule="eval_regression",
            task_id="system",
            action="alert",
            detail=detail,
            severity="WARNING",
        )
        return True
    return False


def ring_retrain_check(completed_count: int):
    """RING 9: Check if enough tasks accumulated for a retrain."""
    try:
        manifest_path = Path.home() / "Library" / "CloudStorage" / "GoogleDrive-mailforlkgarg@gmail.com" / "My Drive" / "nucleus-training" / "data" / "manifest.json"
        last_count = 0
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            last_count = manifest.get("last_retrain_task_count", 0)
        delta = completed_count - last_count
        if delta >= 100:
            print(f"[RING 9] *** RETRAIN READY *** {delta} tasks since last retrain (threshold: 100)")
            print(f"[RING 9] Run: python3 .brain/training/colab_push_data.py")
        elif delta >= 75:
            print(f"[RING 9] Retrain approaching: {delta}/100 tasks since last retrain")
    except Exception as e:
        pass  # Silent — Drive may not be mounted


def ring_distill_replay(task: Dict) -> str:
    """RING 3+: Inject high-confidence DCAs from previous distillation."""
    try:
        from mcp_server_nucleus.replay import ReplayEngine
        engine = ReplayEngine(str(BRAIN_PATH))
        atoms = engine.load_atoms()
        if atoms:
            filtered = engine.filter_atoms(atoms, min_confidence=0.8, max_atoms=3)
            if filtered:
                print(f"[RING 3+] Replay: {len(filtered)} DCAs injected")
                lines = []
                for a in filtered:
                    decision = getattr(a, 'decision', str(a))[:200]
                    lines.append(f"- {decision}")
                return "\n## Prior Decisions (high confidence)\n" + "\n".join(lines) + "\n"
    except Exception as e:
        print(f"[RING 3+] Replay: skip ({e.__class__.__name__})")
    return ""


def generate_session_report(session_id: str, driver_start_time: datetime = None):
    """Generate a markdown summary report for the completed driver session.

    Reads runs.jsonl, shadow_log.jsonl, and alerts.jsonl to aggregate:
    - tasks attempted + outcomes
    - total duration (task time + wall clock)
    - training data generated (shadow_log entries, session transcripts)
    - alerts fired during session
    Saves to .brain/driver/session_reports/<timestamp>_<session_id>.md
    """
    reports_dir = DRIVER_DIR / "session_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    start_ts = driver_start_time.isoformat() if driver_start_time else ""

    # ── Helper: load jsonl with optional time filter ──
    def _load_jsonl(path: Path, since: str = "") -> List[Dict]:
        entries = []
        if not path.exists():
            return entries
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if since and e.get("ts", "") < since:
                        continue
                    entries.append(e)
                except json.JSONDecodeError:
                    continue
        return entries

    # ── Collect runs for this session ──
    all_runs = _load_jsonl(RUNS_PATH, since=start_ts)
    # Prefer session_id match; fall back to today's v2 runs
    session_runs = [r for r in all_runs if r.get("session_id") == session_id] if session_id else []
    if not session_runs:
        today_prefix = now.strftime("%Y-%m-%d")
        session_runs = [
            r for r in all_runs
            if r.get("driver_version") == "v2"
            and r.get("ts", "").startswith(today_prefix)
        ]
    if not session_runs:
        return

    # ── Shadow log entries this session ──
    shadow_entries = _load_jsonl(SHADOW_LOG_PATH, since=start_ts)
    shadow_count = len(shadow_entries)

    # ── Alerts this session ──
    alerts = _load_jsonl(ALERTS_PATH, since=start_ts)

    # ── Session transcripts archived ──
    transcripts_dir = BRAIN_PATH / "training" / "session_transcripts"
    transcript_count = 0
    if transcripts_dir.exists():
        for f in transcripts_dir.iterdir():
            if f.suffix == ".jsonl" and f.stat().st_mtime >= (driver_start_time or now).timestamp():
                transcript_count += 1

    # ── Aggregate stats ──
    task_duration = sum(r.get("duration_seconds", 0) for r in session_runs)
    wall_clock = int((now - driver_start_time).total_seconds()) if driver_start_time else task_duration
    total_turns = sum(r.get("turns", 0) for r in session_runs)
    outcomes = {}
    for r in session_runs:
        o = r.get("outcome", "unknown")
        outcomes[o] = outcomes.get(o, 0) + 1
    completed = outcomes.get("completed", 0) + outcomes.get("completed_no_pr", 0)
    completion_rate = round(completed / len(session_runs) * 100) if session_runs else 0

    # ── Duration stats ──
    run_durations = sorted(r.get("duration_seconds", 0) for r in session_runs)
    run_durations_nonzero = [d for d in run_durations if d > 0]
    avg_duration = round(sum(run_durations_nonzero) / len(run_durations_nonzero)) if run_durations_nonzero else 0
    if run_durations_nonzero:
        p95_idx = max(0, int(len(run_durations_nonzero) * 0.95) - 1)
        p95_duration = run_durations_nonzero[p95_idx]
    else:
        p95_duration = 0

    # ── Build markdown ──
    sid_short = (session_id or "none")[:12]
    report_name = f"{now.strftime('%Y%m%d_%H%M%S')}_{sid_short}.md"

    lines = [
        f"# Driver Session Report",
        f"",
        f"- **Date:** {now.strftime('%Y-%m-%d %H:%M')}",
        f"- **Session ID:** {session_id or 'N/A'}",
        f"- **Tasks attempted:** {len(session_runs)}",
        f"- **Completion rate:** {completion_rate}% ({completed}/{len(session_runs)})",
        f"- **Total duration:** {task_duration}s ({task_duration // 60}m {task_duration % 60}s)",
        f"- **Wall clock:** {wall_clock}s ({wall_clock // 60}m {wall_clock % 60}s)",
        f"- **Avg duration:** {avg_duration}s ({avg_duration // 60}m {avg_duration % 60}s)",
        f"- **P95 duration:** {p95_duration}s ({p95_duration // 60}m {p95_duration % 60}s)",
        f"- **Total turns:** {total_turns}",
        f"",
        f"## Outcomes",
        f"",
    ]
    for outcome, count in sorted(outcomes.items(), key=lambda x: -x[1]):
        lines.append(f"- {outcome}: {count}")

    lines += [
        f"",
        f"## Tasks",
        f"",
        f"| Task | Title | Outcome | Duration | Turns |",
        f"|------|-------|---------|----------|-------|",
    ]
    for r in session_runs:
        lines.append(
            f"| {r.get('task_id', '?')} "
            f"| {r.get('task_title', '?')[:50]} "
            f"| {r.get('outcome', '?')} "
            f"| {r.get('duration_seconds', 0)}s "
            f"| {r.get('turns', 0)} |"
        )

    lines += [
        f"",
        f"## Training Data",
        f"",
        f"- **shadow_log entries added today:** {shadow_count}",
        f"- **Session transcripts archived:** {transcript_count}",
        f"",
    ]

    if alerts:
        lines += [
            f"## Alerts",
            f"",
            f"| Time | Rule | Severity | Detail |",
            f"|------|------|----------|--------|",
        ]
        for a in alerts:
            ts_short = a.get("ts", "")[:19]
            lines.append(
                f"| {ts_short} "
                f"| {a.get('rule', '?')} "
                f"| {a.get('severity', '?')} "
                f"| {a.get('detail', '')[:60]} |"
            )
        lines.append("")

    report_path = reports_dir / report_name
    report_path.write_text("\n".join(lines))
    print(f"[REPORT] Session report saved: {report_path.name}")

    # Show branch summary if on a TB branch
    current_branch = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    if current_branch.startswith("tb/"):
        tb_branch_summary(current_branch)


# ═══════════════════════════════════════════════════════════════
# CORE DRIVER LOOP (v2 — session resume)
# ═══════════════════════════════════════════════════════════════

def _build_task_context(task: Dict, config: Dict,
                        session_task_count: int) -> Tuple[Dict, str, list, str]:
    """Classify task and build enriched context (RAG + rings).

    Returns:
        (classification, raw_context, rag_results, enriched_context)
    """
    task_id = task.get("id", "?")
    try:
        classification = classify_task(task, config)
        _fw_record_survived("phase_a_classify", task_id, config)
    except Exception as e:
        _fw_file_ticket("phase_a_classify", task_id, str(e), config)
        raise

    print("[DRIVER] Building context (brain_rag)...")
    context = ""
    rag_results = []
    try:
        from providers.brain_rag import build_full_context
        context, rag_results = build_full_context(
            task["description"], brain_path=BRAIN_PATH
        )
        print(f"[DRIVER] Context: {len(context.split())} words, {len(rag_results)} chunks")
    except Exception as e:
        print(f"[DRIVER] Context error: {e}. Continuing without RAG.")

    engrams = ring_engram_lookup(task)
    dcas = ring_distill_replay(task)

    if session_task_count > 0 and config.get("delta_context_after_first", True):
        enriched_context = (context or "(no RAG context available)") + engrams + dcas
        try:
            delta = subprocess.run(
                ["git", "diff", "--stat", "HEAD~1"],
                capture_output=True, text=True, timeout=10,
                cwd=str(PROJECT_ROOT)).stdout[:2000]
            if delta.strip():
                enriched_context += f"\n## Changes Since Last Task\n{delta}\n"
        except Exception:
            pass
        print(f"[CONTEXT] Delta mode: ~{len(enriched_context.split())} words "
              f"(task {session_task_count + 1} on session)")
    else:
        agent_prompt = ring_load_agent_prompt(task)
        knowledge = ring_knowledge_rules(task)
        enriched_context = (context or "(no RAG context available)") + agent_prompt + knowledge + engrams + dcas
        print(f"[CONTEXT] Full mode: ~{len(enriched_context.split())} words")

    return classification, context, rag_results, enriched_context


def _build_task_prompt(task: Dict, enriched_context: str, config: Dict,
                       classification: Dict, session_id: str) -> Tuple[str, dict, str]:
    """Run scout (if needed) and build prompt via TB or template fallback.

    Returns:
        (message, scout_findings, tb_prompt)
    """
    scout_findings = {}
    scout_on_main = bool(session_id and config.get("scout_on_main_session", True))
    task_id = task.get("id", "?")
    if classification.get("needs_scout"):
        try:
            scout_findings = run_scout_agent(
                task, enriched_context, config,
                scout_turns_override=classification.get("scout_turns"),
                session_id=session_id,
            )
            _fw_record_survived("phase_b_scout", task_id, config)
        except Exception as e:
            _fw_file_ticket("phase_b_scout", task_id, str(e), config)
            scout_findings = {}

    try:
        tb_prompt = tb_write_enriched_prompt(task, enriched_context, scout_findings, config)
        # None is a legitimate fallback (template), not a failure — still a survived outcome.
        _fw_record_survived("phase_c_prompt_writer", task_id, config)
    except Exception as e:
        _fw_file_ticket("phase_c_prompt_writer", task_id, str(e), config)
        tb_prompt = None

    if tb_prompt:
        message = tb_prompt
    else:
        scope_str = ", ".join(task.get("scope", ["**"]))
        scope_list = "\n".join(f"- {s}" for s in task.get("scope", ["**"]))
        message = TASK_TEMPLATE.format(
            title=task["title"],
            description=task["description"],
            context=enriched_context,
            scope=scope_str,
            scope_list=scope_list,
        )
        if scout_findings and scout_findings.get("raw") and not scout_on_main:
            message += f"\n\n## Scout Investigation Findings\n{scout_findings['raw']}\n"

    return message, scout_findings, tb_prompt


def _build_claude_cmd(message: str, classification: Dict, task: Dict,
                      config: Dict, session_id: str,
                      system_context: str) -> Tuple[list, int, str, int, bool]:
    """Build the claude CLI command and execution parameters.

    Returns:
        (cmd, max_turns, effort, timeout_sec, streaming)
    """
    max_turns = classification.get("max_turns", task.get("max_turns", config.get("claude_max_turns", 30)))
    allowed_tools = classification.get("tools", "Bash,Read,Edit,Write,Glob,Grep")
    effort = config.get("claude_effort", "max")
    timeout_sec = config.get("session_timeout_minutes", 120) * 60

    claude_model = config.get("claude_model", "")
    streaming = config.get("streaming_enabled", False)
    output_fmt = "stream-json" if streaming else "json"
    cmd = [
        "claude", "-p", message,
        "--output-format", output_fmt,
        "--max-turns", str(max_turns),
        "--effort", effort,
        "--allowedTools", allowed_tools,
    ]
    if streaming:
        cmd.append("--verbose")
    if claude_model:
        cmd.extend(["--model", claude_model])
    if session_id:
        cmd.extend(["--resume", session_id])
    if system_context:
        cmd.extend(["--append-system-prompt", system_context[:8000]])

    # Headless: skip permission prompts (requires explicit opt-in + trust phase 2+)
    headless_active = False
    if config.get("headless_enabled", False):
        trust_phase = config.get("trust_ladder", {}).get("current_phase", 1)
        if trust_phase >= 2:
            cmd.append("--dangerously-skip-permissions")
            headless_active = True
        else:
            print(f"[DRIVER] headless_enabled but trust phase {trust_phase} < 2 — permissions NOT skipped")

    model_label = claude_model or "default"
    stream_label = " [streaming]" if streaming else ""
    headless_label = " [headless]" if headless_active else ""
    print(f"[DRIVER] Executing: claude -p (model={model_label}, max {max_turns} turns, "
          f"effort {effort}{stream_label}{headless_label})"
          f"{f', resume={session_id[:12]}...' if session_id else ', fresh session'}")

    return cmd, max_turns, effort, timeout_sec, streaming


def _run_claude_with_retry(cmd: list, timeout_sec: int, config: Dict,
                           task: Dict) -> Tuple[Optional[object], int, Optional[str]]:
    """Non-streaming subprocess execution with session contention + transient retry.

    Returns:
        (result, exec_retry_count, error_type) where error_type is None on success,
        ``"timeout"`` on TimeoutExpired, or ``"session_busy"`` when retries exhausted.
    """
    max_retries = config.get("session_retry_max", 30)
    retry_interval = config.get("session_retry_interval", 60)

    EXEC_MAX_RETRIES = config.get("max_retries", 2)
    EXEC_BACKOFF_BASE = 5
    EXEC_BACKOFF_MULT = 3
    NO_RETRY_PATTERNS = ("guardrail", "kill_switch", "stop file", "permission denied",
                         "not allowed", "blocked by policy")

    exec_retry_count = 0
    result = None
    for attempt in range(1, max_retries + 1):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout_sec,
            )
            if result.returncode != 0:
                stderr = result.stderr or ""
                stderr_lower = stderr.lower()

                if any(p in stderr_lower for p in NO_RETRY_PATTERNS):
                    print(f"[DRIVER] Non-retryable failure (exit {result.returncode}): "
                          f"{stderr[:200]}")
                    break

                if any(s in stderr_lower for s in ("session", "lock", "busy", "in use", "conflict")):
                    print(f"[DRIVER] Session busy (attempt {attempt}/{max_retries}). "
                          f"Waiting {retry_interval}s...")
                    time.sleep(retry_interval)
                    continue

                if exec_retry_count < EXEC_MAX_RETRIES:
                    exec_retry_count += 1
                    backoff = EXEC_BACKOFF_BASE * (EXEC_BACKOFF_MULT ** (exec_retry_count - 1))
                    print(f"[DRIVER] Subprocess failed (exit {result.returncode}). "
                          f"Retry {exec_retry_count}/{EXEC_MAX_RETRIES} in {backoff}s...")
                    log_alert(
                        rule="exec_retry",
                        task_id=task.get("id", "?"),
                        action=f"retry_{exec_retry_count}",
                        detail=f"exit={result.returncode}, backoff={backoff}s, "
                               f"stderr={stderr[:300]}",
                        severity="WARNING",
                    )
                    time.sleep(backoff)
                    result = None
                    continue

            break
        except subprocess.TimeoutExpired:
            return None, exec_retry_count, "timeout"

    if result is None:
        print(f"[DRIVER] All {max_retries} retries exhausted. Session never freed.")
        return None, exec_retry_count, "session_busy"

    return result, exec_retry_count, None


def _parse_claude_output(result) -> Dict:
    """Parse JSON (or plain text) response from claude stdout."""
    response = {}
    if result.stdout.strip():
        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError:
            response = {"result": result.stdout.strip()}

    if result.returncode != 0 and not response:
        response = {"result": result.stderr.strip() if result.stderr else "non-zero exit"}

    return response


def execute_task(task: Dict, session_id: str, config: Dict,
                 system_context: str = "", session_task_count: int = 0) -> Dict:
    """Execute a single task via claude -p --resume. Returns parsed JSON response.

    v3 flow: classify → [scout] → build prompt → execute
    """
    # Phase 1: Context + prompt
    classification, context, rag_results, enriched_context = \
        _build_task_context(task, config, session_task_count)
    message, scout_findings, tb_prompt = \
        _build_task_prompt(task, enriched_context, config, classification, session_id)

    # Phase 2: Build command
    cmd, max_turns, effort, timeout_sec, streaming = \
        _build_claude_cmd(message, classification, task, config, session_id, system_context)
    task_start = time.time()

    # Metadata shared by all exit paths
    base_meta = {
        "context": context,
        "rag_results": rag_results,
        "message": message,
        "classification": classification,
        "scout_findings": scout_findings,
    }

    # ── Streaming path ──
    if streaming:
        stream_log = Path(config.get("stream_log_path", str(DRIVER_DIR / "stream.log")))
        response = execute_streaming(cmd, timeout_sec, stream_log, max_turns)
        duration = int(time.time() - task_start)
        _check_duration_alerts(task, duration, config)

        response["duration_seconds"] = duration
        response["retry_count"] = 0
        response["tb_prompt"] = tb_prompt or ""
        response.update(base_meta)

        if not session_id and response.get("session_id"):
            session_id = response["session_id"]

        effective_session = session_id or response.get("session_id", "")
        if effective_session:
            ctx_metrics = monitor_session_context(effective_session)
            response["context_metrics"] = ctx_metrics
            print(f"[MONITOR] Session: {ctx_metrics['turns']} turns, "
                  f"{ctx_metrics['bytes'] // 1024}KB, {ctx_metrics['pressure_pct']}% pressure")

        return response

    # ── Non-streaming path ──
    result, exec_retry_count, error_type = \
        _run_claude_with_retry(cmd, timeout_sec, config, task)
    duration = int(time.time() - task_start)

    if error_type == "timeout":
        print(f"[DRIVER] Session timeout after {duration}s")
        return {"outcome": "timeout", "result": "", "turns": 0,
                "duration_seconds": duration, "retry_count": exec_retry_count,
                **base_meta}

    if error_type == "session_busy":
        return {"outcome": "session_busy",
                "result": "Session contention — retries exhausted", "turns": 0,
                "duration_seconds": duration, "retry_count": exec_retry_count,
                **base_meta}

    _check_duration_alerts(task, duration, config)

    response = _parse_claude_output(result)
    response["duration_seconds"] = duration
    response["retry_count"] = exec_retry_count
    response["tb_prompt"] = tb_prompt or ""
    response.update(base_meta)

    if session_id:
        ctx_metrics = monitor_session_context(session_id)
        response["context_metrics"] = ctx_metrics
        print(f"[MONITOR] Session: {ctx_metrics['turns']} turns, "
              f"{ctx_metrics['bytes'] // 1024}KB, {ctx_metrics['pressure_pct']}% pressure")

    return response


def execute_streaming(cmd: list, timeout: int, stream_log: Path,
                      max_turns: int) -> dict:
    """Execute claude via Popen with stream-json output.

    Reads stdout line by line for live visibility and early abort.
    Returns assembled response dict matching the JSON output format.
    """
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    result_event = None
    accumulated_text = []
    turn_count = 0
    current_tool = ""
    session_id_captured = ""

    try:
        log_fh = open(stream_log, "a")
    except Exception:
        log_fh = None

    try:
        for line in proc.stdout:
            line = line.rstrip("\n")
            if not line:
                continue

            # Log raw stream for tail -f
            if log_fh:
                try:
                    log_fh.write(line + "\n")
                    log_fh.flush()
                except Exception:
                    pass

            # Parse stream event
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                accumulated_text.append(line)
                continue

            event_type = event.get("type", "")

            # Track tool usage for live display
            if event_type == "tool_use":
                current_tool = event.get("tool", event.get("name", "?"))
                print(f"[STREAM] Turn {turn_count}: using {current_tool}")

            # Track turns
            if event_type in ("assistant", "turn_end"):
                turn_count += 1

            # Capture result event (final metadata)
            if event_type == "result":
                result_event = event
                session_id_captured = event.get("session_id", "")

            # Capture assistant text
            if event_type == "assistant":
                msg = event.get("message", {})
                content = msg.get("content", "")
                if isinstance(content, str) and content:
                    accumulated_text.append(content)

            # Early abort: stuck or runaway
            if turn_count > max_turns * 1.5:
                print(f"[STREAM] Early abort: {turn_count} turns > {max_turns * 1.5} limit")
                proc.kill()
                break

    except Exception as e:
        print(f"[STREAM] Read error: {e}")
    finally:
        if log_fh:
            try:
                log_fh.close()
            except Exception:
                pass

    # Wait for process to finish
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()

    # Assemble response
    if result_event:
        response = result_event
        # Ensure "result" key exists
        if "result" not in response and accumulated_text:
            response["result"] = "\n".join(accumulated_text)
    else:
        # No result event — assemble from stream
        response = {
            "result": "\n".join(accumulated_text) if accumulated_text else "no output",
            "_stream_incomplete": True,
            "num_turns": turn_count,
        }

    if session_id_captured:
        response["session_id"] = session_id_captured

    # Read stderr
    try:
        stderr = proc.stderr.read() if proc.stderr else ""
        if stderr and proc.returncode != 0:
            response.setdefault("stderr", stderr.strip())
    except Exception:
        pass

    response["returncode"] = proc.returncode
    return response


def ensure_tb_branch(branch_name: str = "tb/nucleus-work") -> str:
    """Create or switch to TB's long-lived work branch. Returns branch name."""
    current = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    if current == branch_name:
        print(f"[BRANCH] Already on {branch_name}")
        return branch_name

    # Check if branch exists
    existing = git("branch", "--list", branch_name).strip()
    if existing:
        git("checkout", branch_name)
        # Merge latest main to stay current
        git("merge", "main", "--no-edit", "--quiet")
        print(f"[BRANCH] Switched to {branch_name} (merged main)")
    else:
        git("checkout", "-b", branch_name)
        print(f"[BRANCH] Created {branch_name} from {current}")

    return branch_name


def tb_branch_summary(branch_name: str = "tb/nucleus-work"):
    """Print summary of TB's work on branch vs main."""
    commits = git("log", f"main..{branch_name}", "--oneline")
    if not commits.strip():
        print(f"[BRANCH] No new commits on {branch_name}")
        return

    commit_lines = [l for l in commits.strip().split('\n') if l.strip()]
    print(f"\n[BRANCH] ═══════════════════════════════════════════")
    print(f"[BRANCH] {len(commit_lines)} commits on {branch_name} ahead of main:")
    for line in commit_lines[:20]:
        print(f"  {line}")
    if len(commit_lines) > 20:
        print(f"  ... and {len(commit_lines) - 20} more")

    diff_stat = git("diff", "--stat", f"main..{branch_name}")
    print(f"\n{diff_stat}")
    print(f"[BRANCH] Review: git diff main..{branch_name}")
    print(f"[BRANCH] Merge:  git checkout main && git merge {branch_name}")
    print(f"[BRANCH] ═══════════════════════════════════════════\n")


def run_driver(session_id: str, mode: str = "supervised", dry_run: bool = False,
               branch: str = "", max_tasks: int = 0):
    """Main driver loop — v2 session resume architecture.
    max_tasks: stop after N tasks (0 = unlimited, loops until kill switch or idle).
    """
    config = load_config()
    mode = mode or config.get("mode", "supervised")
    session_exhaustion_count = 0
    MAX_SESSION_ROTATIONS = 5  # safety: don't rotate infinitely
    driver_start_time = datetime.now()

    # ── Restore session ID from persisted state ──
    if not session_id and STATE_PATH.exists():
        try:
            prev_state = json.loads(STATE_PATH.read_text())
            prev_session = prev_state.get("session_id", "")
            if prev_session:
                session_id = prev_session
                print(f"[DRIVER] Restored session: {session_id}")
        except (json.JSONDecodeError, KeyError):
            pass

    # ── Branch mode: TB works on its own branch, no approval gates ──
    if branch:
        branch_name = ensure_tb_branch(branch)
        mode = "autonomous"  # no gates on TB's branch
        print(f"[BRANCH] TB working autonomously on {branch_name}")

    v3 = config.get("v3_features", {})
    v3_status = []
    if v3.get("classification_enabled"):
        v3_status.append("classify")
    if v3.get("scout_enabled"):
        v3_status.append("scout")
    if v3.get("tb_prompt_writer_enabled"):
        v3_status.append("tb_prompt")
    if v3.get("tb_reviewer_enabled"):
        v3_status.append("tb_review")
    if branch:
        v3_status.append("sparring")
    v3_label = f"v3 [{'+'.join(v3_status)}]" if v3_status else "v2"

    print(f"""
====================================================
  Third Brother Driver {v3_label} — Session Resume
----------------------------------------------------
  Mode:       {mode}{f' (branch: {branch})' if branch else ''}
  Session:    {session_id}
  Kill switch: touch .brain/driver/stop
  Config:     .brain/driver/config.json
====================================================
""")

    # Recover any stale tasks from previous crash
    recover_stale_tasks()

    handoff_summary = ""  # populated by rotate_with_handoff, consumed by next execute_task
    tasks_on_current_session = 0  # for delta context mode
    tasks_completed = 0  # for max_tasks limit

    # Warm up Ollama model to avoid cold-start timeouts on first task
    tb_model = os.environ.get("TB_MODEL") or config.get("v3_features", {}).get("tb_model", "third-brother:latest")
    if config.get("v3_features", {}).get("tb_prompt_writer_enabled") or \
       config.get("v3_features", {}).get("tb_reviewer_enabled"):
        _ollama_warmup(tb_model)

    while True:
        # ── Kill switch ──
        if check_kill_switch():
            print("[DRIVER] Kill switch activated. Stopping.")
            save_state("stopped")
            generate_session_report(session_id, driver_start_time)
            break

        # ── max_tasks limit (sparring / compound mode) ──
        if max_tasks > 0 and tasks_completed >= max_tasks:
            print(f"[DRIVER] Completed {tasks_completed}/{max_tasks} tasks. Done.")
            generate_session_report(session_id, driver_start_time)
            break

        # ── Pick task ──
        task = pick_next_task()
        if not task:
            if max_tasks > 0:
                # In bounded mode, don't idle-loop — just exit
                print(f"[DRIVER] No committed tasks. Done ({tasks_completed} completed).")
                break
            idle_minutes = config.get("idle_check_minutes", 30)
            print(f"[DRIVER] No committed tasks. Sleeping {idle_minutes}min...")
            save_state("idle", session_id=session_id)
            time.sleep(idle_minutes * 60)
            config = load_config()  # reload in case tasks were added
            continue

        task_id = task["id"]
        print(f"\n[DRIVER] ═══════════════════════════════════════════")
        print(f"[DRIVER] Task: {task['title']} ({task_id})")
        print(f"[DRIVER] Priority: {task.get('priority', '?')} | Scope: {', '.join(task.get('scope', ['**']))}")

        # ── RING 5: Commitment scoring (pre-flight) ──
        ring_commitment_score(task)

        # ── Dry run: validate pipeline, stop ──
        if dry_run:
            print("[DRY RUN] Would execute this task. Pipeline validated.")
            return

        # ── Supervised gate ──
        if mode == "supervised":
            try:
                choice = input("[Send / Skip / Quit] > ").strip().lower()
                if choice in ("quit", "q"):
                    save_state("stopped")
                    generate_session_report(session_id, driver_start_time)
                    print("[DRIVER] Stopped by user.")
                    return
                elif choice in ("skip", "s"):
                    update_task_status(task_id, "skipped")
                    print("[DRIVER] Task skipped.")
                    continue
                # else: send (Enter or "send")
            except (EOFError, KeyboardInterrupt):
                save_state("stopped")
                generate_session_report(session_id, driver_start_time)
                print("\n[DRIVER] Stopped.")
                return

        # ── RING 3: Event emit (task starting) ──
        ring_emit_event("task_started", task)

        # ── RING 4: Depth push ──
        ring_depth_push(task)

        # ── RING 7: Checkpoint save (starting) ──
        ring_checkpoint_save(task, progress=10)

        # ── Execute with per-task lock ──
        lock = get_driver_lock()
        _task_crashed = False
        try:
            if not lock.acquire():
                print("[DRIVER] Session locked by another process. Waiting...")
                ring_depth_pop()
                time.sleep(30)
                continue

            update_task_status(task_id, "in_progress")
            save_state("executing", task, session_id=session_id)

            pre_snapshot = snapshot_working_tree()
            pre_staged = capture_staged_files()
            # Write session manifest so pre-commit hook can detect contamination
            try:
                MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
                MANIFEST_PATH.write_text(json.dumps({
                    "session_id": session_id or "",
                    "task_id": task.get("id", ""),
                    "started_at": datetime.now().isoformat(),
                    "pre_staged_files": sorted(pre_staged),
                }, indent=2))
            except Exception:
                pass
            # Save HEAD before execution so we can detect committed changes
            try:
                _pre_head = subprocess.run(
                    ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                    timeout=5, cwd=str(PROJECT_ROOT),
                ).stdout.strip()
            except Exception:
                _pre_head = ""
            response = execute_task(task, session_id, config,
                                    system_context=handoff_summary,
                                    session_task_count=tasks_on_current_session)
            handoff_summary = ""  # consumed

            # Auto-capture session ID from first Claude call (for branch mode)
            if not session_id and response.get("session_id"):
                session_id = response["session_id"]
                print(f"[DRIVER] Captured session: {session_id}")

            # ── v3 Phase D: TB Review before commit ──
            # Check unstaged, staged, AND committed changes (Claude often commits during session)
            git_diff_text = ""
            try:
                # Unstaged changes
                diff_result = subprocess.run(
                    ["git", "diff", "--stat"], capture_output=True, text=True, timeout=10,
                    cwd=str(PROJECT_ROOT),
                )
                git_diff_text = diff_result.stdout[:3000]
                # Staged changes
                if not git_diff_text.strip():
                    diff_result = subprocess.run(
                        ["git", "diff", "--cached", "--stat"], capture_output=True, text=True,
                        timeout=10, cwd=str(PROJECT_ROOT),
                    )
                    git_diff_text = diff_result.stdout[:3000]
                # Changes committed during session (Claude Code often commits)
                if not git_diff_text.strip() and _pre_head:
                    diff_result = subprocess.run(
                        ["git", "log", "--stat", "--format=", f"{_pre_head}..HEAD"],
                        capture_output=True, text=True, timeout=10, cwd=str(PROJECT_ROOT),
                    )
                    git_diff_text = diff_result.stdout[:3000]
            except Exception:
                pass

            # ── Execution verification (Frontier 1: GROUND — deterministic, no LLM) ──
            verification_result = None
            if config.get("execution_verification_enabled", True):
                try:
                    from execution_verifier import verify_execution, build_calibration_dpo
                    _verify_config = dict(config)
                    _verify_config["_current_task"] = task
                    verification_result = verify_execution(
                        git_diff_text, _pre_head, _verify_config, PROJECT_ROOT)
                    response["verification"] = verification_result
                    _v = verification_result
                    _tier_str = f"tiers_passed={_v['tiers_passed']} failed={_v['tiers_failed']}"
                    print(f"[VERIFY] {'PASS' if _v['verified'] else 'FAIL'} "
                          f"({_v['duration_s']}s) {_tier_str}")
                    for sig in _v.get("signals", []):
                        status = "PASS" if sig.get("passed") else "FAIL"
                        target = sig.get("file", sig.get("module", ""))
                        err = f" — {sig['error']}" if sig.get("error") else ""
                        print(f"[VERIFY]   Tier {sig.get('tier', '?')}: "
                              f"{sig.get('check', '?')} {status} {target}{err}")
                    # Log every verification run (audit trail)
                    _vlog = {"task_id": task.get("id", ""), **_v,
                             "ts": datetime.now().isoformat()}
                    with open(VERIFICATION_LOG_PATH, "a") as _vf:
                        _vf.write(json.dumps(_vlog, default=str) + "\n")
                    if not _v["verified"]:
                        _log_hard_negative(task, "verification_failed",
                            f"Tiers failed: {_v['tiers_failed']}, "
                            f"signals: {json.dumps(_v['signals'][:5], default=str)}")
                        # Calibration DPO (Frontier 3: COMPOUND signal)
                        if config.get("calibration_dpo_enabled", True):
                            cal_dpo = build_calibration_dpo(task, response, _v)
                            if cal_dpo:
                                with open(SPARRING_DPO_PATH, "a") as _f:
                                    _f.write(json.dumps(cal_dpo, default=str) + "\n")
                                print("[VERIFY] Calibration DPO captured")
                        # Hard gate: block task + escalate to ALIGN
                        if config.get("execution_verification_hard_gate", False):
                            task["status"] = "blocked"
                            task["blocked_reason"] = "GROUND verification failed"
                            print(f"[VERIFY] HARD GATE: task {task.get('id', '?')} → blocked")
                            # Write escalation for human review (ALIGN frontier)
                            _verdicts_path = DRIVER_DIR / "human_verdicts.jsonl"
                            _escalation = {
                                "task_id": task.get("id", ""),
                                "verdict": "pending",
                                "source": "ground_hard_gate",
                                "verification_receipt": _v,
                                "task_description": task.get("description", "")[:500],
                                "session_id": session_id if 'session_id' in dir() else "",
                                "ts": datetime.now().isoformat(),
                            }
                            _verdicts_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(_verdicts_path, "a") as _vf:
                                _vf.write(json.dumps(_escalation, default=str) + "\n")
                            print("[VERIFY] Escalation written to human_verdicts.jsonl")
                except Exception as e:
                    print(f"[VERIFY] Error (non-fatal): {e}")

            # ── Programmatic scope check (hard gate — no LLM judgment) ──
            task_scope = task.get("scope", ["**"])
            scope_violations = check_scope_violations(git_diff_text, task_scope)
            if scope_violations:
                violation_list = ", ".join(scope_violations[:10])
                print(f"[SCOPE] ESCALATE: {len(scope_violations)} file(s) outside scope "
                      f"{task_scope}: {violation_list}")
                review = {
                    "verdict": "ESCALATE",
                    "reason": f"Scope violation: {violation_list} modified outside allowed scope {task_scope}",
                    "confidence": 1.0,
                }
                log_alert("scope_violation", task_id, "escalated",
                          f"Files outside scope: {violation_list}", "WARNING")
            else:
                try:
                    review = tb_review_output(task, response, git_diff_text, config)
                    # Reviewer answering is the survived event; downstream verdict
                    # (ACCEPT/DEEPEN/ESCALATE) is captured separately in CSR via the
                    # outcome path below.
                    _fw_record_survived("phase_d_reviewer", task_id, config)
                except Exception as e:
                    _fw_file_ticket("phase_d_reviewer", task_id, str(e), config)
                    review = {
                        "verdict": "ESCALATE",
                        "reason": f"reviewer crashed: {e}",
                        "confidence": 0.0,
                    }

            response["tb_review"] = review
            _review_action = None  # "deepen" or "escalate" or None

            if review["verdict"] == "DEEPEN":
                max_chain = config.get("max_deepen_chain",
                                       v3.get("max_deepen_retries", 1))
                deepen_count = 0
                deepen_notes = ""

                while review["verdict"] == "DEEPEN" and deepen_count < max_chain:
                    deepen_count += 1
                    deepen_notes = review.get("deepen_notes", review.get("reason", ""))
                    print(f"[REVIEW] DEEPEN {deepen_count}/{max_chain}: inline follow-up")
                    pre_result = response.get("result", "")
                    response, review = deepen_follow_up(
                        task, deepen_notes, session_id, config)
                    response["tb_review"] = review
                    # Capture B: DEEPEN DPO pair
                    if config.get("training_capture_enabled", True):
                        _capture_deepen_dpo(task, pre_result, response.get("result", ""),
                                            deepen_notes, deepen_count)

                if review["verdict"] == "DEEPEN":
                    # Exhausted inline retries → fall back to re-queue
                    _review_action = "deepen"
                    task["description"] += (f"\n\n## Review Notes "
                                            f"(deepen x{deepen_count})\n{deepen_notes}")
                    update_task_status(task_id, "committed")
                    print(f"[REVIEW] DEEPEN: exhausted {max_chain} inline retries, re-queuing")
                    _log_hard_negative(task, "deepen_exhausted", deepen_notes)
                elif review["verdict"] == "ESCALATE":
                    _review_action = "escalate"
                    log_alert("tb_review_escalate", task_id, "escalated",
                              review.get("reason", ""), "WARNING")
                    update_task_status(task_id, "blocked")
                    print(f"[REVIEW] ESCALATE after deepen: {task_id} blocked")
                    _log_hard_negative(task, "escalated_after_deepen", review.get("reason", ""))
            elif review["verdict"] == "ESCALATE":
                _review_action = "escalate"
                log_alert("tb_review_escalate", task_id, "escalated",
                          review.get("reason", ""), "WARNING")
                update_task_status(task_id, "blocked")
                print(f"[REVIEW] ESCALATE: {task_id} blocked for human review")
                _log_hard_negative(task, "escalated", review.get("reason", ""))

            # ── Sparring: score Phase C+D output for training data ──
            if config.get("training_capture_enabled", True):
                response["git_diff"] = git_diff_text  # pass diff to eval
                _spar_phase_cd(task, response, review, config)

            # ── Capture A: execution-grounded DPO (ACCEPT only) ──
            if not _review_action and config.get("training_capture_enabled", True):
                _capture_execution_dpo(task, response, git_diff_text, config)

            if not _review_action:
                # ACCEPT — Auto-commit only files changed by Claude Code session
                auto_commit(task, pre_snapshot=pre_snapshot, pre_staged=pre_staged)
        except Exception as exc:
            # Session crash: mark task failed so it doesn't stay in_progress forever
            _task_crashed = True
            failure_reason = f"session_crash: {type(exc).__name__}: {str(exc)[:200]}"
            print(f"[DRIVER] CRASH during {task_id}: {failure_reason}")
            update_task_status(task_id, "failed", failure_reason=failure_reason)
            save_state("crash_recovered", task, session_id=session_id)
            log_alert("session_crash", task_id, "failed", failure_reason, "ERROR")
            ring_depth_pop()
            ring_emit_event("task_crashed", task, {
                "task_id": task_id, "error": failure_reason,
            })
        finally:
            lock.release()

        if _task_crashed:
            continue

        # ── Session accounting: runs for ALL tasks, regardless of review verdict ──
        tasks_on_current_session += 1

        # ── Adaptive compaction: check BEFORE skipping on review action ──
        ctx = response.get("context_metrics", {})
        compact_turns = config.get("compact_trigger_turns", 40)
        compact_bytes = config.get("compact_trigger_bytes", 2_097_152)
        compact_pct = config.get("compact_trigger_pressure_pct", 60)
        if session_id and (
            ctx.get("turns", 0) > compact_turns
            or ctx.get("bytes", 0) > compact_bytes
            or ctx.get("pressure_pct", 0) > compact_pct
        ):
            print(f"[COMPACT] Threshold exceeded (turns={ctx.get('turns', 0)}, "
                  f"bytes={ctx.get('bytes', 0) // 1024}KB, "
                  f"pressure={ctx.get('pressure_pct', 0)}%) — compacting")
            session_id, handoff_summary = rotate_with_handoff(
                session_id, branch, config)
            tasks_on_current_session = 0
            save_state("rotating", session_id=session_id)

        # Handle review actions outside the lock
        if _review_action:
            ring_depth_pop()
            continue

        # ── RING 7: Checkpoint save (completed) ──
        ring_checkpoint_save(task, progress=100)

        # ── RING 4: Depth pop ──
        ring_depth_pop()

        # ── Post-flight: log and update (lock released) ──
        duration = response.get("duration_seconds", 0)
        turns = response.get("num_turns", response.get("turns", 0))
        result_text = response.get("result", "")

        # Determine outcome
        if response.get("outcome") == "session_busy":
            # Session still in use — reset task and wait
            update_task_status(task_id, "committed")
            print(f"[DRIVER] Session busy. Task {task_id} reset. Waiting for session to free...")
            time.sleep(120)
            continue
        elif response.get("outcome") == "timeout":
            outcome = "timeout"
        elif result_text and "prompt is too long" in result_text.lower():
            # Session context exhausted — rotate to fresh session
            outcome = "session_exhausted"
            update_task_status(task_id, "committed")
            session_exhaustion_count += 1
            log_run(task, "session_exhausted", turns=turns, duration_seconds=duration,
                    failure_reason="prompt too long",
                    retry_count=response.get("retry_count", 0),
                    session_id=session_id)

            if session_exhaustion_count >= MAX_SESSION_ROTATIONS:
                print(f"[DRIVER] Session exhausted {session_exhaustion_count} times. Stopping.")
                generate_session_report(session_id, driver_start_time)
                break

            # Drop --resume flag: next execute_task will start fresh
            old_session = session_id
            session_id = ""  # empty = no --resume flag → fresh session
            tasks_on_current_session = 0
            save_state("rotating", session_id=session_id)
            print(f"[DRIVER] Session exhausted. Rotating: {old_session[:12]}... → fresh session")
            continue
        elif result_text and "stuck" not in result_text.lower()[:100]:
            outcome = "completed"
        else:
            outcome = "completed"  # trust Claude Code's output

        # (Compaction check moved above _review_action gate so it runs for all tasks)

        # ── RING 9: Self-heal on failure ──
        if outcome in ("timeout", "error", "blocked"):
            ring_selfheal_on_failure(task, result_text[:500])

        update_task_status(task_id, outcome)
        tasks_completed += 1
        ctx_metrics = response.get("context_metrics")
        save_state(outcome, task, session_id=session_id, context_metrics=ctx_metrics)

        if outcome == "completed":
            write_session_state(session_id, branch,
                                [t for t in load_tasks() if t.get("status") == "completed"],
                                config)

        # ── RING 10: Quick eval every 5th completed task ──
        completed_count = sum(1 for t in load_tasks() if t.get("status") == "completed")
        eval_score = None
        if outcome == "completed" and completed_count > 0 and completed_count % 5 == 0:
            eval_score = ring_eval_quick(task_id)
            if eval_score is not None:
                check_eval_regression(eval_score)

        log_run(task, outcome, turns=turns, duration_seconds=duration,
                retry_count=response.get("retry_count", 0),
                session_id=session_id, eval_score=eval_score)

        log_shadow_raft(
            task=task,
            instruction=response.get("message", ""),
            response=result_text,
            session_id=session_id,
            rag_results=response.get("rag_results", []),
            context=response.get("context", ""),
            turn_count=turns,
            outcome=outcome,
            duration_ms=duration * 1000,
            classification=response.get("classification"),
            scout_findings=response.get("scout_findings"),
            tb_review=response.get("tb_review"),
        )

        # Capture D: outcome SFT (fires for ALL outcomes)
        if config.get("training_capture_enabled", True):
            _capture_outcome_sft(task, response, outcome, config)

        # Archive full Claude Code session transcript (platinum training data)
        archive_session_transcript(
            session_id=session_id,
            task=task,
            outcome=outcome,
        )

        # Layer 0: Inline conversation ingest
        if config.get("layer0_ingest_enabled", True) and session_id:
            try:
                from mcp_server_nucleus.runtime.conversation_ops import ingest_conversations
                l0 = ingest_conversations(mode="single", session_id=session_id)
                l0_t, l0_p = l0.get("turns_created", 0), l0.get("preferences_found", 0)
                if l0_t or l0_p:
                    print(f"[LAYER 0] {l0_t} turns, {l0_p} DPO ({l0.get('duration_ms', 0)}ms)")
            except Exception as e:
                print(f"[LAYER 0] Ingest failed (non-fatal): {e}")

        # ── RING 8: Archive turn for training pipeline ──
        ring_archive_turn(task, outcome, response, duration)

        # ── RING 3: Event emit (task completed) ──
        ring_emit_event("task_completed", task, {
            "task_id": task["id"], "outcome": outcome,
            "duration": duration, "turns": turns,
        })

        # ── Webhook: notify external systems ──
        fire_task_webhook(task, outcome, duration, turns, config)

        apply_trust_ladder(config)

        print(f"[DRIVER] Task {task_id}: {outcome} ({duration}s, {turns} turns)")
        print(f"[DRIVER] ═══════════════════════════════════════════\n")

        # ── RING 1: Heartbeat check between tasks ──
        ring_heartbeat_check()

        # ── Stale session detection ──
        if check_stale_session(session_id, config):
            print(f"[DRIVER] Session stale. Rotating to fresh session.")
            session_id = ""  # next execute_task starts fresh

        # ── RING 6: Consolidation (every 5 tasks) ──
        if completed_count % 5 == 0 and completed_count > 0:
            ring_consolidation()

        # ── RING 8+: Export training data (every 10 tasks) ──
        if completed_count % 10 == 0 and completed_count > 0:
            ring_export_training()

        # ── RING 9: Retrain readiness check (every 10 tasks) ──
        if completed_count % 10 == 0 and completed_count > 0:
            ring_retrain_check(completed_count)

        # Reload config between tasks (in case it was updated)
        config = load_config()


# ═══════════════════════════════════════════════════════════════
# CLI COMMANDS
# ═══════════════════════════════════════════════════════════════

def cmd_add_task():
    """Interactive task addition."""
    print("Add a new task:")
    title = input("  Title: ").strip()
    if not title:
        print("Cancelled.")
        return

    print("  Description (end with empty line):")
    desc_lines = []
    while True:
        line = input("  ")
        if line == "":
            break
        desc_lines.append(line)
    description = "\n".join(desc_lines)

    scope_input = input("  Scope (comma-separated globs, default **): ").strip()
    scope = [s.strip() for s in scope_input.split(",")] if scope_input else ["**"]

    priority = int(input("  Priority (1=highest, default 5): ").strip() or "5")

    task = add_task(title, description, scope, priority)
    print(f"  Created: {task['id']} — {task['title']}")


def cmd_list_tasks():
    """Show all tasks."""
    tasks = load_tasks()
    if not tasks:
        print("No tasks.")
        return

    for t in tasks:
        status_icon = {
            "committed": "+", "in_progress": ">", "completed": "v",
            "blocked": "x", "skipped": "-",
        }.get(t["status"], "?")
        print(f"  [{status_icon}] {t['id']}  P{t.get('priority', '?')}  {t['title']}  ({t['status']})")


def cmd_trust_status():
    """Show trust ladder status."""
    config = load_config()
    runs = load_runs()
    phase = config.get("trust_ladder", {}).get("current_phase", 1)
    mode = PHASE_MODES.get(phase, "supervised")

    print(f"  Phase: {phase} ({mode})")
    print(f"  Total runs: {len(runs)}")

    if runs:
        completed = sum(1 for r in runs if r.get("outcome") == "completed")
        print(f"  Completed: {completed}/{len(runs)} ({completed/len(runs):.0%})")

    old, new, reason = evaluate_trust_ladder(config)
    if old != new:
        print(f"  Pending: Phase {old} -> Phase {new} ({reason})")
    else:
        print(f"  Status: {reason}")


def cmd_validate_shadow_log():
    """Scan shadow_log.jsonl and report corrupt/incomplete entries."""
    REQUIRED_FIELDS = ("task_id", "query", "response", "outcome", "oracle_chunks")
    if not SHADOW_LOG_PATH.exists():
        print(f"  shadow_log not found: {SHADOW_LOG_PATH}")
        return
    lines = SHADOW_LOG_PATH.read_text().strip().split("\n")
    issues = []
    for lineno, line in enumerate(lines, start=1):
        if not line.strip():
            issues.append((lineno, "blank line"))
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as e:
            issues.append((lineno, f"corrupt JSON: {e}"))
            continue
        for field in REQUIRED_FIELDS:
            if field not in entry:
                issues.append((lineno, f"missing field: {field}"))
        if not entry.get("query"):
            issues.append((lineno, "empty instruction (query)"))
        if not entry.get("response"):
            issues.append((lineno, "empty response"))

    total = len(lines)
    bad = len({ln for ln, _ in issues})
    print(f"  Scanned {total} entries, {bad} with issues:")
    if not issues:
        print("  All entries valid.")
    else:
        for lineno, msg in issues:
            print(f"  L{lineno}: {msg}")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def run_sparring_mode(rounds: int, session_id: str, branch: str):
    """Run sparring rounds from the task bank through the full driver pipeline.

    Unlike standalone sparring (tb_sparring.py), this executes tasks on the real
    codebase — training data is execution-grounded, not synthetic evaluation.
    """
    import random

    if not SPARRING_TASK_BANK_PATH.exists():
        print(f"[SPARRING] Task bank not found: {SPARRING_TASK_BANK_PATH}")
        return

    with open(SPARRING_TASK_BANK_PATH) as f:
        bank = json.load(f)

    random.shuffle(bank)
    tasks_to_run = bank[:rounds]

    print(f"[SPARRING] Loaded {len(bank)} tasks, running {len(tasks_to_run)} rounds on branch {branch}")

    # Inject sparring tasks into tasks.json
    existing_tasks = load_tasks()
    sparring_ids = []
    for i, entry in enumerate(tasks_to_run):
        task_id = f"sparring-{i:03d}"
        sparring_ids.append(task_id)

        # Extract scope from "File: path" in task description
        desc = entry.get("task", "")
        scope = ["backend/**", "providers/**", "scripts/**", "tests/**"]
        file_match = re.search(r"File:\s*(\S+)", desc)
        if file_match:
            file_path = file_match.group(1).rstrip(".,;")
            # Use the directory as scope
            if "/" in file_path:
                scope = [str(Path(file_path).parent / "**"), file_path]
            else:
                scope = [file_path]

        task = {
            "id": task_id,
            "title": entry["task"][:80],
            "description": entry["task"],
            "scope": scope,
            "priority": 1,
            "status": "committed",
            "source": "sparring_bank",
        }
        existing_tasks.append(task)

    save_tasks(existing_tasks)

    try:
        run_driver(session_id, mode="autonomous", branch=branch, max_tasks=rounds)
    finally:
        # Clean up sparring tasks from tasks.json
        tasks = load_tasks()
        tasks = [t for t in tasks if t.get("id") not in sparring_ids]
        save_tasks(tasks)
        print(f"[SPARRING] Cleaned up {len(sparring_ids)} sparring tasks from tasks.json")


def run_compound_mode(branch: str, sparring_rounds: int = 5):
    """The exponential loop: real tasks → sparring on hard negatives → export training.

    One command that compounds:
      1. Run all committed real tasks (captures DPO/SFT at 4 points)
      2. Count hard negatives accumulated during real tasks
      3. Sparring round on hard negatives + task bank (more captures)
      4. Export all training data to inbox

    Usage: python3 scripts/third_brother_driver.py --compound
    """
    print("=" * 60)
    print("  COMPOUND MODE — Work = Training")
    print("  real tasks → sparring → export")
    print("=" * 60)

    # Pre-flight: verify Ollama + TB model are running (needed for training captures)
    config = load_config()
    tb_model = os.environ.get("TB_MODEL") or config.get("v3_features", {}).get("tb_model", "third-brother:latest")
    tb_model_base = tb_model.split(":")[0]
    try:
        tb_check = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=5)
        if tb_model_base not in tb_check.stdout:
            print(f"[COMPOUND] WARNING: {tb_model} not found in Ollama — "
                  "tb_prompt will be empty, Capture A DPO pairs will be lost")
            print(f"[COMPOUND] Fix: ollama pull {tb_model}")
        else:
            print(f"[COMPOUND] Pre-flight OK: Ollama + {tb_model} available")
    except Exception:
        print("[COMPOUND] WARNING: Ollama not running — training captures will be degraded")
        print("[COMPOUND] Fix: ollama serve")

    # Phase 1: Real tasks (bounded — exits when no committed tasks)
    print("\n[COMPOUND] Phase 1/3: Running real tasks...")
    run_driver("", mode="autonomous", branch=branch, max_tasks=sparring_rounds)

    # Phase 2: Sparring on hard negatives + task bank
    # Count how many hard negatives were added during Phase 1
    hard_neg_count = 0
    if SPARRING_TASK_BANK_PATH.exists():
        with open(SPARRING_TASK_BANK_PATH) as f:
            bank = json.load(f)
        hard_neg_count = sum(1 for t in bank if t.get("source") == "hard_negative")

    rounds = max(sparring_rounds, hard_neg_count)
    if rounds > 0:
        print(f"\n[COMPOUND] Phase 2/3: Sparring ({rounds} rounds, "
              f"{hard_neg_count} hard negatives in bank)...")
        run_sparring_mode(rounds, "", branch)
    else:
        print("\n[COMPOUND] Phase 2/3: No sparring tasks — skipped")

    # Phase 3: Export training data
    print("\n[COMPOUND] Phase 3/3: Exporting training data...")
    ring_export_training()

    # Summary
    inbox_dir = BRAIN_PATH / "training" / "inbox"
    dpo_count = sft_count = 0
    dpo_path = inbox_dir / "sparring_dpo.jsonl"
    sft_path = inbox_dir / "sparring_sft.jsonl"
    if dpo_path.exists():
        dpo_count = sum(1 for _ in open(dpo_path))
    if sft_path.exists():
        sft_count = sum(1 for _ in open(sft_path))

    print("\n" + "=" * 60)
    print("  COMPOUND COMPLETE")
    print(f"  DPO pairs in inbox: {dpo_count}")
    print(f"  SFT entries in inbox: {sft_count}")
    print(f"  Hard negatives in bank: {hard_neg_count}")
    print(f"  Next run: these feed back in → exponential")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Third Brother Autonomous Driver v2 — Session Resume Architecture"
    )
    parser.add_argument("--session", help="Claude Code session ID to resume")
    parser.add_argument("--auto", action="store_true", help="Autonomous mode (no approval gate)")
    parser.add_argument("--branch", nargs="?", const="tb/nucleus-work", default="",
                        help="Work on a branch (default: tb/nucleus-work). Autonomous, commits to branch, sparring inline.")
    parser.add_argument("--dry-run", action="store_true", help="Validate pipeline without executing")
    parser.add_argument("--add-task", action="store_true", help="Add a task interactively")
    parser.add_argument("--list-tasks", action="store_true", help="List all tasks")
    parser.add_argument("--trust-status", action="store_true", help="Show trust ladder status")
    parser.add_argument("--export-training", action="store_true", help="Export training data now")
    parser.add_argument("--validate-shadow-log", action="store_true",
                        help="Scan shadow_log.jsonl and report corrupt/incomplete entries")
    parser.add_argument("--sparring", nargs="?", const=10, type=int,
                        help="Run N sparring rounds from task bank (default: 10)")
    parser.add_argument("--compound", nargs="?", const=5, type=int,
                        help="Exponential loop: real tasks → sparring (N rounds, default 5) → export training")
    parser.add_argument("--verbose", action="store_true",
                        help="Log every Ollama call's input and output to stdout")
    args = parser.parse_args()

    global VERBOSE
    VERBOSE = args.verbose

    # Ensure driver directory exists
    DRIVER_DIR.mkdir(parents=True, exist_ok=True)

    if args.add_task:
        cmd_add_task()
    elif args.list_tasks:
        cmd_list_tasks()
    elif args.trust_status:
        cmd_trust_status()
    elif args.export_training:
        ring_export_training()
        print("Training export complete.")
    elif args.validate_shadow_log:
        cmd_validate_shadow_log()
    elif args.compound is not None:
        branch = args.branch or "tb/nucleus-work"
        run_compound_mode(branch, sparring_rounds=args.compound)
    elif args.sparring is not None:
        run_sparring_mode(args.sparring, args.session or "",
                          args.branch or "tb/sparring-test")
    elif args.branch:
        # Branch mode: session is optional (auto-captures from first Claude call)
        session = args.session or ""
        run_driver(session, mode="autonomous", dry_run=args.dry_run, branch=args.branch)
    elif args.session:
        mode = "autonomous" if args.auto else "supervised"
        run_driver(args.session, mode=mode, dry_run=args.dry_run, branch=args.branch)
    else:
        parser.print_help()
        print("\nExample: python3 scripts/third_brother_driver.py --session abc123")
        print("         python3 scripts/third_brother_driver.py --branch")
        print("         python3 scripts/third_brother_driver.py --compound  # the exponential loop")


if __name__ == "__main__":
    main()
