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

# Force unbuffered stdout so streaming (tail -f) works in background mode
if not sys.stdout.line_buffering:
    sys.stdout.reconfigure(line_buffering=True)
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple, Any

# ── Global flags ─────────────────────────────────────────────
VERBOSE = False  # Set by --verbose; logs every Ollama call's input/output
_PREV_RUNTIME_CTX: dict = {}  # Set after each task; read by Phase C + D (Batcomputer)
_LAST_DCAS_REPLAYED: list = []  # Populated by ring_distill_replay; read by run_driver

# ── Phase 0.5 sovereignty consult (TB axis) ──────────────────
# Mirror of the endpoint-side gate (PR #219). The driver runs autonomously
# (sparring/compound/cron/audit), so without this primitive any driver-fired
# turn that touches sovereign content (TB internals, family architecture,
# identity sparring) leaks into shadow_log + DPO archive unconditionally.
#
# Each task carries a `sovereignty` field (`public|guarded|sovereign`); when
# `sovereign`, every corpus-write site short-circuits — no shadow_log entry,
# no DPO/SFT pair, no verdict, no scorecard. Default `guarded` (more
# conservative than the endpoint's `public` default) because the driver
# isn't an interactive surface — user can't classify each turn at write
# time.
#
# Override per invocation via --sovereignty flag or TB_DRIVER_SOVEREIGNTY
# env var. Override per task via the `sovereignty` field on the task dict.
_VALID_SOVEREIGNTY = {"public", "guarded", "sovereign"}
_DRIVER_DEFAULT_SOVEREIGNTY = (
    os.environ.get("TB_DRIVER_SOVEREIGNTY", "guarded").lower()
)
if _DRIVER_DEFAULT_SOVEREIGNTY not in _VALID_SOVEREIGNTY:
    _DRIVER_DEFAULT_SOVEREIGNTY = "guarded"


def _should_write_corpus(task_or_sov) -> bool:
    """True if the task/sovereignty allows corpus writes.

    Accepts either a task dict (reads `task.get('sovereignty')`) or a
    sovereignty string directly. Missing/None → DRIVER default. Any value
    other than `'sovereign'` permits writes; `'sovereign'` short-circuits.
    """
    if isinstance(task_or_sov, dict):
        sov = task_or_sov.get("sovereignty") or _DRIVER_DEFAULT_SOVEREIGNTY
    else:
        sov = task_or_sov or _DRIVER_DEFAULT_SOVEREIGNTY
    return str(sov).lower() != "sovereign"

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


# Nucleus infrastructure writes — ambient, not task output
_INFRA_PREFIXES = (
    ".brain/", "nucleus-mcp", "mcp-server-nucleus/scripts/sync_public_repo",
)


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
        # Skip Nucleus infrastructure writes (ambient, not task output)
        if any(filepath.startswith(p) for p in _INFRA_PREFIXES):
            continue
        if not _file_matches_scope(filepath, scope):
            violations.append(filepath)
    return violations


def _filter_diff_by_snapshot(git_diff_text: str, pre_snapshot: set) -> str:
    """Remove git diff --stat lines for files already dirty before task execution."""
    if not pre_snapshot or not git_diff_text:
        return git_diff_text
    # Parse porcelain status lines into filenames
    pre_dirty = set()
    for line in pre_snapshot:
        parts = line.strip().split(None, 1)
        if len(parts) >= 2:
            # Handle renames: "R  old -> new"
            pre_dirty.add(parts[1].split(" -> ")[-1].strip('"'))
    if not pre_dirty:
        return git_diff_text
    filtered = []
    for line in git_diff_text.strip().splitlines():
        if "|" not in line:
            # Summary line like " 5 files changed, ..."
            continue
        filepath = line.strip().split("|")[0].strip()
        if filepath in pre_dirty:
            continue
        # git diff --stat truncates long paths with "..." prefix
        if filepath.startswith("...") and any(
            p.endswith(filepath[3:]) for p in pre_dirty
        ):
            continue
        filtered.append(line)
    return "\n".join(filtered)


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

STRUCTURED_AUDIT_TEMPLATE = """## Plan Audit: {title}
Source: {plan_filename}

### Execution Phases (follow in order)

#### Phase A: CLAIMS
List every testable claim this plan makes.
For each change: what file, what function, what it should do after.

#### Phase B: VERIFY CURRENT STATE
For each claim, check the current code with evidence.
Use Grep/Read to confirm. Mark each:
- DONE (file:line) — exists as planned
- MISSING (searched, not found) — needs implementation
- PARTIAL (explain gap) — partially implemented

#### Phase C: PLAN
For MISSING/PARTIAL claims, describe exact changes needed.
File path, function name, what changes, dependencies.
{complexity_expansion}

#### Phase D: IMPLEMENT
Make the changes from Phase C, in dependency order.
Run tests if applicable.

#### Phase E: SUMMARY
Output a table: Claim | File | Status | Action Taken
The driver will independently run verification after you complete (GT40).

### The Plan

{plan_text}

### Constraints
- Do NOT commit changes (the driver handles commits)
- Do NOT modify files outside the plan's scope
- If a planned change conflicts with current code, skip it and note why
"""


def _classify_plan_complexity(plan_text: str, scope: List[str]) -> Dict:
    """Classify plan complexity → controls audit prompt template + turn budget."""
    file_count = len(scope)
    changes = re.findall(r"^\s*(?:\d+\.|-|\*)\s+.*`", plan_text, re.MULTILINE)
    change_count = len(changes)
    sections = re.findall(r"^##+ ", plan_text, re.MULTILINE)

    if file_count <= 2 and change_count <= 3:
        return {"level": "simple", "file_count": file_count,
                "change_count": change_count, "recommended_turns": 15}
    if file_count > 5 or change_count > 7 or len(sections) > 8:
        return {"level": "complex", "file_count": file_count,
                "change_count": change_count, "recommended_turns": 35}
    return {"level": "medium", "file_count": file_count,
            "change_count": change_count, "recommended_turns": 25}


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

    # Plan audit tasks: the plan IS the specification — no scout, tight turns
    if task.get("source") == "plan_audit":
        return {
            "type": "investigate",
            "needs_scout": False,
            "max_turns": task.get("max_turns", 25),
            "tools": v3.get("executor_tools_investigate", "Bash,Read,Glob,Grep,WebSearch"),
            "confidence": 1.0,
            "scout_turns": 0,
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
                     num_predict: int = -1, temperature: float = 0.7,
                     stop: list = None) -> tuple:
    """Call Ollama via HTTP API (not CLI subprocess). Returns (response_text, duration_ms).

    Uses the same pattern proven in tb_sparring.py. HTTP API is faster than
    subprocess (no process fork) and doesn't include model loading in timeout.

    stop: optional list of literal stop sequences forwarded to Ollama options.stop.
    """
    import urllib.request

    options = {"num_predict": num_predict, "temperature": temperature}
    if stop:
        options["stop"] = list(stop)

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": options,
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
            text = data.get("response", "").strip()
            # Strip qwen3 chain-of-thought — closed or unclosed
            think_end = text.find("</think>")
            if think_end >= 0:
                text = text[think_end + 8:].strip()
            elif text.startswith("<think>"):
                text = text[7:].strip()
            return text, duration_ms
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
# TB ENRICHMENT — situational awareness for prompt writer
# ═══════════════════════════════════════════════════════════════

def _gather_recent_history(task: Dict) -> str:
    """Build situational awareness block for TB prompt writer.

    Collects: previous attempts at this task, queue state, recent git log.
    Returns a text block to inject into the TB prompt, or empty string.
    """
    sections = []
    task_id = task.get("id", "")

    # 1. Previous attempts at this task (from task description amendments)
    desc = task.get("description", "")
    prev_failures = [line for line in desc.split("\n") if "Previous failure:" in line]
    if prev_failures:
        sections.append(f"Previous attempts ({len(prev_failures)}):")
        for pf in prev_failures[-3:]:  # last 3
            sections.append(f"  {pf.strip()[:200]}")

    # 2. Queue state
    try:
        tasks = load_tasks()
        committed = sum(1 for t in tasks if t.get("status") == "committed")
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        blocked = sum(1 for t in tasks if t.get("status") == "blocked")
        sections.append(f"Queue: {committed} pending, {completed} done, {blocked} blocked")
    except Exception:
        pass

    # 3. Recent git log (last 5 commits, one line each)
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True, text=True, timeout=5,
            cwd=str(BRAIN_PATH.parent),
        )
        if result.returncode == 0 and result.stdout.strip():
            sections.append("Recent commits:")
            for line in result.stdout.strip().splitlines():
                sections.append(f"  {line[:120]}")
    except Exception:
        pass

    # 4. CSR snapshot
    try:
        csr_path = BRAIN_PATH / "flywheel" / "csr.json"
        if csr_path.exists():
            csr = json.loads(csr_path.read_text())
            ratio = csr.get("ratio", 1.0)
            sections.append(f"CSR: {ratio:.1%} ({csr.get('claims_total', 0)} claims)")
    except Exception:
        pass

    return "\n".join(sections) if sections else "(no history available)"


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
    history_text = _gather_recent_history(task)

    ollama_prompt = f"""You are Third Brother, the project manager for the Nucleus codebase.
Write a detailed instruction (300-500 words) for Claude Code to execute this task.

Task: {task.get('title', '')}
Description: {task.get('description', '')}

Brain Context (from RAG):
{context[:2000]}

Scout Investigation Findings:
{scout_text[:2000] if scout_text else '(no scout run)'}

Situational Awareness:
{history_text}

Your instruction must include:
- Specific file paths and line numbers from scout findings
- Root cause analysis (what is broken and why)
- Recommended approach (not just "fix it")
- Constraints (scope, files to modify, files NOT to modify)
- How to verify the fix works

Write the instruction now:"""

    # Inject task run history so TB knows past attempts
    task_id = task.get("id", "")
    task_history = _gather_task_run_history(task_id)
    if task_history:
        ollama_prompt += f"\n\nTask Run History:\n{task_history}"

    # Inject runtime context from previous task (Batcomputer)
    runtime_text = _format_runtime_context(_PREV_RUNTIME_CTX, config)
    if runtime_text:
        ollama_prompt += f"\n\n{runtime_text}"

    print(f"[TB] Generating enriched prompt via {tb_model}...")

    response_text, duration_ms = _ollama_generate(
        ollama_prompt, tb_model, timeout=600, num_predict=-1)

    # Phase 0.5 sov-consult: skip audit-trail + interaction-log writes for
    # sovereign tasks. TB still generates the enriched prompt — the answer
    # gets returned — but no .brain/driver/* trace is left.
    if _should_write_corpus(task):
        log_ollama_call("TB", tb_model, ollama_prompt, response_text or "",
                        0 if response_text else -1, duration_ms, "", task_id)

        _log_tb_interaction(task_id, "C", ollama_prompt, response_text or "",
                            duration_ms=duration_ms)

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


def _spawn_lever_fix_task(parent_task: Dict, lever_matches: List[Dict],
                          tasks_path: Optional[Path] = None) -> Optional[str]:
    """Spawn a fix task for lever findings. Day-0 compounding — no LLM.

    Dedupes: if a pending lever-fix task with the same lever set + file set
    already exists, returns None and does not create a new one.

    Returns the new task id (or existing deduped id), or None on failure.
    """
    path = tasks_path if tasks_path is not None else TASKS_PATH
    try:
        lever_names = sorted({m.get("lever", "?") for m in lever_matches})
        affected_files: set = set()
        finding_samples: List[str] = []
        file_exts = (".py", ".js", ".ts", ".tsx", ".yaml", ".yml",
                     ".md", ".json", ".sh", ".toml")
        for m in lever_matches:
            findings = m.get("detail", {}).get("findings", [])
            if isinstance(findings, list):
                for f in findings[:3]:
                    finding_samples.append(f)
                    # Parse tokens and file:line:col forms; collect path-like bits.
                    for token in str(f).split():
                        token = token.rstrip(",.)")
                        for candidate in [token] + token.split(":"):
                            if "/" in candidate and candidate.endswith(file_exts):
                                affected_files.add(candidate)
                                break

        dedup_key = f"{','.join(lever_names)}|{','.join(sorted(affected_files))}"

        if path.exists():
            data = json.loads(path.read_text())
        else:
            data = {"tasks": []}
        tasks = data.get("tasks", [])

        for t in tasks:
            if (t.get("source") == "lever_gate"
                    and t.get("status") in ("pending", "in_progress")
                    and t.get("lever_gate_dedup_key") == dedup_key):
                return t.get("id")

        ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        new_id = f"lever-fix-{'-'.join(lever_names)}-{ts}"
        description_lines = [
            f"Lever gate spawned this task from {len(lever_matches)} finding(s).",
            f"Levers: {', '.join(lever_names)}",
            f"Parent task: {parent_task.get('id', '?')}",
            "",
            "Sample findings:",
        ] + [f"  - {f}" for f in finding_samples[:8]]
        scope = sorted(affected_files) if affected_files else parent_task.get("scope", ["**"])

        new_task = {
            "id": new_id,
            "title": f"Fix {','.join(lever_names)} findings in {parent_task.get('id', '?')}",
            "description": "\n".join(description_lines),
            "scope": scope,
            "priority": "high",
            "status": "pending",
            "assigned_to": "tb",
            "created_at": datetime.now().isoformat(),
            "source": "lever_gate",
            "lever_gate_dedup_key": dedup_key,
            "lever_gate_parent_task_id": parent_task.get("id", ""),
        }
        tasks.append(new_task)
        data["tasks"] = tasks
        data["schema_version"] = data.get("schema_version", 1)
        data["updated_at"] = datetime.now().isoformat()
        path.write_text(json.dumps(data, indent=2))
        return new_id
    except Exception as e:
        print(f"[LEVER_GATE] task spawn failed (non-fatal): {e}")
        return None


def _spar_phase_cd(task: Dict, executor_result: Dict, review: Dict, config: Dict):
    """Score TB's Phase C prompt and Phase D review — produce DPO pairs from real work.

    This runs inline during branch mode. Every task TB works on
    becomes training data regardless of outcome.
    """
    if not _should_write_corpus(task):
        return  # Phase 0.5 sov-consult: sovereign tasks emit no DPO/SFT.
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

        # ── Phase D: Review quality — outcome-correlated scoring ──
        # Score TB's verdict by what actually happened (final verdict after deepen
        # chain + GROUND verification), not by a second Claude opinion.
        review_score = None
        if config.get("training_capture_review_dpo", True) and review.get("verdict"):
            tb_verdict = review["verdict"]
            final_verdict = executor_result.get("final_verdict", tb_verdict)
            verification_passed = (executor_result.get("verification") or {}).get("verified")

            # Rubric:
            #   ESCALATE                                 → 5 (right by definition)
            #   DEEPEN → final ESCALATE/DEEPEN_EXHAUSTED  → 5 (Claude couldn't satisfy)
            #   DEEPEN → final ACCEPT after retry        → 5 (push produced better output)
            #   DEEPEN → (ambiguous)                      → 3
            #   ACCEPT & verification_passed is True     → 4
            #   ACCEPT & verification_passed is False    → 1 (rubber-stamped broken fix)
            #   ACCEPT & verification_passed is None     → 3
            verdict_correct = None
            if tb_verdict == "ESCALATE":
                review_score = 5
                verdict_correct = True
            elif tb_verdict == "DEEPEN":
                if final_verdict in ("ESCALATE", "DEEPEN_EXHAUSTED", "ACCEPT"):
                    review_score = 5
                    verdict_correct = True
                else:
                    review_score = 3
            elif tb_verdict == "ACCEPT":
                if verification_passed is False:
                    review_score = 1
                    verdict_correct = False
                elif verification_passed is True:
                    review_score = 4
                    verdict_correct = True
                else:
                    review_score = 3
            else:
                review_score = 3

            tb_review_text = (f"VERDICT: {review.get('verdict', '?')}\n"
                              f"REASON: {review.get('reason', '')}\n"
                              f"NOTES: {review.get('deepen_notes', '')}")
            review_sys = ("You are Third Brother, reviewing work done by Claude Code. "
                          "Respond with VERDICT, REASON, and NOTES.")
            review_user = (f"Task: {task_desc[:300]}\n"
                           f"Executor result: {str(executor_result.get('result', ''))[:300]}\n"
                           f"Git diff: {git_diff[:300]}")

            # High-signal DPO: only when TB was actually wrong (score <= 2).
            if review_score <= 2:
                review_dpo = {
                    "prompt": [
                        {"role": "system", "content": review_sys},
                        {"role": "user", "content": review_user},
                    ],
                    "chosen": [{"role": "assistant",
                                "content": "VERDICT: DEEPEN\nREASON: verification failed; "
                                           "prior ACCEPT was premature.\nNOTES: re-examine "
                                           "the diff against the task's verification criteria."}],
                    "rejected": [{"role": "assistant", "content": tb_review_text}],
                    "metadata": {
                        "source": "tb_review_outcome",
                        "task_id": task.get("id", ""),
                        "review_score": review_score,
                        "verdict_correct": verdict_correct,
                        "tb_verdict": tb_verdict,
                        "final_verdict": final_verdict,
                        "verification_passed": verification_passed,
                        "category": "review_quality",
                        "ts": datetime.now().isoformat(),
                    },
                }
                with open(SPARRING_DPO_PATH, "a") as f:
                    f.write(json.dumps(review_dpo) + "\n")

            # SFT entry for positive cases (score >= 4).
            if review_score >= 4:
                review_sft = {
                    "messages": [
                        {"role": "system", "content": review_sys},
                        {"role": "user", "content": review_user},
                        {"role": "assistant", "content": tb_review_text[:1500]},
                    ],
                    "metadata": {
                        "source": "tb_review_outcome",
                        "task_id": task.get("id", ""),
                        "original_score": review_score,
                        "category": "review_quality",
                        "quality": "gold",
                        "tb_verdict": tb_verdict,
                        "final_verdict": final_verdict,
                        "verification_passed": verification_passed,
                        "ts": datetime.now().isoformat(),
                    },
                }
                with open(SPARRING_SFT_PATH, "a") as f:
                    f.write(json.dumps(review_sft) + "\n")

            print(f"[SPARRING] Phase D scored {review_score}/5 "
                  f"(outcome-correlated, tb={tb_verdict}, final={final_verdict}, "
                  f"verify={verification_passed})")

        return {"phase_c_score": score, "phase_d_score": review_score}

    except Exception as e:
        print(f"[SPARRING] Error (non-fatal): {e}")
        return None


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
    if not _should_write_corpus(task):
        return  # Phase 0.5 sov-consult.
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
    if not _should_write_corpus(task):
        return  # Phase 0.5 sov-consult.
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
    if not _should_write_corpus(task):
        return  # Phase 0.5 sov-consult.
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


def _log_hard_negative(task: Dict, failure_mode: str, notes: str,
                       attributed_to: str = "executor"):
    """Log failed tasks as hard negatives in the sparring task bank.

    attributed_to: "tb_review" (deepen exhausted), "ground" (verification failed),
    "executor" (scope violation, crash, etc.). Lets TB see which of its own outputs
    produced the hard negative.
    """
    if not _should_write_corpus(task):
        return  # Phase 0.5 sov-consult.
    try:
        entry = {
            "task": f"{task.get('description', '')}\n\nPrevious failure: {notes[:300]}",
            "has_file": bool(task.get("scope")),
            "source": "hard_negative",
            "original_task_id": task.get("id", ""),
            "failure_mode": failure_mode,
            "attributed_to": attributed_to,
            "added_at": datetime.now().isoformat(),
        }
        with open(SPARRING_TASK_BANK_PATH, "r") as f:
            bank = json.load(f)
        bank.append(entry)
        with open(SPARRING_TASK_BANK_PATH, "w") as f:
            json.dump(bank, f, indent=2)
        print(f"[TRAINING] Hard negative added to task bank: {failure_mode} "
              f"(source={attributed_to})")
    except Exception as e:
        print(f"[TRAINING] Hard negative log error (non-fatal): {e}")


# ═══════════════════════════════════════════════════════════════
# TB REVIEWER (v3 Phase D)
# ═══════════════════════════════════════════════════════════════

REVIEW_LOG_PATH = DRIVER_DIR / "review_log.jsonl"


def deepen_follow_up(task: Dict, review_notes: str, session_id: str,
                     config: Dict, pre_snapshot: set = None,
                     pre_head: str = "") -> tuple:
    """Inline follow-up on same session after DEEPEN verdict.

    Instead of re-queuing (losing context), immediately sends review feedback
    to the same Claude session and re-reviews the result.

    Args:
        pre_head: Git HEAD SHA from before the original task execution.
                  Used to detect committed changes (Claude often commits
                  during sessions, making unstaged/staged diffs empty).

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
        # Unstaged changes
        diff_result = subprocess.run(
            ["git", "diff", "--stat"], capture_output=True, text=True,
            timeout=10, cwd=str(PROJECT_ROOT))
        git_diff_text = diff_result.stdout[:3000]
        # Staged changes
        if not git_diff_text.strip():
            diff_result = subprocess.run(
                ["git", "diff", "--cached", "--stat"], capture_output=True, text=True,
                timeout=10, cwd=str(PROJECT_ROOT))
            git_diff_text = diff_result.stdout[:3000]
        # Changes committed during session (Claude Code often commits)
        if not git_diff_text.strip() and pre_head:
            diff_result = subprocess.run(
                ["git", "log", "--stat", "--format=", f"{pre_head}..HEAD"],
                capture_output=True, text=True, timeout=10, cwd=str(PROJECT_ROOT))
            git_diff_text = diff_result.stdout[:3000]
    except Exception:
        pass

    # Filter out pre-existing dirty files (same as main execution path)
    if pre_snapshot:
        git_diff_text = _filter_diff_by_snapshot(git_diff_text, pre_snapshot)

    # Re-review the follow-up result
    review = tb_review_output(task, response, git_diff_text, config,
                              plan_text=task.get("_plan_text", "")[:3000])
    return (response, review)


def tb_review_output(task: Dict, executor_result: Dict,
                     git_diff: str, config: Dict,
                     plan_text: str = "") -> Dict:
    """Call TB via Ollama to review executor output.

    Args:
        plan_text: If provided, TB checks diff alignment against the plan.

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
CITATION: [For ACCEPT only: quote 1-2 lines from the git diff above that directly implement the task. Prefix each line with > and copy verbatim. Leave empty for DEEPEN/ESCALATE.]
REASON: [one sentence]
NOTES: [if DEEPEN, what additional work is needed]

SHOW-YOUR-WORK RULE: ACCEPT requires a non-empty CITATION that appears verbatim in the diff above. If you cannot cite a specific diff line that implements the task, return DEEPEN instead. Do not invent citations.

Respond now:"""

    if plan_text:
        review_prompt += f"""

Original Plan (for alignment check):
{plan_text[-1500:]}

ADDITIONAL CHECK: Verify the diff implements what the plan describes.
If the diff diverges significantly from the plan, DEEPEN or ESCALATE."""

    task_id = task.get("id", "")

    # Inject task run history so TB knows past attempts
    task_history = _gather_task_run_history(task_id)
    if task_history:
        review_prompt += (f"\n\nTask Run History:\n{task_history}\n"
            "If this task has failed before for a specific reason, "
            "check whether THAT issue is now fixed before re-judging.")

    # Inject runtime context from previous task (Batcomputer)
    runtime_text = _format_runtime_context(_PREV_RUNTIME_CTX, config)
    if runtime_text:
        review_prompt += f"\n\n{runtime_text}"

    print(f"[REVIEW] Reviewing {task_id or '?'} via {tb_model}...")

    try:
        output, duration_ms = _ollama_generate(
            review_prompt, tb_model, timeout=600, num_predict=-1)

        # Phase 0.5 sov-consult: skip audit-trail write for sovereign tasks.
        if _should_write_corpus(task):
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

        # ── Show-your-work contract (idea #60): ACCEPT requires a diff citation ──
        citation = ""
        for line in output.split("\n"):
            if line.strip().upper().startswith("CITATION:"):
                citation = line.split(":", 1)[1].strip().lstrip(">").strip().strip('"\'')
                break

        syw_enabled = v3.get("show_your_work_enabled", True)
        syw_min_diff_chars = v3.get("show_your_work_min_diff_chars", 100)
        syw_min_citation_chars = v3.get("show_your_work_min_citation_chars", 15)
        original_verdict = verdict
        syw_downgrade = False
        if (syw_enabled and verdict == "ACCEPT"
                and len(git_diff or "") >= syw_min_diff_chars):
            if len(citation) < syw_min_citation_chars:
                verdict = "DEEPEN"
                deepen_notes = (
                    "Show-your-work contract: ACCEPT requires citing diff line(s) "
                    f"that implement the task. Got citation={citation!r}."
                )
                syw_downgrade = True
            elif citation not in (git_diff or ""):
                verdict = "DEEPEN"
                deepen_notes = (
                    f"Show-your-work contract: CITATION {citation[:80]!r} "
                    "not found verbatim in diff."
                )
                syw_downgrade = True

        # ── Lever gate (day-0 runtime compounding, no LLM required) ──
        # If the ledger flags findings on files in this diff, ACCEPT is a
        # rubber-stamp. Force DEEPEN at runtime and spawn a fix task so the
        # system builds its own backlog. Works without a local model.
        lever_gate_enabled = v3.get("lever_gate_enabled", True)
        lever_gate_matches: List[Dict] = []
        lever_gate_spawned_task_id: Optional[str] = None
        if lever_gate_enabled and verdict == "ACCEPT":
            lever_gate_matches = _find_lever_findings_in_diff(
                git_diff, window=v3.get("lever_gate_window", 100),
            )
            if lever_gate_matches:
                lever_names = sorted({m.get("lever", "?") for m in lever_gate_matches})
                verdict = "DEEPEN"
                if original_verdict == "ACCEPT" and not syw_downgrade:
                    # Only set original_verdict if we weren't already tracking
                    # a show-your-work downgrade from the same starting point.
                    pass
                deepen_notes = (
                    f"Lever gate: {len(lever_gate_matches)} finding(s) on diff files "
                    f"from {','.join(lever_names)}. Fix the findings or address them "
                    "explicitly before accepting."
                )
                if v3.get("lever_gate_spawn_task", True):
                    lever_gate_spawned_task_id = _spawn_lever_fix_task(
                        task, lever_gate_matches
                    )

        review_result = {
            "verdict": verdict,
            "reason": reason,
            "confidence": confidence,
        }
        if deepen_notes:
            review_result["deepen_notes"] = deepen_notes
        if syw_downgrade:
            review_result["syw_downgraded"] = True
            review_result["original_verdict"] = original_verdict
            review_result["citation_attempted"] = citation[:200]
        if lever_gate_matches:
            review_result["lever_gate_fired"] = True
            review_result["original_verdict"] = original_verdict
            review_result["lever_gate_count"] = len(lever_gate_matches)
            review_result["lever_gate_types"] = sorted({
                m.get("lever", "?") for m in lever_gate_matches
            })
            if lever_gate_spawned_task_id:
                review_result["lever_gate_spawned_task_id"] = lever_gate_spawned_task_id

        print(f"[REVIEW] {task.get('id', '?')}: {verdict} (confidence: {confidence}, "
              f"parse: {parse_method}) — {reason[:80]}")
        if lever_gate_matches:
            print(f"[REVIEW] Lever gate fired: {len(lever_gate_matches)} finding(s) "
                  f"from {','.join(review_result['lever_gate_types'])}. "
                  f"Spawned task: {lever_gate_spawned_task_id or 'none'}")

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
        if syw_downgrade:
            log_entry["syw_downgraded"] = True
            log_entry["original_verdict"] = original_verdict
        if lever_gate_matches:
            log_entry["lever_gate_fired"] = True
            log_entry["lever_gate_count"] = len(lever_gate_matches)
            log_entry["original_verdict"] = original_verdict
            if lever_gate_spawned_task_id:
                log_entry["lever_gate_spawned_task_id"] = lever_gate_spawned_task_id
        # Phase 0.5 sov-consult: skip review_log + interaction-log writes for
        # sovereign tasks. The verdict still flows back to run_driver via
        # `review_result` — operational decisions (commit / escalate / deepen)
        # work as normal; only the audit trail skips.
        if _should_write_corpus(task):
            with open(REVIEW_LOG_PATH, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

            _log_tb_interaction(task.get("id", ""), "D", review_prompt, output or "",
                                verdict=verdict, duration_ms=duration_ms)

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


TB_INTERACTIONS_LOG = DRIVER_DIR / "tb_interactions.jsonl"


def _log_tb_interaction(task_id: str, phase: str, prompt: str, response: str,
                        verdict: str = "", duration_ms: int = 0):
    """Always-on full TB prompt/response log — analysable post-run."""
    entry = {
        "ts": datetime.now().isoformat(),
        "task_id": task_id,
        "phase": phase,  # "C" (prompt writer) or "D" (reviewer)
        "prompt": prompt,
        "response": response,
        "verdict": verdict,
        "duration_ms": duration_ms,
        "prompt_words": len(prompt.split()),
        "response_words": len(response.split()),
        "batcomputer_enabled": bool(_PREV_RUNTIME_CTX),
    }
    try:
        TB_INTERACTIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(TB_INTERACTIONS_LOG, "a") as f:
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
    if not _should_write_corpus(task):
        return  # Phase 0.5 sov-consult: shadow_log skipped for sovereign tasks.
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


# ═══════════════════════════════════════════════════════════════
# TB ORCHESTRATION — Board Reading + Decision Making
# ═══════════════════════════════════════════════════════════════


def _tb_read_board() -> Dict:
    """Gather system state for TB orchestration decisions."""
    board = {}

    # CSR from flywheel
    try:
        from mcp_server_nucleus.flywheel import Flywheel
        csr_state = Flywheel(BRAIN_PATH).csr()
        board["csr_ratio"] = csr_state.get("ratio", 0)
        board["csr_total"] = csr_state.get("claims_total", 0)
        failures = [c for c in csr_state.get("recent_claims", []) if not c.get("survived")]
        modes = {}
        for f in failures:
            mode = f.get("step", "unknown").split(":")[0]
            modes[mode] = modes.get(mode, 0) + 1
        board["csr_failure_modes"] = modes
    except Exception:
        board["csr_ratio"] = None

    # Task states
    tasks = load_tasks()
    board["tasks_committed"] = [t["id"] for t in tasks if t.get("status") == "committed"]
    board["tasks_blocked"] = [
        {"id": t["id"], "reason": t.get("failure_reason", t.get("blocked_reason", ""))}
        for t in tasks if t.get("status") == "blocked"
    ]
    board["tasks_failed"] = [
        {"id": t["id"], "reason": t.get("failure_reason", "")}
        for t in tasks if t.get("status") == "failed"
    ]

    # Recent runs
    runs = load_runs()[-20:]
    board["recent_runs"] = [
        {"task_id": r.get("task_id"), "outcome": r.get("outcome"),
         "failure_reason": r.get("failure_reason", "")[:150]}
        for r in runs
    ]

    # Verification stats
    board["verification"] = load_verification_stats(50)

    # Hard negatives in sparring bank
    if SPARRING_TASK_BANK_PATH.exists():
        try:
            with open(SPARRING_TASK_BANK_PATH) as f:
                bank = json.load(f)
            hard_negs = [e for e in bank if e.get("source") == "hard_negative"]
            board["hard_negative_count"] = len(hard_negs)
            hn_modes = {}
            for e in hard_negs:
                m = e.get("failure_mode", "unknown")
                hn_modes[m] = hn_modes.get(m, 0) + 1
            board["hard_negative_modes"] = hn_modes
        except Exception:
            board["hard_negative_count"] = 0
    else:
        board["hard_negative_count"] = 0

    return board


def _format_board_for_tb(board: Dict) -> str:
    """Format board dict into a text block for TB's Ollama prompt."""
    lines = []

    # CSR
    csr = board.get("csr_ratio")
    if csr is not None:
        lines.append(f"CSR: {csr:.3f} ({board.get('csr_total', '?')} claims)")
        modes = board.get("csr_failure_modes", {})
        if modes:
            top = sorted(modes.items(), key=lambda x: -x[1])[:5]
            lines.append("CSR failure modes: " + ", ".join(f"{m} ({c}x)" for m, c in top))
    else:
        lines.append("CSR: unavailable")

    # Tasks
    committed = board.get("tasks_committed", [])
    blocked = board.get("tasks_blocked", [])
    failed = board.get("tasks_failed", [])
    lines.append(f"\nTasks: {len(committed)} committed, {len(blocked)} blocked, {len(failed)} failed")
    for t in blocked[:5]:
        lines.append(f"  BLOCKED {t['id']}: {t.get('reason', '?')[:100]}")
    for t in failed[:5]:
        lines.append(f"  FAILED {t['id']}: {t.get('reason', '?')[:100]}")

    # Verification
    v = board.get("verification", {})
    if v.get("total", 0) > 0:
        lines.append(f"\nVerification: {v['accuracy']:.0%} ({v['verified_true']}/{v['total']})")

    # Hard negatives
    hn = board.get("hard_negative_count", 0)
    if hn > 0:
        lines.append(f"\nHard negatives: {hn}")
        hn_modes = board.get("hard_negative_modes", {})
        if hn_modes:
            top = sorted(hn_modes.items(), key=lambda x: -x[1])[:5]
            lines.append("Failure modes: " + ", ".join(f"{m} ({c}x)" for m, c in top))

    # Recent runs
    runs = board.get("recent_runs", [])
    if runs:
        outcomes = {}
        for r in runs:
            o = r.get("outcome", "unknown")
            outcomes[o] = outcomes.get(o, 0) + 1
        lines.append(f"\nLast {len(runs)} runs: " +
                     ", ".join(f"{o}={c}" for o, c in outcomes.items()))

    return "\n".join(lines)


def _gather_task_run_history(task_id: str) -> str:
    """Build per-task run history for Phase C/D injection."""
    if not task_id:
        return ""
    sections = []
    runs = load_runs()
    task_runs = [r for r in runs if r.get("task_id") == task_id]
    if task_runs:
        sections.append(f"TASK HISTORY ({task_id}):")
        for i, r in enumerate(task_runs[-5:], 1):
            ts = r.get("ts", "?")[:10]
            outcome = r.get("outcome", "?")
            reason = r.get("failure_reason", "")[:100]
            sections.append(f"  Run {i} ({ts}): {outcome}" +
                            (f" — {reason}" if reason else ""))

    # Check hard negatives for this task
    if SPARRING_TASK_BANK_PATH.exists():
        try:
            with open(SPARRING_TASK_BANK_PATH) as f:
                bank = json.load(f)
            hn = [e for e in bank if e.get("source") == "hard_negative"
                  and e.get("task_id") == task_id]
            if hn:
                modes = [e.get("failure_mode", "?") for e in hn]
                sections.append(f"  Hard negatives: {', '.join(modes)}")
        except Exception:
            pass

    return "\n".join(sections)


def _format_runtime_context(prev_ctx: dict, config: Optional[Dict] = None) -> str:
    """Format previous task's runtime context for TB's Phase C/D prompts (Batcomputer).

    If config has v3_features.batcomputer_enabled=False, returns "" (A/B off).
    """
    if config and not config.get("v3_features", {}).get("batcomputer_enabled", True):
        return ""
    if not prev_ctx:
        return ""
    lines = ["RUNTIME CONTEXT (previous task):"]

    scores = prev_ctx.get("tb_scores", {})
    if scores:
        c = scores.get("phase_c_score", "?")
        d = scores.get("phase_d_score", "?")
        lines.append(f"  Your scores: Phase C={c}/5, Phase D={d}/5")

    trust = prev_ctx.get("trust_change")
    if trust:
        lines.append(f"  Trust: {trust}")
    elif prev_ctx.get("trust_phase"):
        lines.append(f"  Trust: P{prev_ctx['trust_phase']}")

    turns = prev_ctx.get("session_turns", 0)
    pressure = prev_ctx.get("session_pressure_pct", 0)
    if turns:
        lines.append(f"  Session: {turns} turns, {pressure}% pressure")

    v = prev_ctx.get("verification", {})
    if v and v.get("tiers_failed"):
        lines.append(f"  Verification FAILED: tiers {v['tiers_failed']}")
        for sig in v.get("signals", []):
            if not sig.get("passed"):
                lines.append(f"    {sig.get('check', '?')} FAIL {sig.get('file', '')}")

    cls = prev_ctx.get("classification", {})
    if cls:
        lines.append(f"  Prev task: type={cls.get('type', '?')}, scout={cls.get('needs_scout', False)}")

    dcas = prev_ctx.get("dcas_replayed", [])
    if dcas:
        lines.append(f"  DCAs replayed: {len(dcas)}")
        for d in dcas[:3]:
            decision = d.get("decision", "") if isinstance(d, dict) else str(d)
            lines.append(f"    - {decision[:80]}")

    captures = prev_ctx.get("training_captures", {})
    if captures and any(captures.values()):
        active = [f"{k}={v}" for k, v in captures.items() if v]
        lines.append(f"  Training captured (prev task): {', '.join(active)}")

    return "\n".join(lines) if len(lines) > 1 else ""


def tb_orchestrate(board: Dict, config: Dict) -> Dict:
    """Call TB via Ollama to make an orchestration decision.

    Returns {"action": "compound|retry_stuck|skip",
             "targets": [...], "reason": str, "confidence": float}
    """
    v3 = config.get("v3_features", {})
    tb_model = os.environ.get("TB_MODEL") or v3.get("tb_model", "third-brother:latest")

    board_text = _format_board_for_tb(board)

    prompt = f"""You are Third Brother, the principal. Read the board and decide what to do.

BOARD STATE:
{board_text}

Pick ONE action:

compound — Run compound mode to train on hard negatives and improve the system.
retry_stuck — Reset blocked/failed tasks for re-attempt. You must list which task IDs.
skip — Nothing to do right now.

Decision rules:
- Many hard negatives (>10) means compound is needed.
- Blocked tasks whose failure reason matches a fixed issue should be retried.
- If CSR is stable and nothing is stuck, skip.

Write your answer as three lines:
ACTION: compound
TARGETS: all
REASON: 272 hard negatives need to be addressed via compound training."""

    print("[ORCHESTRATE] TB reading the board...")
    output, duration_ms = _ollama_generate(prompt, tb_model, timeout=600, num_predict=-1)

    # Phase 0.5 sov-consult: orchestration decisions are TB-content too.
    # When orchestrating sovereign work, the prompt + response can leak.
    # Gate by config-level sovereignty (orchestrate doesn't see a task dict).
    if _should_write_corpus(config.get("sovereignty")):
        log_ollama_call("ORCHESTRATE", tb_model, prompt, output or "",
                        0 if output else -1, duration_ms)

    if not output:
        print(f"[ORCHESTRATE] Ollama failed after {duration_ms}ms")
        # Deterministic fallback: decide based on board state
        return _tb_fallback_decision(board)

    # Parse response
    action = None
    targets = []
    reason = output[:200]

    for line in output.split("\n"):
        stripped = line.strip()
        upper = stripped.upper()
        if upper.startswith("ACTION:"):
            token = stripped.split(":", 1)[1].strip().split()[0].lower()
            # Strip punctuation from token
            token = token.rstrip(".,;:")
            if token in ("compound", "retry_stuck", "skip"):
                action = token
        elif upper.startswith("TARGETS:"):
            raw = stripped.split(":", 1)[1].strip()
            if raw.lower() not in ("all", "-", "none", "n/a"):
                targets = [t.strip() for t in raw.split(",")
                           if t.strip() and not t.strip().startswith("[")]
        elif upper.startswith("REASON:"):
            reason = stripped.split(":", 1)[1].strip()

    # If TB couldn't decide, fall back to deterministic logic
    if not action:
        print("[ORCHESTRATE] TB response unparseable, falling back to board heuristics")
        return _tb_fallback_decision(board)

    result = {"action": action, "targets": targets, "reason": reason,
              "confidence": 0.8}
    print(f"[ORCHESTRATE] Decision: {action} (targets={targets[:5]}, "
          f"confidence=0.8)")
    print(f"[ORCHESTRATE] Reason: {reason[:200]}")
    return result


def _tb_fallback_decision(board: Dict) -> Dict:
    """Deterministic fallback when TB can't decide. Uses board heuristics."""
    hard_negs = board.get("hard_negative_count", 0)
    blocked = board.get("tasks_blocked", [])
    failed = board.get("tasks_failed", [])

    if hard_negs >= 10:
        reason = f"{hard_negs} hard negatives — compound needed"
        print(f"[ORCHESTRATE] Fallback: compound ({reason})")
        return {"action": "compound", "targets": [], "reason": reason,
                "confidence": 0.6}

    if blocked or failed:
        ids = [t["id"] for t in blocked + failed]
        reason = f"{len(ids)} stuck task(s) — retrying"
        print(f"[ORCHESTRATE] Fallback: retry_stuck ({reason})")
        return {"action": "retry_stuck", "targets": ids, "reason": reason,
                "confidence": 0.6}

    print("[ORCHESTRATE] Fallback: skip (nothing actionable)")
    return {"action": "skip", "targets": [], "reason": "board is clean",
            "confidence": 0.6}


def _reset_stuck_tasks(task_ids: List[str]):
    """Reset blocked/failed tasks to committed for re-attempt."""
    tasks = load_tasks()
    reset_count = 0
    for t in tasks:
        if t["id"] in task_ids and t.get("status") in ("blocked", "failed"):
            old_status = t["status"]
            t["status"] = "committed"
            print(f"[ORCHESTRATE] Reset {t['id']}: was {old_status}")
            reset_count += 1
    if reset_count > 0:
        save_tasks(tasks)
    return reset_count


def _auto_unstick_after_compound(board_pre: Dict, board_post: Dict) -> int:
    """After compound mode, reset stuck tasks whose failure modes were addressed.

    Deterministic check — compares hard negative mode counts before/after.
    If a failure mode count decreased, tasks stuck on that mode get re-committed.
    """
    pre_modes = board_pre.get("hard_negative_modes", {})
    post_modes = board_post.get("hard_negative_modes", {})

    # Find modes that decreased (compound addressed them)
    addressed_modes = set()
    for mode, pre_count in pre_modes.items():
        post_count = post_modes.get(mode, 0)
        if post_count < pre_count:
            addressed_modes.add(mode)

    if not addressed_modes:
        return 0

    print(f"[ORCHESTRATE] Addressed failure modes: {', '.join(addressed_modes)}")

    # Find stuck tasks whose failure reason matches addressed modes
    stuck_ids = []
    for t in board_post.get("tasks_blocked", []) + board_post.get("tasks_failed", []):
        reason = t.get("reason", "").lower()
        if any(mode.lower() in reason for mode in addressed_modes):
            stuck_ids.append(t["id"])

    if stuck_ids:
        _reset_stuck_tasks(stuck_ids)
    return len(stuck_ids)


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

    # Non-actionable outcomes (infrastructure issues, NOT task failures).
    # MUST be excluded from acceptance_ratio numerator AND denominator — counting
    # skipped tasks as failures kept trust ladder pinned at Phase 1.
    _NON_ACTIONABLE = {"session_exhausted", "timeout", "session_busy", "completed_no_pr"}

    # ── DEMOTION checks (always evaluated first) ──

    critical_alerts = [a for a in alerts if a.get("severity") == "CRITICAL"]
    if critical_alerts and current_phase > 1:
        return current_phase, 1, f"CRITICAL trigger: {critical_alerts[-1].get('rule', '?')}"

    consec_fail_limit = thresholds.get("demotion_consecutive_failures", 3)
    actionable_runs = [r for r in runs if r.get("outcome") not in _NON_ACTIONABLE]
    if len(actionable_runs) >= consec_fail_limit:
        recent = actionable_runs[-consec_fail_limit:]
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

    if current_phase == 1:
        cfg = thresholds.get("phase_1_to_2", {})
        min_runs = cfg.get("min_runs", 20)
        unedited_ratio = cfg.get("unedited_ratio", 0.75)
        if len(runs) >= min_runs:
            recent = runs[-min_runs:]
            # acceptance_ratio fix: drop skipped tasks from BOTH sides of the ratio.
            actionable = [r for r in recent if r.get("outcome") not in _NON_ACTIONABLE]
            if actionable:
                completed = sum(1 for r in actionable if r.get("outcome") == "completed")
                denom = len(actionable)
                ratio = completed / denom
                if ratio >= unedited_ratio:
                    return current_phase, 2, f"Phase 1->2: {completed}/{denom} ({ratio:.0%} >= {unedited_ratio:.0%})"

    elif current_phase == 2:
        cfg = thresholds.get("phase_2_to_3", {})
        min_runs = cfg.get("min_runs", 30)
        acceptance_ratio = cfg.get("acceptance_ratio", 0.70)
        if len(runs) >= min_runs:
            recent = runs[-min_runs:]
            # acceptance_ratio fix: drop skipped tasks from BOTH sides of the ratio.
            actionable = [r for r in recent if r.get("outcome") not in _NON_ACTIONABLE]
            if actionable:
                accepted = sum(1 for r in actionable if r.get("outcome") == "completed")
                denom = len(actionable)
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


def _clear_critical_alerts():
    """Remove CRITICAL alerts from alerts.jsonl after demotion consumes them."""
    if not ALERTS_PATH.exists():
        return
    lines = ALERTS_PATH.read_text().strip().split('\n')
    kept = []
    for line in lines:
        try:
            entry = json.loads(line)
            if entry.get("severity") != "CRITICAL":
                kept.append(line)
        except json.JSONDecodeError:
            kept.append(line)
    ALERTS_PATH.write_text('\n'.join(kept) + '\n' if kept else '')
    print(f"[TRUST] Cleared {len(lines) - len(kept)} consumed CRITICAL alerts")


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

        # Consume CRITICAL alerts after demotion — they triggered the response
        if "CRITICAL trigger" in reason:
            _clear_critical_alerts()

    return new_phase


# ═══════════════════════════════════════════════════════════════
# COMPOUND AUDIT — Scorecard + Degradation Guard
# ═══════════════════════════════════════════════════════════════


def _snapshot_scorecard() -> Dict:
    """Capture running scores for degradation detection."""
    # CSR via Flywheel class
    try:
        from mcp_server_nucleus.flywheel import Flywheel
        csr_data = Flywheel(BRAIN_PATH).csr()
    except Exception:
        csr_data = {"ratio": 0, "claims_total": 0}

    # Verification accuracy from verification_log.jsonl
    vstats = load_verification_stats(50)

    # Trust phase from config
    config = load_config()
    trust_phase = config.get("trust_ladder", {}).get("current_phase", 1)

    # Task success rate from shadow log (last 20 entries)
    task_total, task_success = 0, 0
    if SHADOW_LOG_PATH.exists():
        for line in SHADOW_LOG_PATH.read_text().strip().split('\n')[-20:]:
            if line.strip():
                try:
                    e = json.loads(line)
                    if e.get("outcome"):
                        task_total += 1
                        if e["outcome"] in ("completed", "success", "partial"):
                            task_success += 1
                except (json.JSONDecodeError, KeyError):
                    pass

    # Audit results
    audit_path = BRAIN_PATH / "audit" / "results.json"
    audit_results = {}
    if audit_path.exists():
        try:
            audit_results = json.loads(audit_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    audit_accepts = sum(1 for r in audit_results.values() if r.get("verdict") == "ACCEPT")
    audit_total = len(audit_results)

    return {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "csr": csr_data.get("ratio", 0),
        "csr_total": csr_data.get("claims_total", 0),
        "trust_phase": trust_phase,
        "verify_accuracy": vstats.get("accuracy", 0),
        "verify_total": vstats.get("total", 0),
        "task_success_rate": (task_success / task_total) if task_total else 0,
        "task_total": task_total,
        "audit_accept_rate": (audit_accepts / audit_total) if audit_total else 0,
        "audit_total": audit_total,
    }


def _save_scorecard(label: str, scorecard: Dict):
    """Persist scorecard snapshot to .brain/compound/scorecards.jsonl."""
    compound_dir = BRAIN_PATH / "compound"
    compound_dir.mkdir(parents=True, exist_ok=True)
    path = compound_dir / "scorecards.jsonl"
    entry = {"label": label, **scorecard}
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[COMPOUND-AUDIT] Scorecard '{label}': CSR={scorecard['csr']:.3f}, "
          f"trust=P{scorecard['trust_phase']}, "
          f"verify={scorecard['verify_accuracy']:.0%}, "
          f"audit={scorecard['audit_accept_rate']:.0%} ({scorecard['audit_total']})")


def _check_degradation(pre: Dict, post: Dict) -> List[str]:
    """Compare pre/post scorecards. Return list of degraded metric descriptions."""
    degraded = []
    if post["csr"] < pre["csr"] - 0.05 and pre["csr_total"] > 10:
        degraded.append(f"CSR: {pre['csr']:.3f} -> {post['csr']:.3f}")
    if post["trust_phase"] < pre["trust_phase"]:
        degraded.append(f"trust: P{pre['trust_phase']} -> P{post['trust_phase']}")
    if post["verify_accuracy"] < pre["verify_accuracy"] - 0.10 and pre["verify_total"] > 5:
        degraded.append(f"verify: {pre['verify_accuracy']:.0%} -> {post['verify_accuracy']:.0%}")
    return degraded


def _analyze_compound_signals() -> List[Dict]:
    """Mine CSR failures, verification failures, hard negatives, and audit gaps for compound tasks."""
    tasks = []

    # Signal 1: Recurring CSR failure modes
    failure_modes = {}
    try:
        from mcp_server_nucleus.flywheel import Flywheel
        csr_data = Flywheel(BRAIN_PATH).csr()
        for claim in csr_data.get("recent_claims", []):
            if not claim.get("survived") and claim.get("reason"):
                mode = claim["reason"].split(":")[0].strip()
                failure_modes[mode] = failure_modes.get(mode, 0) + 1
    except Exception:
        pass

    repeated = {m: c for m, c in failure_modes.items() if c >= 2}
    if repeated:
        top = sorted(repeated.items(), key=lambda x: -x[1])[:3]
        modes_str = ", ".join(f"{m} ({c}x)" for m, c in top)
        tasks.append({
            "id": f"compound-csr-{top[0][0][:20]}",
            "title": f"Fix recurring CSR failure: {top[0][0]}",
            "description": f"Recurring failure modes in CSR: {modes_str}. "
                           f"Investigate root cause and fix the underlying issue.",
            "scope": ["scripts/**", "mcp-server-nucleus/**"],
            "priority": 1, "status": "committed", "source": "compound_audit",
            "max_turns": 25,
        })

    # Signal 2: Verification failures (tiers that keep failing)
    tier_failures = {}
    if VERIFICATION_LOG_PATH.exists():
        for line in VERIFICATION_LOG_PATH.read_text().strip().split('\n')[-50:]:
            if line.strip():
                try:
                    e = json.loads(line)
                    for tier in e.get("tiers_failed", []):
                        tier_failures[tier] = tier_failures.get(tier, 0) + 1
                except (json.JSONDecodeError, KeyError):
                    pass

    repeated_tiers = {t: c for t, c in tier_failures.items() if c >= 3}
    if repeated_tiers:
        top_tier = max(repeated_tiers, key=repeated_tiers.get)
        tasks.append({
            "id": f"compound-verify-tier{top_tier}",
            "title": f"Fix verification gap: tier {top_tier} ({repeated_tiers[top_tier]}x failures)",
            "description": f"Verification tier {top_tier} has failed {repeated_tiers[top_tier]} times "
                           f"in the last 50 verifications. Investigate and fix.",
            "scope": ["scripts/**", "mcp-server-nucleus/**"],
            "priority": 1, "status": "committed", "source": "compound_audit",
            "max_turns": 25,
        })

    # Signal 3: Hard negatives in sparring bank
    hard_neg_count = 0
    if SPARRING_TASK_BANK_PATH.exists():
        try:
            with open(SPARRING_TASK_BANK_PATH) as f:
                bank = json.load(f)
            hard_neg_count = sum(1 for t in bank if t.get("source") == "hard_negative")
        except (json.JSONDecodeError, OSError):
            pass

    if hard_neg_count >= 3:
        tasks.append({
            "id": "compound-hard-negatives",
            "title": f"Address {hard_neg_count} accumulated hard negatives",
            "description": f"{hard_neg_count} hard negatives in sparring bank — "
                           f"these represent systematic weaknesses. Review patterns and fix root causes.",
            "scope": ["scripts/**", "mcp-server-nucleus/**"],
            "priority": 2, "status": "committed", "source": "compound_audit",
            "max_turns": 25,
        })

    # Signal 4: Audit results — plans that failed verification
    audit_path = BRAIN_PATH / "audit" / "results.json"
    if audit_path.exists():
        try:
            audit_results = json.loads(audit_path.read_text())
            incomplete = {k: v for k, v in audit_results.items() if v.get("verdict") != "ACCEPT"}
            if incomplete:
                names = ", ".join(list(incomplete.keys())[:3])
                tasks.append({
                    "id": "compound-audit-gaps",
                    "title": f"Close {len(incomplete)} audit gap(s)",
                    "description": f"Plans that failed audit verification: {names}. "
                                   f"The system cannot do what was planned. "
                                   f"Investigate: missing implementation, design flaw, or superseded plan?",
                    "scope": ["scripts/**", "mcp-server-nucleus/**", "backend/**", ".brain/**"],
                    "priority": 1, "status": "committed", "source": "compound_audit",
                    "max_turns": 25,
                })
        except (json.JSONDecodeError, OSError):
            pass

    return tasks


def _print_compound_audit_summary(pre: Dict, post: Dict, compounded: List, rolled_back: List):
    print("\n" + "=" * 60)
    print("  COMPOUND AUDIT COMPLETE")
    print(f"  CSR:       {pre['csr']:.3f} -> {post['csr']:.3f}")
    print(f"  Trust:     P{pre['trust_phase']} -> P{post['trust_phase']}")
    print(f"  Verify:    {pre['verify_accuracy']:.0%} -> {post['verify_accuracy']:.0%}")
    print(f"  Tasks:     {pre['task_success_rate']:.0%} -> {post['task_success_rate']:.0%}")
    print(f"  Audit:     {pre['audit_accept_rate']:.0%} -> {post['audit_accept_rate']:.0%} "
          f"({post['audit_total']} plans)")
    print(f"  Compounded: {len(compounded)} | Rolled back: {len(rolled_back)}")
    if rolled_back:
        print(f"  Rollbacks: {', '.join(rolled_back)}")
    print("=" * 60)


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
        from mcp_server_nucleus.runtime.heartbeat_ops import _heartbeat_check_impl
        result = _heartbeat_check_impl(str(BRAIN_PATH))
        triggers = result.get("triggers", [])
        if triggers:
            names = [t.get("type", "?") for t in triggers]
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
        from mcp_server_nucleus.runtime.event_stream import emit_event, EventSeverity
        emit_event(
            brain_path=BRAIN_PATH,
            event_type=event_type,
            emitter="third-brother-driver-v2",
            payload=payload or {"task_id": task["id"], "task_title": task["title"]},
            severity=EventSeverity.ROUTINE,
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
        archive_result = _archive_resolved_files()
        gc_result = _garbage_collect_tasks(max_age_hours=72)
        archived = archive_result.get("files_moved", 0)
        gc_count = gc_result.get("archived", 0)
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
            signal_absorbed=list(task.get("scope", ["**"])),
            signal_produced=[f"task:{task['id']}:{outcome}"],
            context=f"session-resume, {task.get('scope', ['**'])}",
            confidence=0.8 if outcome == "completed" else 0.3,
            conversation=[{"role": "assistant", "content": response.get("result", "")[:2000]}],
        )
        print(f"[RING 8] Archive: turn recorded")
    except Exception as e:
        print(f"[RING 8] Archive: skip ({e.__class__.__name__})")


def ring_selfheal_on_failure(task: Dict, error: str) -> str:
    """RING 9: Capture 4D context on failure for self-healing."""
    try:
        from mcp_server_nucleus.selfhealer import (
            _get_intent_context,
            _get_recent_history,
        )
        intent = _get_intent_context(BRAIN_PATH)
        changes = _get_recent_history()
        diagnosis = f"Task {task['id']} failed: {error[:200]}\nIntent: {str(intent)[:300]}\nRecent changes: {str(changes)[:300]}"
        print(f"[RING 9] Self-heal: 4D context captured ({len(diagnosis)} chars)")
        return diagnosis
    except Exception as e:
        print(f"[RING 9] Self-heal: skip ({e.__class__.__name__})")
    return ""


def ring_engram_lookup(task: Dict) -> str:
    """RING 3+: Query engrams for task-relevant memory."""
    try:
        from mcp_server_nucleus.runtime.engram_ops import _brain_query_engrams_impl
        raw = _brain_query_engrams_impl(
            context=task.get("title", ""),
            min_intensity=1,
            limit=5,
        )
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        data = parsed.get("data", {}) if isinstance(parsed, dict) else {}
        engrams = data.get("engrams", [])
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


def ring_distill_replay(task: Dict) -> Tuple[str, List[Dict]]:
    """RING 3+: Inject high-confidence DCAs from previous distillation.

    Returns (injected_text, replayed_atoms_for_runtime_ctx).
    """
    try:
        from mcp_server_nucleus.replay import ReplayEngine
        engine = ReplayEngine(BRAIN_PATH)
        atoms = engine.load_atoms()
        if atoms:
            filtered = engine.filter_atoms(atoms, min_confidence=0.8, max_atoms=3)
            if filtered:
                print(f"[RING 3+] Replay: {len(filtered)} DCAs injected")
                lines = []
                for a in filtered:
                    decision = (a.get("decision", "") if isinstance(a, dict) else str(a))[:200]
                    lines.append(f"- {decision}")
                return ("\n## Prior Decisions (high confidence)\n" + "\n".join(lines) + "\n",
                        filtered)
    except Exception as e:
        print(f"[RING 3+] Replay: skip ({e.__class__.__name__})")
    return "", []


EXPERIMENTS_PATH = BRAIN_PATH / "experiments" / "experiments.json"


def _append_experiment_result(task: Dict, review: Dict, verification: Dict, config: Dict):
    """Record task outcome in the active experiment journal.

    Tracks verification pass rate (CSR) and scope escalation rate
    to measure whether the experiment's hypothesis holds.
    """
    exp_id = config.get("active_experiment", "")
    if not exp_id or not EXPERIMENTS_PATH.exists():
        return
    try:
        data = json.loads(EXPERIMENTS_PATH.read_text())
        exp = next((e for e in data.get("experiments", []) if e["id"] == exp_id), None)
        if not exp or exp.get("status") != "active":
            return

        exp["runs_in_experiment"] = exp.get("runs_in_experiment", 0) + 1
        verified = verification.get("verified", True) if verification else True
        escalated = review.get("verdict") == "ESCALATE"

        # Track running CSR: verified_pass / total
        total = exp["runs_in_experiment"]
        # Use a simple running count stored in the experiment
        prev_pass = exp.get("_verified_pass", 0)
        if verified and not escalated:
            prev_pass += 1
        exp["_verified_pass"] = prev_pass
        exp["csr_delta"] = round(prev_pass / total - exp.get("baseline_csr", 0), 4)

        data["last_updated"] = datetime.now().isoformat()
        EXPERIMENTS_PATH.write_text(json.dumps(data, indent=2))
    except Exception as e:
        print(f"[EXPERIMENT] Update failed (non-fatal): {e}")


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
        rag_scope = "code"  # driver only does code work; "life" scope for future personal assistant
        context, rag_results = build_full_context(
            task["description"], brain_path=BRAIN_PATH, scope=rag_scope
        )
        print(f"[DRIVER] Context: {len(context.split())} words, {len(rag_results)} chunks")
    except Exception as e:
        print(f"[DRIVER] Context error: {e}. Continuing without RAG.")

    engrams = ring_engram_lookup(task)
    dcas, dcas_replayed = ring_distill_replay(task)
    global _LAST_DCAS_REPLAYED
    _LAST_DCAS_REPLAYED = dcas_replayed

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

    # Audit tasks: the task description IS the prompt — don't let TB rewrite it
    if task.get("source") == "plan_audit":
        tb_prompt = None
    else:
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
    global _PREV_RUNTIME_CTX

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
        # Phase 0.5 sov-consult: stamp sovereignty on every task before
        # execution. Per-task sovereignty (from task bank) wins; otherwise
        # fall to driver-level default (--sovereignty CLI / env / "guarded").
        task.setdefault(
            "sovereignty",
            config.get("sovereignty") or _DRIVER_DEFAULT_SOVEREIGNTY,
        )
        print(f"\n[DRIVER] ═══════════════════════════════════════════")
        print(f"[DRIVER] Task: {task['title']} ({task_id})")
        print(f"[DRIVER] Priority: {task.get('priority', '?')} | Scope: {', '.join(task.get('scope', ['**']))} | Sovereignty: {task['sovereignty']}")

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

            # ── Batcomputer: start accumulating runtime context ──
            _runtime_ctx = {
                "classification": response.get("classification", {}),
                "session_turns": response.get("context_metrics", {}).get("turns", 0),
                "session_pressure_pct": response.get("context_metrics", {}).get("pressure_pct", 0),
                "dcas_replayed": [
                    {"decision": (a.get("decision", "") if isinstance(a, dict) else str(a))[:100]}
                    for a in _LAST_DCAS_REPLAYED
                ],
            }

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
                    # Log every verification run (audit trail).
                    # Phase 0.5 sov-consult: skip when task is sovereign.
                    if _should_write_corpus(task):
                        _vlog = {"task_id": task.get("id", ""), **_v,
                                 "ts": datetime.now().isoformat()}
                        with open(VERIFICATION_LOG_PATH, "a") as _vf:
                            _vf.write(json.dumps(_vlog, default=str) + "\n")
                    if not _v["verified"]:
                        _log_hard_negative(task, "verification_failed",
                            f"Tiers failed: {_v['tiers_failed']}, "
                            f"signals: {json.dumps(_v['signals'][:5], default=str)}",
                            attributed_to="ground")
                        # Calibration DPO (Frontier 3: COMPOUND signal).
                        # _log_hard_negative already gates on sovereignty;
                        # the calibration DPO needs its own check.
                        if (config.get("calibration_dpo_enabled", True)
                                and _should_write_corpus(task)):
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

            # Batcomputer: capture verification breakdown
            if verification_result:
                _runtime_ctx["verification"] = {
                    "tiers_passed": verification_result.get("tiers_passed", []),
                    "tiers_failed": verification_result.get("tiers_failed", []),
                    "signals": [{"tier": s.get("tier"), "check": s.get("check"),
                                 "passed": s.get("passed"), "file": s.get("file", "")}
                                for s in verification_result.get("signals", [])[:5]],
                }

            # ── Programmatic scope check (hard gate — no LLM judgment) ──
            # Filter out files that were already dirty before task execution
            git_diff_text = _filter_diff_by_snapshot(git_diff_text, pre_snapshot)
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
                if not task_id.startswith("sparring-"):
                    log_alert("scope_violation", task_id, "escalated",
                              f"Files outside scope: {violation_list}", "WARNING")
            else:
                # ── Auto-fire post-executor levers before review ──
                # Day-0 runtime compounding: levers observe the fresh diff
                # and write findings to the ledger so tb_review_output's
                # lever gate can see them. Failure of a lever must never
                # block the driver.
                if config.get("v3_features", {}).get("lever_auto_fire_enabled", True):
                    try:
                        from scripts.levers.run_lever import run_trigger as _lever_run_trigger
                        _lever_run_trigger("post_executor")
                    except Exception as _e:
                        print(f"[LEVER] auto-fire failed (non-fatal): {_e}")

                try:
                    audit_plan_text = ""
                    if task.get("source") == "plan_audit" and task.get("_plan_text"):
                        audit_plan_text = task["_plan_text"][:3000]
                    review = tb_review_output(task, response, git_diff_text, config,
                                              plan_text=audit_plan_text)
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
                        task, deepen_notes, session_id, config, pre_snapshot,
                        pre_head=_pre_head)
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
                    update_task_status(task_id, "blocked")
                    task["blocked_reason"] = f"deepen_exhausted: {deepen_notes[:200]}"
                    print(f"[REVIEW] DEEPEN: exhausted {max_chain} inline retries, blocked")
                    _log_hard_negative(task, "deepen_exhausted", deepen_notes,
                                       attributed_to="tb_review")
                    _fw_file_ticket("task_outcome", task_id,
                                    f"deepen_exhausted: {deepen_notes[:200]}", config)
                elif review["verdict"] == "ESCALATE":
                    _review_action = "escalate"
                    if not task_id.startswith("sparring-"):
                        log_alert("tb_review_escalate", task_id, "escalated",
                                  review.get("reason", ""), "WARNING")
                    update_task_status(task_id, "blocked")
                    print(f"[REVIEW] ESCALATE after deepen: {task_id} blocked")
                    _log_hard_negative(task, "escalated_after_deepen", review.get("reason", ""),
                                       attributed_to="tb_review")
                    _fw_file_ticket("task_outcome", task_id,
                                    f"escalate_after_deepen: {review.get('reason', '')[:200]}", config)
            elif review["verdict"] == "ESCALATE":
                _review_action = "escalate"
                if not task_id.startswith("sparring-"):
                    log_alert("tb_review_escalate", task_id, "escalated",
                              review.get("reason", ""), "WARNING")
                update_task_status(task_id, "blocked")
                print(f"[REVIEW] ESCALATE: {task_id} blocked for human review")
                _log_hard_negative(task, "escalated", review.get("reason", ""),
                                   attributed_to="tb_review")
                _fw_file_ticket("task_outcome", task_id,
                                f"escalate: {review.get('reason', '')[:200]}", config)

            # Thread final_verdict so Phase D outcome scorer can see terminal state
            response["final_verdict"] = (
                "DEEPEN_EXHAUSTED"
                if review["verdict"] == "DEEPEN" and _review_action == "deepen"
                else review["verdict"]
            )

            # ── Sparring: score Phase C+D output for training data ──
            if config.get("training_capture_enabled", True):
                response["git_diff"] = git_diff_text  # pass diff to eval
                _spar_result = _spar_phase_cd(task, response, review, config)
                if _spar_result:
                    _runtime_ctx["tb_scores"] = _spar_result

            # Batcomputer: capture training attribution (which source produced hard negs)
            _runtime_ctx["training_captures"] = {
                "tb_review": 1 if _review_action in ("deepen", "escalate") else 0,
                "ground": 1 if verification_result and not verification_result.get("verified") else 0,
                "executor": 1 if scope_violations else 0,
            }

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
            if not task_id.startswith("sparring-"):
                log_alert("session_crash", task_id, "failed", failure_reason, "ERROR")
            _fw_file_ticket("task_outcome", task_id, failure_reason, config)
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

        # Every attempted task counts toward max_tasks limit
        tasks_completed += 1

        # Experiment journal: track every attempted task (including escalated/sparring)
        _append_experiment_result(
            task, response.get("tb_review", {}),
            response.get("verification"), config)

        # Handle review actions outside the lock
        if _review_action:
            # Batcomputer: still publish partial context for next task
            _PREV_RUNTIME_CTX = _runtime_ctx
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
            _fw_file_ticket("task_outcome", task_id, "timeout", config)
        elif result_text and "prompt is too long" in result_text.lower():
            # Session context exhausted — rotate to fresh session
            outcome = "session_exhausted"
            update_task_status(task_id, "committed")
            session_exhaustion_count += 1
            if not task_id.startswith("sparring-"):
                log_run(task, "session_exhausted", turns=turns, duration_seconds=duration,
                        failure_reason="prompt too long",
                        retry_count=response.get("retry_count", 0),
                        session_id=session_id)

            _fw_file_ticket("task_outcome", task_id, "session_exhausted", config)

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
        ctx_metrics = response.get("context_metrics")
        save_state(outcome, task, session_id=session_id, context_metrics=ctx_metrics)

        if outcome == "completed":
            write_session_state(session_id, branch,
                                [t for t in load_tasks() if t.get("status") == "completed"],
                                config)
            _fw_record_survived("task_outcome", task_id, config)

        # ── RING 10: Quick eval every 5th completed task ──
        completed_count = sum(1 for t in load_tasks() if t.get("status") == "completed")
        eval_score = None
        if outcome == "completed" and completed_count > 0 and completed_count % 5 == 0:
            eval_score = ring_eval_quick(task_id)
            if eval_score is not None:
                check_eval_regression(eval_score)

        if not task_id.startswith("sparring-"):
            log_run(task, outcome, turns=turns, duration_seconds=duration,
                    retry_count=response.get("retry_count", 0),
                    session_id=session_id, eval_score=eval_score)

        # ── GT40: Two-gate verdict for audit results ──
        if task.get("source") == "plan_audit" and task.get("_plan_path"):
            # Gate 1: Claude completed Steps 1+2
            claude_passed = (outcome == "completed")

            # Gate 2: Car's independent verification (GT40 onboard diagnostics)
            verify_text = task.get("_verify_text", "")
            car_result = None
            car_passed = True  # no verification section = skip gate 2
            quality = "none"
            if verify_text and claude_passed:
                print(f"[GT40] Running independent verification for "
                      f"{Path(task['_plan_path']).name}...")
                auto_cmds = _auto_verification_commands(task.get("_plan_text", ""))
                car_result = _run_verification_commands(
                    verify_text, extra_commands=auto_cmds)
                quality = _compute_verification_quality(car_result)
                _print_verification_report(car_result)
                print(f"[GT40] Verification quality: {quality}")
                car_passed = car_result["passed"]

            # Both gates must pass for ACCEPT
            if claude_passed and car_passed:
                verdict = "ACCEPT"
            elif claude_passed and not car_passed:
                # GT40 retry: feed failure details back to Claude for one fix attempt
                failed_cmds = [r for r in car_result["results"]
                               if r.get("passed") is False]
                failure_report = "\n".join(
                    f"  FAIL: `{r['command']}`\n"
                    f"    exit_code={r.get('exit_code')}\n"
                    f"    stderr: {r.get('stderr', '')[:200]}"
                    for r in failed_cmds)
                retry_prompt = (
                    f"GT40 independent verification found {len(failed_cmds)} "
                    f"failure(s):\n{failure_report}\n\n"
                    "Fix these failures so the verification commands pass. "
                    "When done, summarize what you fixed."
                )
                print(f"[GT40] Verification FAILED — retrying with failure feedback...")
                config = load_config()
                retry_response, _ = deepen_follow_up(
                    task, retry_prompt, session_id, config, None)

                # Re-run GT40 after fix attempt
                car_result_2 = _run_verification_commands(verify_text)
                _print_verification_report(car_result_2)
                if car_result_2["passed"]:
                    verdict = "ACCEPT"
                    car_result = car_result_2
                    print("[GT40] Retry succeeded — ACCEPT")
                else:
                    verdict = "VERIFY_FAILED"
                    car_result = car_result_2
                    print("[GT40] Retry failed — VERIFY_FAILED")
            else:
                verdict = "INCOMPLETE"

            _record_audit_result(
                plan_filename=Path(task["_plan_path"]).name,
                plan_mtime=os.path.getmtime(task["_plan_path"]),
                verdict=verdict,
                turns=turns,
                duration_s=duration,
                session_id=session_id,
                verification=car_result,
                verification_quality=quality,
                plan_source=task.get("plan_source", ""),
                plan_kind=task.get("plan_kind", ""),
            )

            _log_structured_outcome(
                task, verdict, review,
                verification_result=car_result,
                verification_quality=quality,
                duration_s=duration, turns=turns,
                executor_result=response,
            )

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

        if not task_id.startswith("sparring-"):
            _old_trust = config.get("trust_ladder", {}).get("current_phase", 1)
            _new_trust = apply_trust_ladder(config)
            _runtime_ctx["trust_phase"] = _new_trust
            if _old_trust != _new_trust:
                _runtime_ctx["trust_change"] = f"P{_old_trust}->P{_new_trust}"

        # Batcomputer: publish runtime context for next task's Phase C/D
        _PREV_RUNTIME_CTX = _runtime_ctx

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


def _record_audit_result(plan_filename, plan_mtime, verdict, turns, duration_s,
                         session_id, verification=None, verification_quality=None,
                         plan_source="", plan_kind=""):
    """Persist audit verdict so future runs auto-skip verified plans."""
    audit_dir = BRAIN_PATH / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    results_path = audit_dir / "results.json"

    results = {}
    if results_path.exists():
        try:
            results = json.loads(results_path.read_text())
        except (json.JSONDecodeError, OSError):
            results = {}

    entry = {
        "verdict": verdict,
        "audited_at": datetime.now().isoformat(timespec="seconds"),
        "plan_mtime": datetime.fromtimestamp(plan_mtime).isoformat(timespec="seconds"),
        "turns": turns,
        "duration_s": round(duration_s),
        "session_id": session_id[:16] if session_id else "",
    }
    if plan_source:
        entry["plan_source"] = plan_source
    if plan_kind:
        entry["plan_kind"] = plan_kind
    if verification:
        entry["verification"] = {
            "passed": verification["passed"],
            "passed_count": verification["passed_count"],
            "failed_count": verification["failed_count"],
            "skipped_count": verification["skipped_count"],
            "duration_s": verification["duration_s"],
        }
    if verification_quality:
        entry["verification_quality"] = verification_quality
    results[plan_filename] = entry
    tmp_path = results_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(results, indent=2) + "\n")
    os.replace(tmp_path, results_path)
    print(f"[AUDIT] Recorded: {plan_filename} → {verdict}")


STRUCTURED_OUTCOME_LOG = DRIVER_DIR / "structured_outcomes.jsonl"


def _extract_closeness(executor_result: Dict) -> Dict:
    """Parse DONE/MISSING/PARTIAL counts from structured audit executor output.

    Used as a quality signal — a plan that's 80% implemented is more valuable
    to retry than one that's 0% implemented.
    """
    text = str(executor_result.get("result", "")).upper()
    done = text.count("DONE")
    missing = text.count("MISSING")
    partial = text.count("PARTIAL")
    total = done + missing + partial
    return {
        "done": done, "missing": missing, "partial": partial,
        "ratio": round(done / total, 2) if total > 0 else 0,
        "total_checks": total,
    }


def _log_structured_outcome(task: Dict, verdict: str, review: Dict = None,
                            verification_result: Dict = None,
                            verification_quality: str = "none",
                            duration_s: int = 0, turns: int = 0,
                            executor_result: Dict = None):
    """Log structured audit outcome for process learning. Append-only JSONL."""
    if not _should_write_corpus(task):
        return  # Phase 0.5 sov-consult.
    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "task_id": task.get("id", ""),
        "plan": Path(task.get("_plan_path", "")).name if task.get("_plan_path") else "",
        "plan_source": task.get("plan_source", ""),
        "plan_kind": task.get("plan_kind", ""),
        "complexity_level": task.get("_complexity", {}).get("level", "unknown"),
        "template_used": ("structured" if task.get("_complexity", {}).get("level")
                          in ("medium", "complex") else "freeform"),
        "file_count": task.get("_complexity", {}).get("file_count", 0),
        "verdict": verdict,
        "tb_verdict": review.get("verdict", "") if review else "",
        "tb_confidence": review.get("confidence", 0) if review else 0,
        "verification_quality": verification_quality,
        "verification_passed": (verification_result["passed"]
                                if verification_result else None),
        "turns": turns,
        "duration_s": round(duration_s),
        "structure_version": "v2-phased",
    }
    if executor_result:
        entry["closeness"] = _extract_closeness(executor_result)
    STRUCTURED_OUTCOME_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(STRUCTURED_OUTCOME_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def cmd_audit_stats():
    """Print structured audit statistics from outcome log."""
    if not STRUCTURED_OUTCOME_LOG.exists():
        print("[AUDIT-STATS] No data yet. Run --audit-plans first.")
        return
    entries = []
    for line in STRUCTURED_OUTCOME_LOG.read_text().splitlines():
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if not entries:
        print("[AUDIT-STATS] No data yet.")
        return

    total = len(entries)
    accepts = sum(1 for e in entries if e.get("verdict") == "ACCEPT")
    print(f"\n{'=' * 50}")
    print(f"  AUDIT STATISTICS ({total} audits)")
    print(f"{'=' * 50}")
    print(f"  ACCEPT rate: {accepts}/{total} ({100*accepts/total:.0f}%)")

    # By complexity
    print(f"\n  By complexity:")
    for level in ("simple", "medium", "complex", "unknown"):
        subset = [e for e in entries if e.get("complexity_level") == level]
        if subset:
            acc = sum(1 for e in subset if e.get("verdict") == "ACCEPT")
            print(f"    {level:10s}: {acc}/{len(subset)} ACCEPT")

    # By verification quality
    print(f"\n  By verification quality:")
    for q in ("strong", "weak", "none"):
        subset = [e for e in entries if e.get("verification_quality") == q]
        if subset:
            acc = sum(1 for e in subset if e.get("verdict") == "ACCEPT")
            print(f"    {q:10s}: {acc}/{len(subset)} ACCEPT")

    # Averages
    durations = [e.get("duration_s", 0) for e in entries if e.get("duration_s")]
    turns_list = [e.get("turns", 0) for e in entries if e.get("turns")]
    if durations:
        print(f"\n  Avg duration: {sum(durations)/len(durations):.0f}s")
    if turns_list:
        print(f"  Avg turns: {sum(turns_list)/len(turns_list):.0f}")
    print(f"{'=' * 50}\n")


# ═══════════════════════════════════════════════════════════════
# GT40 — Script-level independent verification (the Car verifies)
# ═══════════════════════════════════════════════════════════════

_RECURSION_GUARDS = {"--audit-plans", "--compound-audit", "--sparring", "--compound", "--tb-loop"}

def _parse_verification_commands(verify_text: str) -> List[Dict]:
    """Extract runnable shell commands from plan verification markdown.

    Parses numbered lists, bullets, and inline backtick commands.
    Skips prose-only lines and recursive driver invocations.
    """
    commands = []
    for line in verify_text.split('\n'):
        line = line.strip().lstrip('0123456789.-) ')
        # Extract backtick-wrapped commands
        match = re.search(r'`([^`]+)`', line)
        if not match:
            continue
        cmd = match.group(1).strip()
        if not cmd or len(cmd) < 3:
            continue
        # Recursion guard — never invoke the driver from within its own verification
        if any(guard in cmd for guard in _RECURSION_GUARDS):
            commands.append({"command": cmd, "skipped": True,
                           "skip_reason": "recursion guard"})
            continue
        # Skip non-shell commands (prose in backticks like `ratio < 1.0`)
        if not any(cmd.startswith(p) for p in (
            "python", "cat", "grep", "ls", "cd", "npm", "node",
            "pytest", "bash", "sh", "./", "make", "curl", "git")):
            continue
        commands.append({"command": cmd, "skipped": False,
                         "kind": _classify_verification_cmd(cmd)})
    return commands


def _classify_verification_cmd(cmd: str) -> str:
    """Tag command as 'assertion' (can meaningfully fail) or 'observation' (always exits 0)."""
    if re.search(r'\bpytest\b|python3?\s+-m\s+pytest', cmd):
        return "assertion"
    if re.search(r'\bassert\b|\braise\b', cmd):
        return "assertion"
    if cmd.startswith(("grep ", "test ", "[ ")):
        return "assertion"
    if cmd.startswith(("cat ", "ls ", "echo ", "head ", "tail ", "wc ")):
        return "observation"
    return "assertion"  # conservative default


def _compute_verification_quality(result: Dict) -> str:
    """Rate: 'strong' (>=50% assertions), 'weak' (all observations), 'none' (no commands)."""
    executed = [r for r in result.get("results", []) if not r.get("skipped")]
    if not executed:
        return "none"
    assertions = [r for r in executed if r.get("kind") == "assertion"]
    return "strong" if len(assertions) >= len(executed) / 2 else "weak"


def _auto_verification_commands(plan_text: str) -> List[Dict]:
    """Derive deterministic checks from ## Files Modified / ## Affected Files. No LLM writes these."""
    cmds = []
    files_match = re.search(
        r"## (?:Files Modified|Affected Files)\s*\n((?:(?!^## ).*\n?)*)", plan_text, re.MULTILINE)
    if not files_match:
        return cmds
    for line in files_match.group(1).splitlines():
        # Handle bullet lists (- `path`) first
        path = re.sub(r"^[-*]\s*`?|`?\s*[—|].*$|`", "", line).strip()
        # Fall back to extracting backtick-wrapped path from table rows (| `path` | ... |)
        if not path or not re.match(r"[\w./\-]+\.\w+", path):
            tbl = re.search(r"`([\w./\-]+\.\w+)`", line)
            if tbl:
                path = tbl.group(1)
            else:
                continue
        if not re.match(r"[\w./\-]+\.\w+", path):
            continue
        cmds.append({"command": f"test -f {path}", "skipped": False,
                     "kind": "assertion", "auto_generated": True})
        if path.endswith(".py") and not path.startswith("tests/"):
            mod = path.replace("/", ".").replace(".py", "")
            cmds.append({"command": f'python3 -c "import {mod}"', "skipped": False,
                         "kind": "assertion", "auto_generated": True})
        if re.match(r"tests?/test_.*\.py$", path):
            cmds.append({"command": f"python3 -m pytest {path} -q --tb=no",
                         "skipped": False, "kind": "assertion", "auto_generated": True})
    return cmds


def _run_verification_commands(verify_text: str, cwd: Path = None,
                               timeout_per_cmd: int = 120,
                               timeout_total: int = 300,
                               extra_commands: List[Dict] = None) -> Dict:
    """Run plan verification commands independently via subprocess.

    The CAR verifies, not the DRIVER. Exit code 0 = PASS, nonzero = FAIL.
    Returns structured results for verdict gating and audit persistence.
    """
    commands = _parse_verification_commands(verify_text)
    if extra_commands:
        commands.extend(extra_commands)
    if not commands:
        return {"passed": True, "results": [], "total": 0,
                "passed_count": 0, "failed_count": 0, "skipped_count": 0,
                "duration_s": 0, "note": "no parseable commands in verification section"}

    results = []
    start = time.time()
    for cmd_info in commands:
        if cmd_info.get("skipped"):
            results.append({**cmd_info, "exit_code": None, "stdout": "", "stderr": "",
                          "passed": None, "duration_s": 0})
            continue
        # Total timeout guard
        elapsed = time.time() - start
        if elapsed > timeout_total:
            results.append({**cmd_info, "exit_code": None, "stdout": "",
                          "stderr": "total timeout exceeded", "passed": None,
                          "skipped": True, "skip_reason": "total timeout", "duration_s": 0})
            continue
        cmd_start = time.time()
        try:
            result = subprocess.run(
                cmd_info["command"], shell=True, capture_output=True, text=True,
                timeout=timeout_per_cmd, cwd=str(cwd or PROJECT_ROOT))
            results.append({
                "command": cmd_info["command"],
                "exit_code": result.returncode,
                "stdout": result.stdout[-500:] if result.stdout else "",
                "stderr": result.stderr[-500:] if result.stderr else "",
                "passed": result.returncode == 0,
                "skipped": False,
                "duration_s": round(time.time() - cmd_start, 1),
            })
        except subprocess.TimeoutExpired:
            results.append({
                "command": cmd_info["command"],
                "exit_code": None, "stdout": "", "stderr": "command timed out",
                "passed": False, "skipped": False,
                "skip_reason": f"timeout ({timeout_per_cmd}s)",
                "duration_s": timeout_per_cmd,
            })

    passed_results = [r for r in results if r.get("passed") is True]
    failed_results = [r for r in results if r.get("passed") is False]
    skipped_results = [r for r in results if r.get("passed") is None]

    return {
        "passed": len(failed_results) == 0,
        "results": results,
        "total": len(results),
        "passed_count": len(passed_results),
        "failed_count": len(failed_results),
        "skipped_count": len(skipped_results),
        "duration_s": round(time.time() - start, 1),
    }


def _print_verification_report(result: Dict):
    """Print GT40 independent verification results."""
    print(f"\n{'=' * 50}")
    print(f"  GT40 INDEPENDENT VERIFICATION")
    print(f"{'=' * 50}")
    for r in result["results"]:
        if r.get("skipped") or r.get("passed") is None:
            status = f"SKIP ({r.get('skip_reason', '')})"
        elif r.get("passed"):
            status = "PASS"
        else:
            status = f"FAIL (exit {r.get('exit_code')})"
        print(f"  [{status:20s}] {r['command'][:60]}")
        if r.get("stderr") and r.get("passed") is False:
            print(f"                       stderr: {r['stderr'][:100]}")
    print(f"\n  Result: {'ALL PASSED' if result['passed'] else 'FAILURES DETECTED'}")
    print(f"  {result['passed_count']} passed, {result['failed_count']} failed, "
          f"{result['skipped_count']} skipped ({result['duration_s']}s)")
    print(f"{'=' * 50}\n")


PLAN_SOURCES = [
    (Path.home() / ".claude" / "plans", "claude", "*.md"),
    (Path.home() / ".windsurf" / "plans", "windsurf", "*.md"),
    (BRAIN_PATH / "plans", "brain", "*.md"),
    (Path.home() / ".gemini" / "antigravity" / "brain", "antigravity",
     "*/implementation_plan_*.md"),
]


def _classify_plan_file(plan_path: Path, plan_text: str) -> Dict:
    """Classify a plan file as plan/status_report/megaplan/implementation_plan.

    Returns {"kind": str, "actionable": bool}.
    """
    name = plan_path.name.lower()
    text_lower = plan_text.lower()

    if any(k in name for k in ("status", "closeout", "close_out", "complete")):
        return {"kind": "status_report", "actionable": False}
    if text_lower.count("successfully") + text_lower.count("completed") > 5:
        return {"kind": "status_report", "actionable": False}

    line_count = plan_text.count("\n")
    if "megaplan" in name or line_count > 500:
        return {"kind": "megaplan", "actionable": True}

    if name.startswith("implementation_plan_") or name.startswith("design_thinking_"):
        return {"kind": "implementation_plan", "actionable": True}

    return {"kind": "plan", "actionable": True}


def _find_github_issues(label: str = "nucleus-bug", limit: int = 5) -> List[Dict]:
    """Scan GitHub for open issues (optional task source). Requires `gh` CLI.

    Returns empty list if gh is unavailable. P7 skeleton — not wired into
    orchestrator yet.
    """
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--label", label, "--limit", str(limit),
             "--state", "open", "--json", "number,title,body,url"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        pass
    return []


def _triage_priority(plan_path: Path, prev_results: Dict) -> int:
    """Return triage priority for a plan. Lower = higher priority.

    0 = un-audited (never tried)
    1 = DEEPEN_EXHAUSTED (retry failed audit)
    2 = ACCEPT but plan file changed since audit (re-verify)
    3 = ABANDONED or stable ACCEPT (skip unless --audit-force)
    """
    result = prev_results.get(plan_path.name)
    if not result:
        return 0
    verdict = result.get("verdict")
    if verdict == "DEEPEN_EXHAUSTED":
        return 1
    if verdict == "ACCEPT":
        try:
            plan_mtime = plan_path.stat().st_mtime
            audit_mtime_str = result.get("plan_mtime", "2020-01-01")
            audit_mtime = datetime.fromisoformat(audit_mtime_str).timestamp()
            if plan_mtime > audit_mtime:
                return 2
        except (ValueError, OSError):
            pass
    return 3


def run_plan_audit_mode(max_plans: int, session_id: str, branch: str, skip: int = 0, force: bool = False):
    """Accountability loop: walk plans newest-to-oldest, verify + implement each.

    For each plan:
      1. Read the plan file
      2. Verify each change against the codebase
      3. Implement anything missing
      4. Run tests / live-fire verification
      5. Move to next (older) plan — less work each time

    Usage: python3 scripts/third_brother_driver.py --audit-plans 3
    """
    # P1: Scan all 4 IDE ecosystems for plans (Claude + Windsurf + brain + Antigravity)
    seen_names = set()
    all_plan_files = []  # list of (plan_path, source_tag) tuples
    source_counts = {}
    for pdir, source_tag, pattern in PLAN_SOURCES:
        if not pdir.exists():
            continue
        count = 0
        for p in pdir.glob(pattern):
            if p.name not in seen_names:
                seen_names.add(p.name)
                all_plan_files.append((p, source_tag))
                count += 1
        if count > 0:
            source_counts[source_tag] = count
    if not all_plan_files:
        print("[AUDIT] No plan files found in any plan directory.")
        return

    print(f"[AUDIT] Plan sources: {', '.join(f'{k} ({v})' for k, v in source_counts.items())}")

    # P2: Classify — filter out status reports and other non-actionable files
    actionable = []
    non_actionable_count = 0
    for p, source in all_plan_files:
        try:
            plan_text = p.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        kind = _classify_plan_file(p, plan_text)
        if not kind["actionable"]:
            non_actionable_count += 1
            continue
        actionable.append((p, source, kind["kind"], plan_text))
    if non_actionable_count > 0:
        print(f"[AUDIT] Skipping {non_actionable_count} non-actionable files (status reports, etc.)")

    if not actionable:
        print("[AUDIT] No actionable plans after classification.")
        return

    # Sort newest first across all sources
    actionable.sort(key=lambda x: x[0].stat().st_mtime, reverse=True)

    # Load previous audit results
    audit_results_path = BRAIN_PATH / "audit" / "results.json"
    prev_results = {}
    if audit_results_path.exists():
        try:
            prev_results = json.loads(audit_results_path.read_text())
        except (json.JSONDecodeError, OSError):
            prev_results = {}

    # P4: Triage — un-audited first, then failed, then stale ACCEPT
    if not force:
        triaged = [(p, s, k, t, _triage_priority(p, prev_results))
                   for p, s, k, t in actionable]
        # Sort by (priority asc, mtime desc)
        triaged.sort(key=lambda x: (x[4], -x[0].stat().st_mtime))
        # Exclude priority 3 (nothing to do)
        unverified = [(p, s, k, t) for p, s, k, t, pri in triaged if pri < 3]
        skipped_count = sum(1 for _, _, _, _, pri in triaged if pri >= 3)
        if skipped_count > 0:
            print(f"[AUDIT] Auto-skipped {skipped_count} verified/abandoned plans")
    else:
        unverified = actionable
        print("[AUDIT] Force mode: re-auditing all plans")

    plans_to_audit = unverified[skip:skip + max_plans]
    print(f"[AUDIT] Found {len(actionable)} actionable plans, auditing {len(plans_to_audit)} "
          f"(un-audited first)")
    for i, (p, source, kind, _) in enumerate(plans_to_audit):
        print(f"  {i}: [{source}:{kind}] {p.name}")

    # Read each plan and create audit tasks
    existing_tasks = load_tasks()
    audit_ids = []

    for i, (plan_path, plan_source, plan_kind, plan_text) in enumerate(plans_to_audit):
        task_id = f"audit-{i:03d}"
        audit_ids.append(task_id)

        # Extract title from first markdown heading
        title_match = re.search(r"^#\s+(?:Plan:\s*)?(.+)$", plan_text, re.MULTILINE)
        plan_title = title_match.group(1).strip() if title_match else plan_path.stem

        # Extract "Files Modified" section for scope
        scope = ["scripts/**", "mcp-server-nucleus/**", "backend/**", ".brain/**"]
        files_match = re.search(r"## Files Modified\s*\n((?:- .+\n?)+)", plan_text)
        if files_match:
            file_lines = files_match.group(1).strip().splitlines()
            scope = []
            for line in file_lines:
                path = re.sub(r"^-\s*`?|`?\s*—.*$", "", line).strip()
                if path:
                    scope.append(path)

        # Extract "Verification" section for live-fire step
        verify_match = re.search(
            r"## Verification[^\n]*\n((?:(?!^## ).*\n?)*)", plan_text, re.MULTILINE)
        verify_steps = verify_match.group(1).strip() if verify_match else ""

        # GT40 pre-flight: check if verification already passes (informational)
        # NOTE: Pre-flight passing does NOT auto-ACCEPT — verification passing
        # doesn't mean the plan's code changes exist. Claude still does Step 1
        # (reality check). Pre-flight just tells us what to expect post-audit.
        if verify_steps:
            preflight = _run_verification_commands(verify_steps)
            runnable = [r for r in preflight["results"]
                        if r.get("passed") is not None and not r.get("skipped")]
            if runnable and preflight["passed"]:
                print(f"[GT40-PREFLIGHT] {plan_path.name}: ALL PASS (Claude still audits)")
            elif runnable:
                failed = [r for r in preflight["results"] if r.get("passed") is False]
                print(f"[GT40-PREFLIGHT] {plan_path.name}: {len(failed)} FAIL "
                      f"— Claude will attempt fixes")

        # Classify complexity → route to freeform or structured template
        complexity = _classify_plan_complexity(plan_text, scope)
        print(f"[AUDIT] {plan_path.name}: complexity={complexity['level']} "
              f"(files={complexity['file_count']}, changes={complexity['change_count']})")

        if complexity["level"] == "simple":
            # Keep freeform Steps 1-3 for simple plans
            description = f"""## Plan Audit: {plan_title}
Source: {plan_path.name}

### Your job

You are running the **accountability loop**. This plan was written but may not
have been fully implemented. Walk through it systematically:

**Step 1 — Verify against reality:**
For EACH change listed in the plan, check if it exists in the codebase.
Use Grep/Read to confirm functions, files, and wiring are present.
Report a table: Change | Status (DONE / MISSING / PARTIAL).

**Step 2 — Implement what's missing:**
For any MISSING or PARTIAL changes, implement them exactly as specified
in the plan. Follow the plan's code snippets and line references.

**Step 3 — Document changes:**
Summarize what you found (Step 1) and what you implemented (Step 2).
List any changes you skipped and why. The driver will independently
run the plan's verification commands after you complete (GT40 verification).

### The Plan

{plan_text}

### Constraints
- Do NOT commit changes (the driver handles commits)
- Do NOT modify files outside the plan's scope
- If a planned change conflicts with current code, skip it and note why
- If ALL steps in Step 1 are DONE, report "All changes verified"
"""
        else:
            expansion = ("Group changes by file. Write a sub-plan for each "
                         "file group." if complexity["level"] == "complex" else "")
            description = STRUCTURED_AUDIT_TEMPLATE.format(
                title=plan_title,
                plan_filename=plan_path.name,
                plan_text=plan_text,
                complexity_expansion=expansion,
            )

        task = {
            "id": task_id,
            "title": f"Audit: {plan_title[:60]}",
            "description": description,
            "scope": scope,
            "priority": 1,
            "status": "committed",
            "source": "plan_audit",
            "plan_source": plan_source,
            "plan_kind": plan_kind,
            "max_turns": complexity["recommended_turns"],
            "_complexity": complexity,
            "_plan_path": str(plan_path),
            "_verify_text": verify_steps,
            "_plan_text": plan_text,
        }
        existing_tasks.append(task)

    save_tasks(existing_tasks)
    print(f"[AUDIT] Injected {len(audit_ids)} audit tasks into queue")

    # Clear stale session state — audit must start fresh, not resume old context
    if STATE_PATH.exists():
        prev = json.loads(STATE_PATH.read_text())
        prev["session_id"] = ""
        STATE_PATH.write_text(json.dumps(prev))
        print("[AUDIT] Cleared stale session state — starting fresh")

    # P3: Loop 1 guardrails — scorecard + git tag + degradation rollback
    try:
        pre_scorecard = _snapshot_scorecard()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        git("tag", f"audit-pre-{ts}")
        print(f"[AUDIT] Checkpoint: audit-pre-{ts}")
    except Exception as e:
        print(f"[AUDIT] Checkpoint setup failed (non-fatal): {e}")
        pre_scorecard = None
        ts = ""

    try:
        run_driver("", mode="autonomous", branch=branch, max_tasks=len(audit_ids))

        # Post-run degradation check
        if pre_scorecard:
            try:
                post_scorecard = _snapshot_scorecard()
                degraded = _check_degradation(pre_scorecard, post_scorecard)
                if degraded:
                    print(f"[AUDIT] DEGRADATION: {', '.join(degraded)}")
                    print(f"[AUDIT] Rolling back to audit-pre-{ts}")
                    git("checkout", f"audit-pre-{ts}", "--", ".")
                else:
                    print("[AUDIT] Scorecard: no degradation")
            except Exception as e:
                print(f"[AUDIT] Post-check failed (non-fatal): {e}")
    finally:
        # Clean up audit tasks from tasks.json
        tasks = load_tasks()
        tasks = [t for t in tasks if t.get("id") not in audit_ids]
        save_tasks(tasks)
        print(f"[AUDIT] Cleaned up {len(audit_ids)} audit tasks from tasks.json")


def run_compound_audit_mode(max_tasks: int, branch: str):
    """Automated compound step: measure -> identify gaps -> close gaps -> verify.

    Safety: git tag before each step, scorecard before/after, rollback on degradation.
    Usage: python3 scripts/third_brother_driver.py --compound-audit 3
    """
    print("=" * 60)
    print("  COMPOUND AUDIT — Measure + Compound + Verify")
    print("=" * 60)

    # Phase 1: Pre-scorecard + checkpoint
    pre_scorecard = _snapshot_scorecard()
    _save_scorecard("compound-pre", pre_scorecard)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    git("tag", f"compound-pre-{ts}")
    print(f"[COMPOUND-AUDIT] Checkpoint: compound-pre-{ts}")

    # Phase 2: Analyze existing signals for compound opportunities
    print("\n[COMPOUND-AUDIT] Analyzing signals (CSR, verification, hard negatives, audit)...")
    compound_tasks = _analyze_compound_signals()

    if not compound_tasks:
        print("[COMPOUND-AUDIT] No compound opportunities — loop is clean")
        post_scorecard = _snapshot_scorecard()
        _save_scorecard("compound-post-noop", post_scorecard)
        _print_compound_audit_summary(pre_scorecard, post_scorecard, [], [])
        return

    # Cap at max_tasks
    compound_tasks = compound_tasks[:max_tasks]
    print(f"[COMPOUND-AUDIT] Found {len(compound_tasks)} compound tasks")

    # Phase 3: Execute with per-step checkpointing
    compounded = []
    rolled_back = []

    for task in compound_tasks:
        print(f"\n[COMPOUND-AUDIT] Executing: {task['title']}")
        step_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        git("tag", f"compound-step-{step_ts}")
        step_pre = _snapshot_scorecard()

        # Inject task and run
        existing = load_tasks()
        existing.append(task)
        save_tasks(existing)

        try:
            run_driver("", mode="autonomous", branch=branch, max_tasks=1)
        finally:
            tasks = load_tasks()
            tasks = [t for t in tasks if t.get("id") != task["id"]]
            save_tasks(tasks)

        step_post = _snapshot_scorecard()
        degraded = _check_degradation(step_pre, step_post)

        if degraded:
            print(f"[COMPOUND-AUDIT] DEGRADATION: {', '.join(degraded)}")
            print(f"[COMPOUND-AUDIT] Rolling back to compound-step-{step_ts}")
            git("checkout", f"compound-step-{step_ts}", "--", ".")
            _log_hard_negative(task, "compound_degradation",
                               f"Rolled back: {', '.join(degraded)}")
            _fw_file_ticket("compound_audit", task["id"],
                            f"compound_degradation: {', '.join(degraded)}", load_config())
            rolled_back.append(task["id"])
        else:
            compounded.append(task["id"])
            print(f"[COMPOUND-AUDIT] {task['id']}: OK")

    # Final scorecard
    final_scorecard = _snapshot_scorecard()
    _save_scorecard(f"compound-post-{ts}", final_scorecard)
    _print_compound_audit_summary(pre_scorecard, final_scorecard, compounded, rolled_back)


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


def run_tb_loop(max_iterations: int, branch: str):
    """TB-orchestrated loop: read board → decide → execute → repeat.

    TB sees the full system state and decides what to do next:
    compound (train on failures), retry_stuck (re-attempt failed tasks),
    or skip (nothing actionable).

    Usage: python3 scripts/third_brother_driver.py --tb-loop 3
    """
    config = load_config()
    branch_name = ensure_tb_branch(branch)

    # Warmup TB model
    v3 = config.get("v3_features", {})
    tb_model = os.environ.get("TB_MODEL") or v3.get("tb_model", "third-brother:latest")
    _ollama_warmup(tb_model)

    print("=" * 60)
    print("  TB ORCHESTRATION LOOP")
    print(f"  Max iterations: {max_iterations}")
    print(f"  Branch: {branch_name}")
    print("=" * 60)

    iterations_run = 0
    for i in range(max_iterations):
        iterations_run = i + 1
        print(f"\n[TB-LOOP] Iteration {i+1}/{max_iterations}")

        # 1. Read the board
        board = _tb_read_board()
        print(f"[TB-LOOP] Board: CSR={board.get('csr_ratio', '?')}, "
              f"blocked={len(board.get('tasks_blocked', []))}, "
              f"failed={len(board.get('tasks_failed', []))}, "
              f"hard_negs={board.get('hard_negative_count', 0)}")

        # 2. TB decides
        decision = tb_orchestrate(board, config)

        if decision["action"] == "skip":
            print("[TB-LOOP] TB says nothing actionable — stopping")
            break

        # 3. Execute
        board_pre = board
        if decision["action"] == "compound":
            run_compound_mode(branch_name)
            board_post = _tb_read_board()
            unstuck = _auto_unstick_after_compound(board_pre, board_post)
            if unstuck > 0:
                print(f"[TB-LOOP] Auto-unstuck {unstuck} task(s)")

        elif decision["action"] == "retry_stuck":
            targets = decision.get("targets", [])
            if targets:
                reset = _reset_stuck_tasks(targets)
                if reset > 0:
                    run_driver("", mode="autonomous", branch=branch_name,
                               max_tasks=len(targets))
            else:
                print("[TB-LOOP] retry_stuck with no targets — skipping")

        # 4. Post-iteration check
        board_post = _tb_read_board()
        print(f"[TB-LOOP] Post: CSR={board_post.get('csr_ratio', '?')}, "
              f"blocked={len(board_post.get('tasks_blocked', []))}")

    print(f"\n[TB-LOOP] Complete after {iterations_run} iteration(s)")


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
    parser.add_argument("--sovereignty",
                        choices=["public", "guarded", "sovereign"],
                        default=None,
                        help="Phase 0.5 sov-consult: corpus-write gate for all "
                             "tasks this run. sovereign = NO writes (no "
                             "shadow_log/DPO/SFT/verdict/audit). guarded = "
                             "writes proceed (default if unset). public = "
                             "writes proceed. Override per-task via task "
                             "bank's `sovereignty` field. Env: "
                             "TB_DRIVER_SOVEREIGNTY (same values).")
    parser.add_argument("--sparring", nargs="?", const=10, type=int,
                        help="Run N sparring rounds from task bank (default: 10)")
    parser.add_argument("--compound", nargs="?", const=5, type=int,
                        help="Exponential loop: real tasks → sparring (N rounds, default 5) → export training")
    parser.add_argument("--audit-plans", nargs="?", const=3, type=int,
                        help="Accountability loop: verify N plans newest-to-oldest (default: 3)")
    parser.add_argument("--audit-skip", type=int, default=0,
                        help="Skip N newest plans before auditing (use with --audit-plans)")
    parser.add_argument("--audit-force", action="store_true",
                        help="Re-audit all plans even if previously verified")
    parser.add_argument("--audit-abandon", nargs="+",
                        help="Mark plan file(s) as ABANDONED (auto-skipped in future audits)")
    parser.add_argument("--audit-stats", action="store_true",
                        help="Show structured audit statistics")
    parser.add_argument("--compound-audit", nargs="?", const=3, type=int,
                        help="Compound audit: measure -> close gaps -> verify (default: 3 tasks)")
    parser.add_argument("--tb-loop", nargs="?", const=3, type=int,
                        help="TB-orchestrated loop: read board → decide → execute → repeat (default: 3 iterations)")
    parser.add_argument("--verbose", action="store_true",
                        help="Log every Ollama call's input and output to stdout")
    args = parser.parse_args()

    global VERBOSE, _DRIVER_DEFAULT_SOVEREIGNTY
    VERBOSE = args.verbose
    if args.sovereignty:
        _DRIVER_DEFAULT_SOVEREIGNTY = args.sovereignty
        print(f"[DRIVER] Phase 0.5 sov-consult: default sovereignty = "
              f"{_DRIVER_DEFAULT_SOVEREIGNTY} (per --sovereignty)")
    elif _DRIVER_DEFAULT_SOVEREIGNTY != "guarded":
        print(f"[DRIVER] Phase 0.5 sov-consult: default sovereignty = "
              f"{_DRIVER_DEFAULT_SOVEREIGNTY} (per env TB_DRIVER_SOVEREIGNTY)")

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
    elif getattr(args, 'audit_stats', False):
        cmd_audit_stats()
    elif args.audit_abandon:
        for name in args.audit_abandon:
            # Accept both bare name and full path
            plan_name = Path(name).name if "/" in name else name
            if not plan_name.endswith(".md"):
                plan_name += ".md"
            plan_path = Path.home() / ".claude" / "plans" / plan_name
            if not plan_path.exists():
                print(f"[AUDIT] Plan not found: {plan_name}")
                continue
            _record_audit_result(
                plan_filename=plan_name,
                plan_mtime=plan_path.stat().st_mtime,
                verdict="ABANDONED",
                turns=0, duration_s=0, session_id="",
            )
        print(f"[AUDIT] Marked {len(args.audit_abandon)} plan(s) as ABANDONED")
    elif args.tb_loop is not None:
        branch = args.branch or "tb/orchestrate"
        run_tb_loop(args.tb_loop, branch)
    elif args.compound_audit is not None:
        branch = args.branch or "tb/compound-audit"
        run_compound_audit_mode(args.compound_audit, branch)
    elif args.compound is not None:
        branch = args.branch or "tb/nucleus-work"
        run_compound_mode(branch, sparring_rounds=args.compound)
    elif args.audit_plans is not None:
        run_plan_audit_mode(args.audit_plans, args.session or "",
                            args.branch or "tb/plan-audit",
                            skip=args.audit_skip,
                            force=args.audit_force)
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


# ─── Lever-gate runtime — appended to fix broken test_lever_compounding.py imports ───
# Source: tb/plan-audit lines 1166-1616 (file-extracted from preserve_tag)
# Defines: LEVER_LEDGER_PATH, _lever_gate_scan, _find_lever_findings_in_diff,
#          _emit_plan_audit_spawner_event, _REAUDIT_BUCKETS, BUCKET_SPAWN_POLICY,
#          _spawn_plan_audit_fix_tasks
LEVER_LEDGER_PATH = BRAIN_PATH / "ledger" / "events.jsonl"


def _lever_gate_scan(git_diff: str,
                     ledger_path: Optional[Path] = None,
                     window: int = 100) -> Dict[str, Any]:
    """Fail-closed scan of recent ledger events against a diff.

    Returns a dict ``{"matches": [...], "status": "clean"|"found"|"unknown"}``.

    ``status`` is the key the gate trusts:
      - ``clean``   — ledger readable, no findings touch diff files
      - ``found``   — ledger readable, one or more findings touch diff files
      - ``unknown`` — ledger unreadable/parse-error/missing. The gate MUST
                     force DEEPEN on unknown, never silently ACCEPT
                     (substrate posture: fail-closed on read errors).

    ``matches`` is always a list; on ``unknown`` it is empty.
    """
    path = ledger_path if ledger_path is not None else LEVER_LEDGER_PATH
    if not git_diff:
        return {"matches": [], "status": "clean"}
    if not path.exists():
        return {"matches": [], "status": "clean"}

    diff_files = set()
    for line in git_diff.splitlines():
        if line.startswith("+++ b/"):
            diff_files.add(line[6:].strip())
        elif line.startswith("diff --git a/") and " b/" in line:
            diff_files.add(line.split(" b/", 1)[1].strip())
    if not diff_files:
        return {"matches": [], "status": "clean"}

    try:
        raw_lines = path.read_text(encoding="utf-8").strip().splitlines()
    except (OSError, UnicodeDecodeError) as e:
        print(f"[LEVER_GATE] ledger unreadable — forcing DEEPEN: {e}")
        return {"matches": [], "status": "unknown", "reason": f"read_error: {e}"}

    matches: List[Dict] = []
    corrupt = 0
    for line in raw_lines[-window:]:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            corrupt += 1
            continue
        etype = event.get("type", "")
        if not (etype.startswith("lever.") and etype.endswith(".observation")):
            continue
        if event.get("outcome") != "found":
            continue
        findings = event.get("detail", {}).get("findings", [])
        finding_text = "\n".join(findings) if isinstance(findings, list) else str(findings)
        if any(f in finding_text for f in diff_files):
            matches.append(event)
    status = "found" if matches else "clean"
    result: Dict[str, Any] = {"matches": matches, "status": status}
    if corrupt:
        result["corrupt_lines"] = corrupt
    return result


def _find_lever_findings_in_diff(git_diff: str,
                                 ledger_path: Optional[Path] = None,
                                 window: int = 100) -> List[Dict]:
    """Backward-compat wrapper — returns only the matches list.

    Phase D scoring uses this to dock reviews that ACCEPT over flagged
    files. For the fail-closed gate, use ``_lever_gate_scan`` instead so
    ``unknown`` (ledger unreadable) can force DEEPEN.
    """
    return _lever_gate_scan(git_diff, ledger_path, window)["matches"]


def _spawn_lever_fix_task(parent_task: Dict, lever_matches: List[Dict],
                          tasks_path: Optional[Path] = None) -> Optional[str]:
    """Spawn a fix task for lever findings. Day-0 compounding — no LLM.

    Dedupes: if a pending lever-fix task with the same lever set + file set
    already exists, returns None and does not create a new one.

    Returns the new task id (or existing deduped id), or None on failure.
    """
    path = tasks_path if tasks_path is not None else TASKS_PATH
    try:
        lever_names = sorted({m.get("lever", "?") for m in lever_matches})
        affected_files: set = set()
        finding_samples: List[str] = []
        file_exts = (".py", ".js", ".ts", ".tsx", ".yaml", ".yml",
                     ".md", ".json", ".sh", ".toml")
        for m in lever_matches:
            findings = m.get("detail", {}).get("findings", [])
            if isinstance(findings, list):
                for f in findings[:3]:
                    finding_samples.append(f)
                    # Parse tokens and file:line:col forms; collect path-like bits.
                    for token in str(f).split():
                        token = token.rstrip(",.)")
                        for candidate in [token] + token.split(":"):
                            if "/" in candidate and candidate.endswith(file_exts):
                                affected_files.add(candidate)
                                break

        dedup_key = f"{','.join(lever_names)}|{','.join(sorted(affected_files))}"

        if path.exists():
            data = json.loads(path.read_text())
        else:
            data = {"tasks": []}
        tasks = data.get("tasks", [])

        for t in tasks:
            if (t.get("source") == "lever_gate"
                    and t.get("status") in ("pending", "in_progress")
                    and t.get("lever_gate_dedup_key") == dedup_key):
                return t.get("id")

        ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        new_id = f"lever-fix-{'-'.join(lever_names)}-{ts}"
        description_lines = [
            f"Lever gate spawned this task from {len(lever_matches)} finding(s).",
            f"Levers: {', '.join(lever_names)}",
            f"Parent task: {parent_task.get('id', '?')}",
            "",
            "Sample findings:",
        ] + [f"  - {f}" for f in finding_samples[:8]]
        scope = sorted(affected_files) if affected_files else parent_task.get("scope", ["**"])

        new_task = {
            "id": new_id,
            "title": f"Fix {','.join(lever_names)} findings in {parent_task.get('id', '?')}",
            "description": "\n".join(description_lines),
            "scope": scope,
            "priority": "high",
            "status": "pending",
            "assigned_to": "tb",
            "created_at": datetime.now().isoformat(),
            "source": "lever_gate",
            "lever_gate_dedup_key": dedup_key,
            "lever_gate_parent_task_id": parent_task.get("id", ""),
        }
        tasks.append(new_task)
        data["tasks"] = tasks
        data["schema_version"] = data.get("schema_version", 1)
        data["updated_at"] = datetime.now().isoformat()
        path.write_text(json.dumps(data, indent=2))
        return new_id
    except Exception as e:
        print(f"[LEVER_GATE] task spawn failed (non-fatal): {e}")
        return None


def _emit_plan_audit_spawner_event(ledger_path: Path, outcome: str,
                                    detail: Dict) -> None:
    """Emit one contract-conformant ``lever.plan_audit_spawner.observation``.

    Uses ``LedgerEvent.for_lever_observation`` so the event type is always
    ``lever.plan_audit_spawner.observation`` (the helper hardcodes the
    ``.observation`` suffix). Never raises — ledger write failures are
    absorbed so the spawner path never breaks session startup.
    """
    try:
        from scripts.levers.base import LedgerEvent, LedgerSchemaError
    except ImportError as e:
        print(f"[PLAN_AUDIT_SPAWNER] LedgerEvent import failed: {e}")
        return
    try:
        event = LedgerEvent.for_lever_observation(
            lever_name="plan_audit_spawner",
            observation={"outcome": outcome, "detail": detail},
        )
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ledger_path, "a", encoding="utf-8") as f:
            f.write(event.to_jsonl() + "\n")
    except (OSError, LedgerSchemaError) as e:
        print(f"[PLAN_AUDIT_SPAWNER] ledger publish failed (non-fatal): {e}")


# Wave 8 — dispatch policy for plan_audit spawner.
#
# Re-audit buckets fall through to the default ``audit-plan-<stem>`` task
# (re-running TB's --audit-plans is the right fix).
#
# Non-re-audit buckets look up BUCKET_SPAWN_POLICY to decide the task
# type. Wave 9 will append ``unverifiable`` and ``drift_detected`` entries
# (the latter with ``task_kwargs={"force": True}`` so the dispatcher adds
# --audit-force to the instruction).
_REAUDIT_BUCKETS = frozenset({
    "never_audited",
    "stale",
    "needs_deepen",
    "deepen_exhausted",
    "failed_audit",
})

BUCKET_SPAWN_POLICY: Dict[str, Dict[str, Any]] = {
    "verified_no_evidence": {
        "task_type": "add-verification",
        "task_kwargs": {},
    },
    # Wave 9 — lever can never auto-grade this plan; structural fix is
    # to add `## Files Modified` / `## Verification`. Same shape as
    # verified_no_evidence.
    "unverifiable": {
        "task_type": "add-verification",
        "task_kwargs": {},
    },
    # Wave 9 — a referenced file was edited after the audit. Re-auditing
    # is the right fix, but TB auto-skips ACCEPT verdicts; force=True so
    # the dispatcher emits the `--audit-force` hint in the description.
    "drift_detected": {
        "task_type": "audit-plan",
        "task_kwargs": {"force": True},
    },
}


def _spawn_plan_audit_fix_tasks(
    tasks_path: Optional[Path] = None,
    ledger_path: Optional[Path] = None,
) -> List[str]:
    """Wave 7+8 — convert plan_audit findings into TB task bank entries.

    Reads the most recent ``lever.plan_audit.observation`` from the
    ledger. For each plan in ``detail.top_rot``, dispatches through
    ``BUCKET_SPAWN_POLICY`` and ``_REAUDIT_BUCKETS`` to decide the task
    shape, unless a pending/in_progress task with the same id already
    exists (dedupe). Plans that vanished from disk between the lever
    fire and this call are skipped (orphan guard).

    Bucket → task-type map (Waves 8+9):

      verified_no_evidence, unverifiable → add-verification-<stem>
        (plan-edit task, NOT re-audit: re-running --audit-plans on a
        plan without parseable `## Files Modified` / `## Verification`
        just produces another quality=none verdict; the structural
        fix is to add those sections).
      drift_detected → audit-plan-<stem>  (re-audit with force=True:
        a referenced file changed after the audit; force the dispatcher
        to emit --audit-force so TB doesn't auto-skip the ACCEPT verdict).
      never_audited, stale, needs_deepen, deepen_exhausted, failed_audit
        → audit-plan-<stem>  (default re-audit task).
      deepen_exhausted also gets ' --audit-force REQUIRED' in the
        description (TB auto-skips otherwise).

    Emission policy (silent-unless-action-or-degraded, to avoid ledger
    flood on frequent session inits):

      N > 0 tasks created  → outcome=found,  detail={created_count,
                              deduped_count, plan_names, skipped_orphans}
      tasks.json unreadable → outcome=skipped, detail={stage: tasks_json_read,
                              error}, returns []
      ledger unreadable     → outcome=skipped, detail={stage: ledger_read,
                              error}, returns []
      no observation / all  → SILENT (no event emitted)
      deduped / no top_rot

    Returns list of newly-created task ids (empty on no-op or failure).
    """
    tpath = tasks_path if tasks_path is not None else TASKS_PATH
    lpath = ledger_path if ledger_path is not None else LEVER_LEDGER_PATH

    # 1. Read ledger tail for most-recent plan_audit observation
    try:
        lines = lpath.read_text(encoding="utf-8").splitlines() if lpath.exists() else []
    except (OSError, UnicodeDecodeError) as e:
        _emit_plan_audit_spawner_event(
            lpath, "skipped",
            {"stage": "ledger_read", "error": str(e)},
        )
        return []

    obs_detail: Optional[Dict] = None
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(raw, dict):
            continue
        if (raw.get("type") == "lever.plan_audit.observation"
                and raw.get("outcome") == "found"):
            d = raw.get("detail")
            if isinstance(d, dict):
                obs_detail = d
                break

    if obs_detail is None:
        return []
    top_rot = obs_detail.get("top_rot") or []
    if not isinstance(top_rot, list) or not top_rot:
        return []

    # 2. Read existing tasks for dedupe
    try:
        if tpath.exists():
            data = json.loads(tpath.read_text(encoding="utf-8"))
        else:
            data = {"tasks": []}
    except (OSError, json.JSONDecodeError) as e:
        _emit_plan_audit_spawner_event(
            lpath, "skipped",
            {"stage": "tasks_json_read", "error": str(e)},
        )
        return []

    if not isinstance(data, dict):
        _emit_plan_audit_spawner_event(
            lpath, "skipped",
            {"stage": "tasks_json_read", "error": "expected object"},
        )
        return []
    tasks = data.get("tasks") or []
    if not isinstance(tasks, list):
        tasks = []
    existing_open_ids = {
        t.get("id") for t in tasks
        if isinstance(t, dict) and t.get("status") in ("pending", "in_progress")
    }

    # 3. Build one task per rotting plan (skip deduped + orphan plans)
    claude_plans = Path.home() / ".claude" / "plans"
    brain_plans = PROJECT_ROOT / ".brain" / "plans"
    created_ids: List[str] = []
    created_plan_names: List[str] = []
    deduped: List[str] = []
    skipped_orphans: List[str] = []

    for plan in top_rot:
        if not isinstance(plan, dict):
            continue
        name = plan.get("name")
        if not isinstance(name, str) or not name:
            continue
        stem = name[:-3] if name.endswith(".md") else name
        bucket = plan.get("bucket", "?")

        # R13: dispatch by bucket. BUCKET_SPAWN_POLICY wins if the bucket
        # has custom task semantics; otherwise re-audit buckets fall
        # through to the default audit-plan task. Unknown buckets are
        # skipped silently (shouldn't reach here — lever only puts
        # rotting buckets in top_rot).
        policy = BUCKET_SPAWN_POLICY.get(bucket)
        if policy is not None:
            task_type = policy["task_type"]
            task_kwargs = policy.get("task_kwargs", {}) or {}
        elif bucket in _REAUDIT_BUCKETS:
            task_type = "audit-plan"
            task_kwargs = {}
        else:
            continue

        task_id = f"{task_type}-{stem}"

        if task_id in existing_open_ids:
            deduped.append(name)
            continue

        plan_on_disk: Optional[Path] = None
        for candidate in (claude_plans / name, brain_plans / name):
            if candidate.exists():
                plan_on_disk = candidate
                break
        if plan_on_disk is None:
            skipped_orphans.append(name)
            continue

        now_iso = datetime.now(timezone.utc).isoformat()

        if task_type == "audit-plan":
            force_flag = (
                task_kwargs.get("force", False) or bucket == "deepen_exhausted"
            )
            force_hint = (
                " --audit-force is REQUIRED: TB auto-skips this verdict."
                if force_flag
                else ""
            )
            title = f"audit plan {name}"[:80]
            description = (
                f"plan_audit lever flagged {name} as bucket="
                f"{bucket} (age {plan.get('age_days', '?')}d). "
                f"Verify plan claims against code + write verdict to "
                f".brain/audit/results.json via: python3 "
                f"scripts/third_brother_driver.py --audit-plans 1 "
                f"(newest-first; use --audit-skip K to reach this plan)."
                f"{force_hint}"
            )
        elif task_type == "add-verification":
            title = f"add verification to {name}"[:80]
            description = (
                f"plan_audit lever flagged {name} as bucket={bucket} "
                f"(age {plan.get('age_days', '?')}d). Plan was ACCEPTed "
                f"without executed verification commands (quality=none "
                f"or missing). Edit the plan to add a `## Files Modified` "
                f"or `## Verification` section listing concrete "
                f"assertions (ran pytest X, checked Y) so a future "
                f"--audit-plans fire can grade evidence. Plan-edit only; "
                f"no code changes expected."
            )
        else:
            continue

        new_task = {
            "id": task_id,
            "title": title,
            "description": description,
            "scope": [str(plan_on_disk)],
            "priority": 1,
            "status": "pending",
            "assigned_to": "tb",
            "created_at": now_iso,
            "source": "plan_audit_spawner",
            "plan_name": name,
            "plan_bucket": bucket,
        }
        tasks.append(new_task)
        created_ids.append(task_id)
        created_plan_names.append(name)

    # 4. Persist + emit only if we actually added tasks
    if created_ids:
        data["tasks"] = tasks
        data["schema_version"] = data.get("schema_version", 1)
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        try:
            tpath.write_text(json.dumps(data, indent=2))
        except OSError as e:
            _emit_plan_audit_spawner_event(
                lpath, "skipped",
                {"stage": "tasks_json_write", "error": str(e)},
            )
            return []
        _emit_plan_audit_spawner_event(
            lpath, "found",
            {
                "created_count": len(created_ids),
                "deduped_count": len(deduped),
                "plan_names": created_plan_names,
                "skipped_orphans": skipped_orphans,
            },
        )
    # else: silent no-op — no emission, avoids ledger flood on session inits

    return created_ids


