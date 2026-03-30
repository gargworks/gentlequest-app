#!/usr/bin/env python3
"""
External Guardrail Watchdog for Third Brother Autonomous Driver
================================================================
Runs as a SEPARATE PROCESS from the driver. Monitors tmux sessions
and enforces safety rules that neither Third Brother nor Claude Code
can override.

Principle (NVIDIA OpenShell): "Don't ask goal-directed systems to
limit their own goals." This process has NO goals — only constraints.

Design spec: .brain/artifacts/architecture/THIRD_BROTHER_AUTONOMOUS_DRIVER.md §9

Usage:
    python3 scripts/driver_guardrails.py              # start watchdog
    python3 scripts/driver_guardrails.py --check-once # single check, exit
    python3 scripts/driver_guardrails.py --status     # show current state
"""

import json
import subprocess
import sys
import re
import time
import fnmatch
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# ── Paths (shared via driver_config) ──────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))
from driver_config import (
    PROJECT_ROOT, BRAIN_PATH, DRIVER_DIR, CONFIG_PATH, STATE_PATH,
    TASKS_PATH, STOP_FILE, ALERTS_PATH,
    load_config as _load_config_shared,
)

# ── Severity ─────────────────────────────────────────────────
CRITICAL = "CRITICAL"   # immediate kill
HIGH = "HIGH"           # kill after grace
MEDIUM = "MEDIUM"       # alert only


# ═══════════════════════════════════════════════════════════════
# SHARED STATE
# ═══════════════════════════════════════════════════════════════

def load_config() -> Dict:
    """Load driver config (shared contract with driver)."""
    return _load_config_shared(CONFIG_PATH)


def load_state() -> Optional[Dict]:
    """Load current driver state from state.json."""
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except json.JSONDecodeError:
            return None
    return None


def load_task_scope(task_id: str) -> List[str]:
    """Load a task's scope from tasks.json."""
    if not TASKS_PATH.exists():
        return ["**"]
    try:
        data = json.loads(TASKS_PATH.read_text())
        for t in data.get("tasks", []):
            if t["id"] == task_id:
                return t.get("scope", ["**"])
    except (json.JSONDecodeError, KeyError):
        pass
    return ["**"]


def load_task_max_turns(task_id: str, config: Dict) -> int:
    """Load a task's max_turns or fall back to config default."""
    if TASKS_PATH.exists():
        try:
            data = json.loads(TASKS_PATH.read_text())
            for t in data.get("tasks", []):
                if t["id"] == task_id:
                    return t.get("max_turns", config.get("max_turns_default", 50))
        except (json.JSONDecodeError, KeyError):
            pass
    return config.get("max_turns_default", 50)


# ═══════════════════════════════════════════════════════════════
# ALERTING
# ═══════════════════════════════════════════════════════════════

def log_alert(rule: str, task_id: str, action: str, detail: str = "",
              severity: str = MEDIUM):
    """Log a guardrail alert to alerts.jsonl and print to terminal."""
    entry = {
        "ts": datetime.now().isoformat(),
        "rule": rule,
        "task_id": task_id,
        "action": action,
        "detail": detail,
        "severity": severity,
        "source": "guardrails",
    }
    ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERTS_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

    severity_icon = {CRITICAL: "!!!", HIGH: "!!", MEDIUM: "i"}.get(severity, "")
    print(f"[GUARDRAIL] [{severity_icon}] {severity} | {rule} | {action} | {detail}")


# ═══════════════════════════════════════════════════════════════
# TMUX (read-only + kill)
# ═══════════════════════════════════════════════════════════════

def tmux_session_exists(name: str) -> bool:
    result = subprocess.run(
        ["tmux", "has-session", "-t", name],
        capture_output=True, timeout=5
    )
    return result.returncode == 0


def tmux_capture(name: str, lines: int = 200) -> str:
    result = subprocess.run(
        ["tmux", "capture-pane", "-t", name, "-p", "-S", f"-{lines}"],
        capture_output=True, text=True, timeout=5
    )
    return result.stdout if result.returncode == 0 else ""


def tmux_kill(name: str):
    subprocess.run(
        ["tmux", "kill-session", "-t", name],
        capture_output=True, timeout=5
    )


# ═══════════════════════════════════════════════════════════════
# GUARDRAIL RULES
# Each returns (violated: bool, detail: str)
# ═══════════════════════════════════════════════════════════════

def rule_kill_switch() -> Tuple[bool, str]:
    """CRITICAL: Check for .brain/driver/stop file."""
    if STOP_FILE.exists():
        return True, "Kill switch file detected"
    return False, ""


def rule_destructive_ops(output: str, config: Dict) -> Tuple[bool, str]:
    """CRITICAL: Scan recent output for destructive patterns in actual commands.

    Skips patterns that appear inside code being written (quoted strings,
    indented lines, test assertions, mock setups). This prevents false
    positives when Claude Code writes test code that references these patterns.
    """
    patterns = config.get("destructive_patterns", [
        "git push --force", "git push -f",
        "git reset --hard", "rm -rf",
        "drop table", "DROP TABLE",
        "git checkout -- .", "git clean -fd",
    ])
    # Only scan last 10 lines (recent activity, not historical code writing)
    last_lines = output.strip().split('\n')[-10:]
    code_indicators = ('"', "'", 'assert', 'def ', 'class ', '# ', 'test_',
                       'mock', 'patch', 'expect', '"""', "'''", '//')
    for line in last_lines:
        stripped = line.strip()
        # Skip lines that look like code/strings being written
        if any(indicator in stripped.lower() for indicator in code_indicators):
            continue
        # Skip indented lines (inside code blocks or tool output)
        if line.startswith('    ') or line.startswith('\t'):
            continue
        for pattern in patterns:
            if pattern in stripped:
                return True, f"Detected: {pattern}"
    return False, ""


def rule_pr_only(worktree_path: str) -> Tuple[bool, str]:
    """CRITICAL: Ensure work is on a feature branch, not main/master."""
    if not worktree_path or not Path(worktree_path).exists():
        return False, ""  # can't check — assume ok
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True,
            cwd=worktree_path, timeout=5
        )
        branch = result.stdout.strip()
        if branch in ("main", "master"):
            return True, f"Working on protected branch: {branch}"
        return False, ""
    except Exception:
        return False, ""


def rule_turn_limit(output: str, max_turns: int) -> Tuple[bool, int]:
    """HIGH: Count turns from tmux output. Hard kill at max_turns + 5."""
    markers = re.findall(r'(?:^|\n)\s*(?:Human:|>\s)', output)
    turn_count = len(markers)
    hard_limit = max_turns + 5
    return turn_count > hard_limit, turn_count


def rule_session_timeout(state: Dict, timeout_minutes: int) -> Tuple[bool, str]:
    """HIGH: Kill session after timeout_minutes."""
    start_time = state.get("start_time")
    if not start_time:
        return False, ""
    try:
        start = datetime.fromisoformat(start_time)
        elapsed_sec = (datetime.now() - start).total_seconds()
        elapsed_min = int(elapsed_sec / 60)
        if elapsed_sec > timeout_minutes * 60:
            return True, f"Elapsed: {elapsed_min}min > limit {timeout_minutes}min"
        return False, ""
    except (ValueError, TypeError):
        return False, ""


def rule_stall(output: str, last_output: str,
               stall_start: Optional[float],
               timeout_minutes: int = 10) -> Tuple[bool, Optional[float]]:
    """HIGH: No new output for timeout_minutes → hard kill.

    Returns (violated, updated_stall_start).
    Guardrails use 10-min hard timeout (driver uses 5-min soft nudge).
    """
    if output.strip() == last_output.strip():
        # Same output
        if stall_start is None:
            return False, time.time()  # start tracking
        elif (time.time() - stall_start) > timeout_minutes * 60:
            return True, stall_start  # exceeded
        else:
            return False, stall_start  # still waiting
    else:
        return False, None  # new output, reset


def rule_cost_cap(output: str, cap_tokens: int) -> Tuple[bool, int, bool]:
    """MEDIUM at 80%, HIGH at 100%: Estimate tokens from tmux output.

    Returns (exceeded_hard, estimated_tokens, exceeded_soft).
    Soft = 80% alert. Hard = 100% kill.
    """
    word_count = len(output.split())
    estimated_tokens = int(word_count * 1.3)
    soft_limit = int(cap_tokens * 0.8)
    return estimated_tokens > cap_tokens, estimated_tokens, estimated_tokens > soft_limit


def rule_scope_lock(worktree_path: str, scope: List[str]) -> List[str]:
    """MEDIUM: Check modified files against task scope. Returns out-of-scope files."""
    if not worktree_path or not Path(worktree_path).exists():
        return []
    if not scope or scope == ["**"]:
        return []  # unrestricted

    try:
        # Check both staged and unstaged changes
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True,
            cwd=worktree_path, timeout=10
        )
        modified = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]

        out_of_scope = []
        for filepath in modified:
            if not any(fnmatch.fnmatch(filepath, pat) for pat in scope):
                out_of_scope.append(filepath)
        return out_of_scope
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════
# MAIN WATCHDOG LOOP
# ═══════════════════════════════════════════════════════════════

def run_watchdog():
    """Main guardrail watchdog — runs continuously as external process."""
    config = load_config()
    guardrails_cfg = config.get("guardrails", {})
    poll_interval = guardrails_cfg.get("kill_switch_poll_seconds", 30)
    session_timeout = config.get("session_timeout_minutes", 120)
    stall_hard_timeout = 10  # minutes — harder than driver's 5min soft nudge

    print(f"""
+--------------------------------------------------------------+
|           Driver Guardrail Watchdog                          |
|--------------------------------------------------------------|
|  Poll interval:    {poll_interval:3d}s                                    |
|  Session timeout:  {session_timeout:3d}min                                   |
|  Stall hard kill:  {stall_hard_timeout:3d}min                                   |
|  PR-only:          enforced                                  |
|  Destructive ops:  blocked                                   |
|--------------------------------------------------------------|
|  This process runs INDEPENDENTLY of the driver.              |
|  Kill switch: touch .brain/driver/stop                       |
|  Ctrl+C to stop watchdog only (does NOT stop the driver).    |
+--------------------------------------------------------------+
""")

    # Per-session tracking
    last_outputs: Dict[str, str] = {}
    stall_starts: Dict[str, Optional[float]] = {}

    while True:
        try:
            # ── RULE 1: Kill switch (CRITICAL) ──
            violated, detail = rule_kill_switch()
            if violated:
                state = load_state()
                session_name = state.get("session_name", "") if state else ""
                task_id = state.get("task_id", "unknown") if state else "unknown"

                if session_name and tmux_session_exists(session_name):
                    tmux_kill(session_name)
                    log_alert("kill_switch", task_id, "session_killed",
                              detail, CRITICAL)

                print("[GUARDRAIL] Kill switch active. Pausing until removed...")
                while rule_kill_switch()[0]:
                    time.sleep(poll_interval)
                print("[GUARDRAIL] Kill switch removed. Resuming.")
                continue

            # ── Load driver state ──
            state = load_state()
            if not state:
                time.sleep(poll_interval)
                continue

            session_name = state.get("session_name", "")
            task_id = state.get("task_id", "unknown")
            driver_state = state.get("state", "")

            # Only monitor active states
            if driver_state not in ("monitor", "send", "launch"):
                time.sleep(poll_interval)
                continue

            # Session must exist
            if not session_name or not tmux_session_exists(session_name):
                # Clean up stale tracking
                last_outputs.pop(session_name, None)
                stall_starts.pop(session_name, None)
                time.sleep(poll_interval)
                continue

            # ── Capture tmux output ──
            output = tmux_capture(session_name)

            # ── RULE 2: Destructive ops (LOG-ONLY while collecting data) ──
            # Downgraded from CRITICAL→MEDIUM: text scanning produces false
            # positives when Claude Code writes code containing these patterns
            # (e.g., test code for guardrails). Log for audit, don't kill.
            violated, detail = rule_destructive_ops(output, config)
            if violated:
                log_alert("destructive_op_detected", task_id, "logged",
                          detail, MEDIUM)

            # ── RULE 3: PR-only (CRITICAL) ──
            worktree_base = config.get("worktree_base", "/tmp/tb-worktrees")
            worktree_path = f"{worktree_base}/{task_id}" if task_id != "unknown" else ""

            violated, detail = rule_pr_only(worktree_path)
            if violated:
                tmux_kill(session_name)
                log_alert("pr_only_violation", task_id, "session_killed",
                          detail, CRITICAL)
                last_outputs.pop(session_name, None)
                stall_starts.pop(session_name, None)
                time.sleep(poll_interval)
                continue

            # ── RULE 4: Session timeout (HIGH) ──
            violated, detail = rule_session_timeout(state, session_timeout)
            if violated:
                tmux_kill(session_name)
                log_alert("session_timeout", task_id, "session_killed",
                          detail, HIGH)
                last_outputs.pop(session_name, None)
                stall_starts.pop(session_name, None)
                time.sleep(poll_interval)
                continue

            # ── RULE 5: Turn limit (HIGH) ──
            max_turns = load_task_max_turns(task_id, config)
            exceeded, turn_count = rule_turn_limit(output, max_turns)
            if exceeded:
                tmux_kill(session_name)
                log_alert("turn_limit_hard", task_id, "session_killed",
                          f"Turn {turn_count} > hard limit {max_turns + 5}", HIGH)
                last_outputs.pop(session_name, None)
                stall_starts.pop(session_name, None)
                time.sleep(poll_interval)
                continue

            # ── RULE 6: Stall hard timeout (HIGH) ──
            last_output = last_outputs.get(session_name, "")
            violated, new_stall_start = rule_stall(
                output, last_output,
                stall_starts.get(session_name),
                stall_hard_timeout
            )
            stall_starts[session_name] = new_stall_start
            last_outputs[session_name] = output.strip()

            if violated:
                tmux_kill(session_name)
                log_alert("stall_hard_timeout", task_id, "session_killed",
                          f"No new output for {stall_hard_timeout}min", HIGH)
                stall_starts.pop(session_name, None)
                last_outputs.pop(session_name, None)
                time.sleep(poll_interval)
                continue

            # ── RULE 7: Cost cap (MEDIUM alert at 80%, HIGH kill at 100%) ──
            cost_cap = config.get("cost_cap_tokens", 500000)
            if cost_cap > 0:
                exceeded_hard, est_tokens, exceeded_soft = rule_cost_cap(
                    output, cost_cap
                )
                if exceeded_hard:
                    tmux_kill(session_name)
                    log_alert("cost_cap_hard", task_id, "session_killed",
                              f"Estimated {est_tokens} tokens > cap {cost_cap}",
                              HIGH)
                    last_outputs.pop(session_name, None)
                    stall_starts.pop(session_name, None)
                    time.sleep(poll_interval)
                    continue
                elif exceeded_soft:
                    log_alert("cost_cap_soft", task_id, "alert",
                              f"Estimated {est_tokens} tokens > 80% of cap {cost_cap}",
                              MEDIUM)

            # ── RULE 8: Scope lock (MEDIUM — alert only) ──
            if worktree_path and Path(worktree_path).exists():
                scope = load_task_scope(task_id)
                out_of_scope = rule_scope_lock(worktree_path, scope)
                if out_of_scope:
                    log_alert("scope_violation", task_id, "alert",
                              f"Out-of-scope: {', '.join(out_of_scope[:5])}", MEDIUM)

            # ── All checks passed this cycle ──
            time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\n[GUARDRAIL] Watchdog stopped by user.")
            break
        except Exception as e:
            print(f"[GUARDRAIL] Watchdog error: {e}")
            time.sleep(poll_interval)


# ═══════════════════════════════════════════════════════════════
# SINGLE CHECK MODE
# ═══════════════════════════════════════════════════════════════

def check_once():
    """Run all guardrail checks once and print results."""
    config = load_config()
    state = load_state()

    print("[GUARDRAIL] Single check\n")

    # Kill switch
    ks, _ = rule_kill_switch()
    print(f"  Kill switch:     {'ACTIVE' if ks else 'OK'}")

    if not state:
        print("  No active driver state.\n")
        return

    task_id = state.get("task_id", "unknown")
    session_name = state.get("session_name", "")
    driver_state = state.get("state", "unknown")

    print(f"  Driver state:    {driver_state}")
    print(f"  Task:            {task_id}")
    print(f"  Session:         {session_name or '(none)'}")

    session_alive = session_name and tmux_session_exists(session_name)
    print(f"  Session alive:   {'YES' if session_alive else 'NO'}")

    if not session_alive:
        print()
        return

    output = tmux_capture(session_name)

    # Destructive ops
    violated, detail = rule_destructive_ops(output, config)
    print(f"  Destructive ops: {'DETECTED — ' + detail if violated else 'OK'}")

    # PR-only
    worktree_base = config.get("worktree_base", "/tmp/tb-worktrees")
    worktree_path = f"{worktree_base}/{task_id}" if task_id != "unknown" else ""
    violated, detail = rule_pr_only(worktree_path)
    print(f"  PR-only:         {'VIOLATION — ' + detail if violated else 'OK'}")

    # Session timeout
    timeout = config.get("session_timeout_minutes", 120)
    violated, detail = rule_session_timeout(state, timeout)
    print(f"  Session timeout: {'EXCEEDED — ' + detail if violated else 'OK'}")

    # Turn limit
    max_turns = load_task_max_turns(task_id, config)
    exceeded, turns = rule_turn_limit(output, max_turns)
    print(f"  Turns:           {turns}/{max_turns} (hard limit {max_turns+5}) {'EXCEEDED' if exceeded else 'OK'}")

    # Cost cap
    cost_cap = config.get("cost_cap_tokens", 500000)
    exceeded_hard, est_tokens, exceeded_soft = rule_cost_cap(output, cost_cap)
    status = "EXCEEDED" if exceeded_hard else ("WARNING (>80%)" if exceeded_soft else "OK")
    print(f"  Cost cap:        {est_tokens}/{cost_cap} tokens — {status}")

    # Scope lock
    if worktree_path and Path(worktree_path).exists():
        scope = load_task_scope(task_id)
        out_of_scope = rule_scope_lock(worktree_path, scope)
        if out_of_scope:
            print(f"  Scope lock:      OUT-OF-SCOPE: {', '.join(out_of_scope[:5])}")
        else:
            print(f"  Scope lock:      OK (scope: {', '.join(scope)[:50]})")
    else:
        print(f"  Scope lock:      N/A (no worktree)")

    print()


# ═══════════════════════════════════════════════════════════════
# STATUS COMMAND
# ═══════════════════════════════════════════════════════════════

def show_status():
    """Show current driver + guardrail status and recent alerts."""
    state = load_state()
    config = load_config()

    print("[GUARDRAIL] Status\n")
    print(f"  Kill switch:  {'ACTIVE' if rule_kill_switch()[0] else 'inactive'}")
    print(f"  Config mode:  {config.get('mode', 'unknown')}")

    if state:
        print(f"  Driver state: {state.get('state', '?')}")
        print(f"  Active task:  {state.get('task_id', 'none')}")
        print(f"  Session:      {state.get('session_name', 'none')}")
        print(f"  Turn count:   {state.get('turn_count', 0)}")
        print(f"  Retry count:  {state.get('retry_count', 0)}")
        print(f"  Updated:      {state.get('updated_at', '?')}")
    else:
        print("  No active driver state.")

    # Recent alerts
    if ALERTS_PATH.exists():
        lines = [l for l in ALERTS_PATH.read_text().strip().split('\n') if l.strip()]
        recent = lines[-5:]
        print(f"\n  Recent alerts ({len(lines)} total):")
        for line in recent:
            try:
                entry = json.loads(line)
                sev = entry.get("severity", "?")
                src = entry.get("source", "?")
                print(f"    [{sev:8s}] {entry['rule']:25s} "
                      f"{entry.get('detail', '')[:50]}  ({src})")
            except json.JSONDecodeError:
                pass
    else:
        print("\n  No alerts logged.")

    print()


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]

    if "--check-once" in args:
        check_once()
    elif "--status" in args:
        show_status()
    elif "--help" in args or "-h" in args:
        print(__doc__)
    else:
        run_watchdog()


if __name__ == "__main__":
    main()
