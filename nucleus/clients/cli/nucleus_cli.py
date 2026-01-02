#!/usr/bin/env python3
"""
Nucleus CLI - Brain Control Interface
======================================
Usage:
    nucleus status          Show current brain state
    nucleus event <type>    Emit an event
    nucleus sprint <name>   Start a new sprint
"""

import sys
import json
from pathlib import Path

# Add parent to path for nucleus import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nucleus import get_state, set_state, emit_event

def show_status():
    """Display brain status."""
    state = get_state()
    sprint = state.get("current_sprint", {})
    counters = state.get("counters", {})
    
    print("\n🧠 NUCLEUS STATUS")
    print("="*40)
    print(f"Sprint: {sprint.get('name', 'None')}")
    print(f"Status: {sprint.get('status', 'UNKNOWN')}")
    print(f"Events: {counters.get('total_events', 0)}")
    print(f"Tasks: {counters.get('tasks_completed', 0)}")
    print(f"Last Updated: {state.get('last_updated', 'Never')}")
    print("="*40 + "\n")

def start_sprint(name: str):
    """Start a new sprint."""
    set_state({
        "current_sprint": {
            "name": name,
            "status": "ACTIVE",
            "started": __import__("datetime").datetime.now().isoformat()
        }
    })
    emit_event("cli", "sprint_started", {"name": name})
    print(f"✅ Sprint '{name}' started")

def main():
    if len(sys.argv) < 2:
        show_status()
        return
    
    cmd = sys.argv[1]
    
    if cmd == "status":
        show_status()
    elif cmd == "sprint" and len(sys.argv) > 2:
        start_sprint(" ".join(sys.argv[2:]))
    elif cmd == "event" and len(sys.argv) > 2:
        event_type = sys.argv[2]
        event_id = emit_event("cli", event_type, {"args": sys.argv[3:]})
        print(f"✅ Event emitted: {event_id}")
    else:
        print("Usage: nucleus [status|sprint <name>|event <type>]")

if __name__ == "__main__":
    main()
