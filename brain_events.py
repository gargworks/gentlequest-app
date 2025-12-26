#!/usr/bin/env python3
"""
Brain Event Utilities
=====================
Helper functions for emitting and reading events in the Nuclear Brain.

Usage:
    from brain_events import emit_event, read_recent_events, get_pending_triggers
    
This module provides tool-agnostic event handling for the .brain/ ledger.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4

# ============================================================================
# CONFIGURATION
# ============================================================================

BRAIN_ROOT = Path(__file__).parent / ".brain"
EVENTS_FILE = BRAIN_ROOT / "ledger" / "events.jsonl"
STATE_FILE = BRAIN_ROOT / "ledger" / "state.json"
TRIGGERS_FILE = BRAIN_ROOT / "ledger" / "triggers.json"

# ============================================================================
# EVENT SCHEMA
# ============================================================================

"""
Event Schema v1.0
=================

Required Fields:
- event_id: str (UUID v4)
- timestamp: str (ISO8601 UTC)
- emitter: str (agent name or "system")
- event_type: str (matches trigger definitions)
- severity: str ("ROUTINE" | "NOTABLE" | "CRITICAL")
- payload: dict (event-specific data)

Optional Fields:
- metadata.task_id: str (reference to related task)
- metadata.parent_event: str (for event chains)
- metadata.ttl_hours: int (expiry time)

Example:
{
    "event_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-12-26T21:44:00Z",
    "emitter": "developer",
    "event_type": "implementation_complete",
    "severity": "NOTABLE",
    "payload": {
        "feature": "function_calling",
        "files_changed": ["providers/gemini.py"],
        "tests_passed": true
    },
    "metadata": {
        "task_id": "task-001"
    }
}
"""

# Valid severity levels
SEVERITY_LEVELS = ["ROUTINE", "NOTABLE", "CRITICAL"]

# Valid event types (from triggers.json)
EVENT_TYPES = [
    "brain_initialized",
    "strategy_updated",
    "spec_ready_for_development",
    "implementation_complete",
    "review_approved",
    "review_blocked",
    "market_shift_detected",
    "founder_decision_needed",
    "meta_optimization_complete",
    "sprint_started",
    "sprint_completed",
    "task_assigned",
    "task_completed",
    "daily_digest_generated",
]


# ============================================================================
# EVENT EMISSION
# ============================================================================

def emit_event(
    emitter: str,
    event_type: str,
    severity: str,
    payload: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Emit an event to the event stream.
    
    Args:
        emitter: Name of the agent emitting (e.g., "developer", "synthesizer")
        event_type: Type of event (must match trigger definitions)
        severity: "ROUTINE", "NOTABLE", or "CRITICAL"
        payload: Event-specific data
        metadata: Optional metadata (task_id, parent_event, etc.)
    
    Returns:
        event_id: The UUID of the emitted event
    
    Example:
        event_id = emit_event(
            emitter="developer",
            event_type="implementation_complete",
            severity="NOTABLE",
            payload={
                "feature": "function_calling",
                "files_changed": ["providers/gemini.py"],
                "tests_passed": True
            }
        )
    """
    # Validate severity
    if severity not in SEVERITY_LEVELS:
        raise ValueError(f"Invalid severity: {severity}. Must be one of {SEVERITY_LEVELS}")
    
    # Create event
    event_id = str(uuid4())
    event = {
        "event_id": event_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "emitter": emitter,
        "event_type": event_type,
        "severity": severity,
        "payload": payload,
        "metadata": metadata or {}
    }
    
    # Append to events.jsonl
    with open(EVENTS_FILE, 'a') as f:
        f.write(json.dumps(event) + '\n')
    
    # Update state counters
    _increment_event_counter()
    
    return event_id


def _increment_event_counter():
    """Increment the total event counter in state.json"""
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        state["counters"]["total_events"] += 1
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass  # Non-critical, continue


# ============================================================================
# EVENT READING
# ============================================================================

def read_recent_events(count: int = 50) -> List[Dict]:
    """
    Read the most recent events from the event stream.
    
    Args:
        count: Number of recent events to return
    
    Returns:
        List of event dictionaries, most recent last
    """
    events = []
    
    if not EVENTS_FILE.exists():
        return events
    
    with open(EVENTS_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    return events[-count:]


def read_events_by_type(event_type: str, count: int = 10) -> List[Dict]:
    """
    Read events of a specific type.
    
    Args:
        event_type: The event type to filter by
        count: Maximum number to return
    
    Returns:
        List of matching events
    """
    all_events = read_recent_events(500)  # Search more events
    matching = [e for e in all_events if e.get("event_type") == event_type]
    return matching[-count:]


def read_events_by_severity(severity: str) -> List[Dict]:
    """
    Read all events of a specific severity level.
    
    Args:
        severity: "ROUTINE", "NOTABLE", or "CRITICAL"
    
    Returns:
        List of matching events
    """
    all_events = read_recent_events(500)
    return [e for e in all_events if e.get("severity") == severity]


# ============================================================================
# TRIGGER PROCESSING
# ============================================================================

def get_triggers() -> Dict:
    """Load trigger definitions from triggers.json"""
    with open(TRIGGERS_FILE, 'r') as f:
        return json.load(f)


def find_matching_triggers(event: Dict) -> List[Dict]:
    """
    Find triggers that match a given event.
    
    Args:
        event: The event to match
    
    Returns:
        List of matching trigger definitions
    """
    triggers = get_triggers()
    event_type = event.get("event_type")
    matching = []
    
    for trigger in triggers.get("triggers", []):
        if trigger.get("event_type") == event_type:
            if _evaluate_condition(trigger.get("condition", {}), event):
                matching.append(trigger)
    
    return matching


def _evaluate_condition(condition: Dict, event: Dict) -> bool:
    """
    Evaluate if a trigger condition is met.
    
    Condition types:
    - always: Always true
    - severity_gte: Severity >= value
    - severity_eq: Severity == value
    - payload_contains: Payload has key
    """
    cond_type = condition.get("type", "always")
    
    if cond_type == "always":
        return True
    
    if cond_type == "severity_gte":
        levels = {"ROUTINE": 0, "NOTABLE": 1, "CRITICAL": 2}
        event_level = levels.get(event.get("severity", "ROUTINE"), 0)
        required_level = levels.get(condition.get("value", "ROUTINE"), 0)
        return event_level >= required_level
    
    if cond_type == "severity_eq":
        return event.get("severity") == condition.get("value")
    
    if cond_type == "payload_contains":
        key = condition.get("value")
        return key in event.get("payload", {})
    
    return True  # Default to true for unknown conditions


def get_agents_to_activate(event: Dict) -> List[str]:
    """
    Determine which agents should be activated for an event.
    
    Args:
        event: The event to process
    
    Returns:
        List of agent names to activate
    """
    matching_triggers = find_matching_triggers(event)
    agents = set()
    
    for trigger in matching_triggers:
        activates = trigger.get("activates", [])
        if activates == ["*"]:
            # Activate all agents
            agents.update(["strategist", "architect", "developer", 
                          "critic", "researcher", "synthesizer"])
        else:
            agents.update(activates)
    
    return list(agents)


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def get_state() -> Dict:
    """Load current brain state"""
    with open(STATE_FILE, 'r') as f:
        return json.load(f)


def update_state(updates: Dict) -> None:
    """
    Update brain state with new values.
    
    Args:
        updates: Dictionary of fields to update
    """
    state = get_state()
    
    def deep_update(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d:
                deep_update(d[k], v)
            else:
                d[k] = v
    
    deep_update(state, updates)
    state["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def set_active_agents(agents: List[str]) -> None:
    """Update the list of currently active agents"""
    update_state({"active_agents": agents})


def get_pending_events() -> List[Dict]:
    """Get events that haven't been processed yet"""
    state = get_state()
    return state.get("pending_events", [])


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def emit_task_assigned(
    target_agent: str,
    task_description: str,
    expected_output: str,
    context_files: Optional[List[str]] = None,
    deadline_hours: int = 24
) -> str:
    """
    Convenience function to emit a task assignment event.
    
    Example:
        emit_task_assigned(
            target_agent="developer",
            task_description="Implement RAG memory layer",
            expected_output="artifacts/code/rag_implementation.md",
            context_files=["memory/context.md"],
            deadline_hours=48
        )
    """
    return emit_event(
        emitter="synthesizer",
        event_type="task_assigned",
        severity="NOTABLE",
        payload={
            "target_agent": target_agent,
            "task_description": task_description,
            "expected_output": expected_output,
            "deadline_hours": deadline_hours,
            "context_files": context_files or []
        }
    )


def emit_task_completed(
    agent: str,
    task_description: str,
    output_path: str,
    success: bool = True,
    notes: str = ""
) -> str:
    """
    Convenience function to emit a task completion event.
    
    Example:
        emit_task_completed(
            agent="developer",
            task_description="Implement RAG memory layer",
            output_path="artifacts/code/rag_implementation.md",
            success=True
        )
    """
    return emit_event(
        emitter=agent,
        event_type="task_completed",
        severity="NOTABLE" if success else "CRITICAL",
        payload={
            "task_description": task_description,
            "output_path": output_path,
            "success": success,
            "notes": notes
        }
    )


def emit_founder_escalation(
    agent: str,
    reason: str,
    options: List[str],
    context: str = ""
) -> str:
    """
    Emit a CRITICAL event requiring founder decision.
    
    Example:
        emit_founder_escalation(
            agent="architect",
            reason="Database migration requires downtime",
            options=["Schedule for 3AM", "Do rolling migration", "Defer to next sprint"],
            context="PostgreSQL upgrade from 15 to 16"
        )
    """
    return emit_event(
        emitter=agent,
        event_type="founder_decision_needed",
        severity="CRITICAL",
        payload={
            "reason": reason,
            "options": options,
            "context": context
        }
    )


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python brain_events.py <command>")
        print("Commands:")
        print("  recent [count]    - Show recent events")
        print("  state             - Show current state")
        print("  emit <type> <msg> - Emit a test event")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "recent":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        events = read_recent_events(count)
        for e in events:
            print(json.dumps(e, indent=2))
    
    elif command == "state":
        state = get_state()
        print(json.dumps(state, indent=2))
    
    elif command == "emit":
        event_type = sys.argv[2] if len(sys.argv) > 2 else "test_event"
        message = sys.argv[3] if len(sys.argv) > 3 else "Test event from CLI"
        event_id = emit_event(
            emitter="cli",
            event_type=event_type,
            severity="ROUTINE",
            payload={"message": message}
        )
        print(f"Emitted event: {event_id}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
