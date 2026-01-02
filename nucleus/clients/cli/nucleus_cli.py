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
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import requests
try:
    from nucleus import get_state, set_state, emit_event
except ImportError:
    # Allow running without nucleus local package if in remote mode
    pass

def show_status():
    """Display brain status."""
    from nucleus import get_state
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

def show_remote_status(url: str):
    """Display remote brain status."""
    try:
        resp = requests.get(f"{url}/api/brain/status")
        resp.raise_for_status()
        # API returns the state object directly
        state = resp.json() 
        sprint = state.get("current_sprint", {})
        counters = state.get("counters", {})
        
        print(f"\n🧠 NUCLEUS STATUS [REMOTE: {url}]")
        print("="*40)
        print(f"Sprint: {sprint.get('name', 'None')}")
        print(f"Status: {sprint.get('status', 'UNKNOWN')}")
        print(f"Events: {counters.get('total_events', 0)}")
        print(f"Tasks: {counters.get('tasks_completed', 0)}")
        print(f"Last Updated: {state.get('last_updated', 'Never')}")
        print("="*40 + "\n")
    except Exception as e:
        print(f"❌ Error connecting to {url}: {e}")

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

def start_remote_sprint(url: str, name: str):
    """Start a new sprint remotely."""
    try:
        data = {
            "goal": name,
            "emitter": "cli"
        }
        resp = requests.post(f"{url}/api/brain/sprint", json=data)
        resp.raise_for_status()
        print(f"✅ Remote Sprint '{name}' started")
    except Exception as e:
        print(f"❌ Error starting sprint on {url}: {e}")

def main():
    if len(sys.argv) < 2:
        show_status()
        return
    
    else:
        print("Usage: nucleus [status|sprint <name>|event <type>]")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Nucleus CLI")
    parser.add_argument("command", choices=["status", "sprint", "event"], help="Command to execute")
    parser.add_argument("args", nargs="*", help="Arguments for the command")
    parser.add_argument("--url", help="Remote Nucleus API URL")
    
    args = parser.parse_args()
    
    if args.url:
        # Remote mode
        if args.command == "status":
            show_remote_status(args.url)
        elif args.command == "sprint" and args.args:
            start_remote_sprint(args.url, " ".join(args.args))
        elif args.command == "event" and args.args:
            # Emit event not fully implemented in remote yet, need endpoint
            print("Event emission not yet supported in remote mode (needs /api/brain/events endpoints)")
    else:
        # Local mode
        if args.command == "status":
            show_status()
        elif args.command == "sprint" and args.args:
            start_sprint(" ".join(args.args))
        elif args.command == "event" and args.args:
            event_type = args.args[0]
            event_args = args.args[1:]
            event_id = emit_event("cli", event_type, {"args": event_args})
            print(f"✅ Event emitted: {event_id}")

if __name__ == "__main__":
    main()
