#!/usr/bin/env python3
"""
Master Controller for Unified Meta-Overhaul Sprint
===================================================
Drives the 8-hour autonomous session with disk-based state persistence.

Usage:
    python scripts/ops/master_controller.py status   # Show current phase
    python scripts/ops/master_controller.py next     # Advance to next step
    python scripts/ops/master_controller.py run      # Execute current phase
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent.parent / "autonomous_state.json"
LOG_FILE = Path(__file__).parent.parent.parent / "autonomous.log"

def log(message: str, level: str = "INFO"):
    """Append to autonomous.log with timestamp."""
    timestamp = datetime.now().isoformat()
    line = f"[{timestamp}] [{level}] {message}\n"
    with open(LOG_FILE, "a") as f:
        f.write(line)
    print(line.strip())

def load_state() -> dict:
    """Load current state from disk."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"current_phase": 0, "current_step": 1, "mode": "UNKNOWN"}

def save_state(state: dict):
    """Persist state to disk."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def show_status():
    """Display current session status."""
    state = load_state()
    phase = state.get("current_phase", 0)
    step = state.get("current_step", 1)
    mode = state.get("mode", "UNKNOWN")
    phases = state.get("phases", {})
    
    print("\n" + "="*50)
    print("🛫 UNIFIED META-OVERHAUL SESSION")
    print("="*50)
    print(f"Session ID: {state.get('session_id', 'N/A')}")
    print(f"Mode: {mode}")
    print(f"Current: Phase {phase}, Step {step}")
    print("-"*50)
    
    for p_num, p_data in phases.items():
        status_icon = "✅" if p_data["status"] == "COMPLETE" else "🔄" if p_data["status"] == "IN_PROGRESS" else "⏳"
        print(f"  {status_icon} Phase {p_num}: {p_data['name']} [{p_data['status']}]")
    
    print("="*50 + "\n")

def advance_phase():
    """Move to next phase."""
    state = load_state()
    current = state.get("current_phase", 0)
    phases = state.get("phases", {})
    
    # Mark current as complete
    if str(current) in phases:
        phases[str(current)]["status"] = "COMPLETE"
        phases[str(current)]["completed"] = datetime.now().isoformat()
    
    # Advance
    next_phase = current + 1
    if str(next_phase) in phases:
        state["current_phase"] = next_phase
        state["current_step"] = 1
        phases[str(next_phase)]["status"] = "IN_PROGRESS"
        phases[str(next_phase)]["started"] = datetime.now().isoformat()
        log(f"Advanced to Phase {next_phase}: {phases[str(next_phase)]['name']}")
    else:
        log("All phases complete!", "SUCCESS")
    
    state["phases"] = phases
    save_state(state)
    show_status()

def add_checkpoint(message: str):
    """Add a checkpoint to state."""
    state = load_state()
    checkpoints = state.get("checkpoints", [])
    checkpoints.append({
        "time": datetime.now().isoformat(),
        "phase": state.get("current_phase"),
        "message": message
    })
    state["checkpoints"] = checkpoints
    save_state(state)
    log(f"Checkpoint: {message}")

def record_error(error: str):
    """Record an error."""
    state = load_state()
    errors = state.get("errors", [])
    errors.append({
        "time": datetime.now().isoformat(),
        "phase": state.get("current_phase"),
        "error": error
    })
    state["errors"] = errors
    save_state(state)
    log(f"Error: {error}", "ERROR")

def main():
    if len(sys.argv) < 2:
        show_status()
        return
    
    cmd = sys.argv[1]
    
    if cmd == "status":
        show_status()
    elif cmd == "next":
        advance_phase()
    elif cmd == "checkpoint":
        msg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Manual checkpoint"
        add_checkpoint(msg)
    elif cmd == "error":
        err = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Unknown error"
        record_error(err)
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: master_controller.py [status|next|checkpoint|error]")

if __name__ == "__main__":
    main()
