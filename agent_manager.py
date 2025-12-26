#!/usr/bin/env python3
"""
Nuclear Brain Agent Manager - Automated Flywheel
=================================================

This script replaces manual copy-pasting of handshake prompts.
It monitors events.jsonl, activates agents automatically, and maintains
the "set-and-forget" protocol for Level 5 Autonomy.

Usage:
    # Start the flywheel (runs until CRITICAL event or manual stop)
    python agent_manager.py start
    
    # Check current status
    python agent_manager.py status
    
    # Stop the flywheel gracefully
    python agent_manager.py stop
    
    # Start a new sprint (only human interaction needed)
    python agent_manager.py sprint "Goal description"

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    AGENT MANAGER FLYWHEEL                   │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │   events.jsonl ──► Event Loop ──► Agent Router ──► Execute  │
    │        ▲                                              │     │
    │        └──────────────── Output Events ◄──────────────┘     │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘

Author: Nuclear Architecture Synthesizer
Version: 2025.Final
"""

import json
import os
import sys
import time
import signal
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import queue
import logging

# ============================================================================
# CONFIGURATION
# ============================================================================

BRAIN_ROOT = Path(__file__).parent / ".brain"
LEDGER_DIR = BRAIN_ROOT / "ledger"
AGENTS_DIR = BRAIN_ROOT / "agents"
ARTIFACTS_DIR = BRAIN_ROOT / "artifacts"
MEMORY_DIR = BRAIN_ROOT / "memory"
META_DIR = BRAIN_ROOT / "meta"

STATE_FILE = LEDGER_DIR / "state.json"
EVENTS_FILE = LEDGER_DIR / "events.jsonl"
TRIGGERS_FILE = LEDGER_DIR / "triggers.json"
DECISIONS_FILE = LEDGER_DIR / "decisions.md"

# Polling interval in seconds
POLL_INTERVAL = 5

# Max events to process per cycle
MAX_EVENTS_PER_CYCLE = 10

# Flywheel PID file
PID_FILE = BRAIN_ROOT / ".flywheel.pid"

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(BRAIN_ROOT / "flywheel.log")
    ]
)
logger = logging.getLogger("AgentManager")

# ============================================================================
# DATA STRUCTURES
# ============================================================================

class Severity(Enum):
    ROUTINE = 0
    NOTABLE = 1
    CRITICAL = 2

@dataclass
class Event:
    event_id: str
    timestamp: str
    emitter: str
    event_type: str
    severity: str
    payload: dict
    metadata: dict = None
    
    @classmethod
    def from_json(cls, data: dict) -> 'Event':
        return cls(
            event_id=data.get('event_id', ''),
            timestamp=data.get('timestamp', ''),
            emitter=data.get('emitter', ''),
            event_type=data.get('event_type', ''),
            severity=data.get('severity', 'ROUTINE'),
            payload=data.get('payload', {}),
            metadata=data.get('metadata', {})
        )

@dataclass
class Trigger:
    id: str
    event: str
    emitter: str
    activates: List[str]
    condition: str
    
    @classmethod
    def from_json(cls, data: dict) -> 'Trigger':
        return cls(
            id=data.get('id', ''),
            event=data.get('event', ''),
            emitter=data.get('emitter', ''),
            activates=data.get('activates', []),
            condition=data.get('condition', 'always')
        )

# ============================================================================
# CORE: STATE MANAGEMENT
# ============================================================================

def load_state() -> dict:
    """Load current brain state"""
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_state(state: dict) -> None:
    """Save brain state"""
    state['last_updated'] = datetime.now(timezone.utc).isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

def load_triggers() -> List[Trigger]:
    """Load trigger definitions"""
    with open(TRIGGERS_FILE, 'r') as f:
        data = json.load(f)
    return [Trigger.from_json(t) for t in data.get('triggers', [])]

def get_last_processed_event_id() -> Optional[str]:
    """Get the ID of the last processed event"""
    state = load_state()
    return state.get('flywheel', {}).get('last_processed_event_id')

def set_last_processed_event_id(event_id: str) -> None:
    """Update the last processed event ID"""
    state = load_state()
    if 'flywheel' not in state:
        state['flywheel'] = {}
    state['flywheel']['last_processed_event_id'] = event_id
    state['flywheel']['last_processed_at'] = datetime.now(timezone.utc).isoformat()
    save_state(state)

# ============================================================================
# CORE: EVENT STREAM
# ============================================================================

def read_all_events() -> List[Event]:
    """Read all events from the stream"""
    events = []
    if not EVENTS_FILE.exists():
        return events
    
    with open(EVENTS_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(Event.from_json(json.loads(line)))
                except json.JSONDecodeError:
                    continue
    return events

def get_unprocessed_events() -> List[Event]:
    """Get events that haven't been processed yet"""
    all_events = read_all_events()
    last_id = get_last_processed_event_id()
    
    if last_id is None:
        return all_events[-MAX_EVENTS_PER_CYCLE:]
    
    # Find events after the last processed one
    unprocessed = []
    found_last = False
    for event in all_events:
        if found_last:
            unprocessed.append(event)
        elif event.event_id == last_id:
            found_last = True
    
    return unprocessed[:MAX_EVENTS_PER_CYCLE]

def emit_event(emitter: str, event_type: str, severity: str, payload: dict, metadata: dict = None) -> str:
    """Emit a new event to the stream"""
    from uuid import uuid4
    
    event = {
        "event_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "emitter": emitter,
        "event_type": event_type,
        "severity": severity,
        "payload": payload,
        "metadata": metadata or {}
    }
    
    with open(EVENTS_FILE, 'a') as f:
        f.write(json.dumps(event) + '\n')
    
    logger.info(f"Emitted: {event_type} from {emitter} [{severity}]")
    return event["event_id"]

# ============================================================================
# CORE: TRIGGER MATCHING
# ============================================================================

def matches_trigger(event: Event, trigger: Trigger) -> bool:
    """Check if an event matches a trigger condition"""
    # Check event type
    if trigger.event != event.event_type:
        return False
    
    # Check emitter (wildcard * matches all)
    if trigger.emitter != '*' and trigger.emitter != event.emitter:
        return False
    
    # Check condition
    condition = trigger.condition.lower()
    
    if condition == 'always':
        return True
    
    if 'severity' in condition:
        severity_map = {'routine': 0, 'notable': 1, 'critical': 2}
        event_severity = severity_map.get(event.severity.lower(), 0)
        
        if '>=' in condition:
            required = condition.split('>=')[1].strip()
            required_level = severity_map.get(required.lower(), 0)
            return event_severity >= required_level
        
        if '==' in condition:
            required = condition.split('==')[1].strip()
            required_level = severity_map.get(required.lower(), 0)
            return event_severity == required_level
    
    return True

def get_agents_to_activate(event: Event, triggers: List[Trigger]) -> List[str]:
    """Determine which agents should be activated for an event"""
    agents = set()
    
    for trigger in triggers:
        if matches_trigger(event, trigger):
            if trigger.activates == ['*']:
                agents.update(['strategist', 'architect', 'developer', 
                              'critic', 'researcher', 'synthesizer'])
            else:
                agents.update(trigger.activates)
    
    return list(agents)

# ============================================================================
# CORE: AGENT EXECUTION
# ============================================================================

def load_agent_prompt(agent_name: str) -> str:
    """Load an agent's system prompt"""
    prompt_file = AGENTS_DIR / f"{agent_name}.md"
    if prompt_file.exists():
        with open(prompt_file, 'r') as f:
            return f.read()
    return ""

def build_agent_context(agent_name: str, event: Event) -> str:
    """Build the context package for agent execution"""
    state = load_state()
    prompt = load_agent_prompt(agent_name)
    
    # Load memory context
    context_file = MEMORY_DIR / "context.md"
    context = ""
    if context_file.exists():
        with open(context_file, 'r') as f:
            context = f.read()
    
    # Build the execution context
    execution_context = f"""
# Agent Activation: {agent_name.upper()}

## Trigger Event
```json
{json.dumps(event.__dict__, indent=2)}
```

## Current State
```json
{json.dumps(state, indent=2)[:2000]}...
```

## Your Task
Based on the trigger event above, execute your assigned task.

## Instructions
1. Read the event payload for task details
2. Execute the task according to your system prompt
3. Write output to your designated artifacts folder
4. Emit a task_completed event when done
5. If blocked, emit a task_blocked event with details

## Context
{context[:1000]}

---
Your System Prompt follows below:
---

{prompt}
"""
    return execution_context

def execute_agent_task(agent_name: str, event: Event) -> dict:
    """
    Execute an agent's task based on an event.
    
    If GEMINI_API_KEY is set, uses brain_executor.py for real LLM execution.
    Otherwise, falls back to creating activation files for manual pickup.
    """
    logger.info(f"Activating agent: {agent_name} for event: {event.event_id}")
    
    # Check if we have LLM capability
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if api_key:
        # USE REAL LLM EXECUTION
        try:
            from brain_executor import AgentExecutor
            
            # Build task from event
            task = {
                "task_id": event.payload.get('task_id', event.event_id),
                "task_description": event.payload.get('task_description', 
                                                       event.payload.get('instruction', 
                                                       f"Process event: {event.event_type}")),
                "expected_output": event.payload.get('expected_output', 'Output based on task'),
                "deadline_hours": event.payload.get('deadline_hours', 24),
                "context_files": event.payload.get('context_files', [])
            }
            
            logger.info(f"Executing {agent_name} via Gemini API...")
            
            executor = AgentExecutor(agent_name)
            result = executor.execute(task)
            
            if result.get('success'):
                logger.info(f"Agent {agent_name} completed: {result.get('output_path')}")
                return {
                    "agent": agent_name,
                    "event_id": event.event_id,
                    "output_path": result.get('output_path'),
                    "status": "completed",
                    "mode": "llm"
                }
            else:
                logger.error(f"Agent {agent_name} failed: {result.get('error')}")
                return {
                    "agent": agent_name,
                    "event_id": event.event_id,
                    "error": result.get('error'),
                    "status": "failed",
                    "mode": "llm"
                }
                
        except ImportError as e:
            logger.warning(f"brain_executor not available: {e}")
        except Exception as e:
            logger.error(f"LLM execution error: {e}")
    
    # FALLBACK: Create activation file for manual pickup
    context = build_agent_context(agent_name, event)
    
    activation_dir = BRAIN_ROOT / "activations"
    activation_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    activation_file = activation_dir / f"{agent_name}_{timestamp}.md"
    
    with open(activation_file, 'w') as f:
        f.write(context)
    
    # Update state to show agent is active
    state = load_state()
    if agent_name not in state.get('active_agents', []):
        state.setdefault('active_agents', []).append(agent_name)
        save_state(state)
    
    logger.info(f"Created activation file: {activation_file}")
    logger.info("💡 Tip: Set GEMINI_API_KEY for automatic LLM execution")
    
    return {
        "agent": agent_name,
        "event_id": event.event_id,
        "activation_file": str(activation_file),
        "status": "activated",
        "mode": "manual"
    }

def check_for_completions() -> List[Event]:
    """Check for task completion events and process them"""
    # Look for task_completed events in the stream
    events = read_all_events()
    completions = [e for e in events if e.event_type == 'task_completed']
    return completions[-5:]  # Return last 5 completions

# ============================================================================
# CORE: FLYWHEEL LOOP
# ============================================================================

class FlywheelManager:
    """
    The main flywheel that runs continuously until stopped.
    """
    
    def __init__(self):
        self.running = False
        self.triggers = []
        self.processed_count = 0
        self.critical_events = []
        
    def start(self):
        """Start the flywheel"""
        self.running = True
        self.triggers = load_triggers()
        
        # Write PID file
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        logger.info("=" * 60)
        logger.info("NUCLEAR FLYWHEEL STARTED")
        logger.info(f"PID: {os.getpid()}")
        logger.info(f"Poll Interval: {POLL_INTERVAL}s")
        logger.info(f"Triggers Loaded: {len(self.triggers)}")
        logger.info("=" * 60)
        
        # Emit flywheel_started event
        emit_event(
            emitter="system",
            event_type="flywheel_started",
            severity="NOTABLE",
            payload={
                "pid": os.getpid(),
                "triggers_loaded": len(self.triggers)
            }
        )
        
        # Main loop
        try:
            while self.running:
                self.cycle()
                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()
    
    def cycle(self):
        """Execute one cycle of the flywheel"""
        try:
            # 1. Get unprocessed events
            events = get_unprocessed_events()
            
            if not events:
                return
            
            logger.info(f"Processing {len(events)} events")
            
            # 2. Process each event
            for event in events:
                self.process_event(event)
                self.processed_count += 1
                
                # Check for CRITICAL - halt flywheel
                if event.severity == 'CRITICAL':
                    self.critical_events.append(event)
                    logger.warning(f"CRITICAL EVENT: {event.event_id}")
                    self.escalate_to_founder(event)
                
                # Mark as processed
                set_last_processed_event_id(event.event_id)
            
        except Exception as e:
            logger.error(f"Cycle error: {e}")
            emit_event(
                emitter="system",
                event_type="flywheel_error",
                severity="NOTABLE",
                payload={"error": str(e)}
            )
    
    def process_event(self, event: Event):
        """Process a single event"""
        logger.info(f"Event: {event.event_type} from {event.emitter}")
        
        # Find matching triggers
        agents = get_agents_to_activate(event, self.triggers)
        
        if not agents:
            logger.info(f"No agents triggered for: {event.event_type}")
            return
        
        logger.info(f"Triggering agents: {agents}")
        
        # Activate each agent
        for agent in agents:
            try:
                result = execute_agent_task(agent, event)
                logger.info(f"Agent {agent} activated: {result['status']}")
            except Exception as e:
                logger.error(f"Failed to activate {agent}: {e}")
    
    def escalate_to_founder(self, event: Event):
        """Handle CRITICAL events by notifying founder"""
        # Create founder notification file
        notification_file = ARTIFACTS_DIR / "synthesis" / f"CRITICAL_{event.event_id}.md"
        notification_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(notification_file, 'w') as f:
            f.write(f"""# 🚨 CRITICAL EVENT - Founder Action Required

**Event ID:** {event.event_id}  
**Time:** {event.timestamp}  
**Emitter:** {event.emitter}  
**Type:** {event.event_type}

## Payload
```json
{json.dumps(event.payload, indent=2)}
```

## Required Action
Review this event and make a decision.

## Flywheel Status
The flywheel is PAUSED pending your decision.
Run `python agent_manager.py resume` after reviewing.
""")
        
        logger.warning(f"Founder notification created: {notification_file}")
    
    def stop(self):
        """Stop the flywheel gracefully"""
        self.running = False
        
        # Remove PID file
        if PID_FILE.exists():
            PID_FILE.unlink()
        
        # Emit flywheel_stopped event
        emit_event(
            emitter="system",
            event_type="flywheel_stopped",
            severity="NOTABLE",
            payload={
                "events_processed": self.processed_count,
                "critical_events": len(self.critical_events)
            }
        )
        
        logger.info("=" * 60)
        logger.info("NUCLEAR FLYWHEEL STOPPED")
        logger.info(f"Events Processed: {self.processed_count}")
        logger.info(f"Critical Events: {len(self.critical_events)}")
        logger.info("=" * 60)

# ============================================================================
# CLI: SPRINT MANAGEMENT
# ============================================================================

def start_sprint(goal: str):
    """Initialize a new sprint (the only human interaction needed)"""
    from uuid import uuid4
    
    state = load_state()
    sprint_id = f"sprint-{str(uuid4())[:8]}"
    
    # Create sprint definition
    sprint = {
        "id": sprint_id,
        "name": f"Sprint: {goal[:50]}",
        "started": datetime.now(timezone.utc).isoformat(),
        "ends": (datetime.now(timezone.utc) + timedelta(hours=72)).isoformat(),
        "focus": goal,
        "status": "ACTIVE",
        "objectives": [goal],
        "tasks": []
    }
    
    state['current_sprint'] = sprint
    state['active_agents'] = ['synthesizer']
    state['pending_events'] = []
    save_state(state)
    
    # Emit sprint_started event to activate Synthesizer
    emit_event(
        emitter="founder",
        event_type="sprint_started",
        severity="NOTABLE",
        payload={
            "sprint_id": sprint_id,
            "goal": goal,
            "instruction": "Synthesizer: Break down this goal into agent tasks and delegate."
        }
    )
    
    logger.info(f"Sprint started: {sprint_id}")
    logger.info(f"Goal: {goal}")
    print(f"\n✅ Sprint {sprint_id} started!")
    print(f"Goal: {goal}")
    print("\nThe flywheel will now orchestrate all agents.")
    print("Run `python agent_manager.py start` to begin processing.")

def show_status():
    """Show current flywheel status"""
    state = load_state()
    events = read_all_events()
    
    print("\n" + "=" * 60)
    print("NUCLEAR FLYWHEEL STATUS")
    print("=" * 60)
    
    # Check if running
    if PID_FILE.exists():
        with open(PID_FILE, 'r') as f:
            pid = f.read().strip()
        print(f"Status: RUNNING (PID: {pid})")
    else:
        print("Status: STOPPED")
    
    # Sprint info
    sprint = state.get('current_sprint', {})
    print(f"\nCurrent Sprint: {sprint.get('name', 'None')}")
    print(f"Sprint Status: {sprint.get('status', 'N/A')}")
    
    # Event stats
    print(f"\nTotal Events: {len(events)}")
    
    last_id = get_last_processed_event_id()
    if last_id:
        print(f"Last Processed: {last_id}")
    
    # Active agents
    print(f"\nActive Agents: {', '.join(state.get('active_agents', ['None']))}")
    
    # Recent events
    print("\nRecent Events (last 5):")
    for event in events[-5:]:
        print(f"  [{event.severity}] {event.event_type} from {event.emitter}")
    
    print("=" * 60 + "\n")

def stop_flywheel():
    """Send stop signal to running flywheel"""
    if not PID_FILE.exists():
        print("Flywheel is not running.")
        return
    
    with open(PID_FILE, 'r') as f:
        pid = int(f.read().strip())
    
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Stop signal sent to PID {pid}")
    except ProcessLookupError:
        print("Flywheel process not found. Cleaning up PID file.")
        PID_FILE.unlink()

# ============================================================================
# CLI: MAIN
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("""
Nuclear Brain Agent Manager
===========================

Usage:
    python agent_manager.py start           Start the flywheel
    python agent_manager.py stop            Stop the flywheel
    python agent_manager.py status          Show current status
    python agent_manager.py sprint "goal"   Start a new sprint

The Set-and-Forget Protocol:
    1. Founder: python agent_manager.py sprint "Build RAG memory layer"
    2. Founder: python agent_manager.py start
    3. ... system runs autonomously ...
    4. Founder reviews daily digest in .brain/artifacts/synthesis/

For CRITICAL events, the flywheel pauses and notifies you.
""")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        flywheel = FlywheelManager()
        flywheel.start()
    
    elif command == 'stop':
        stop_flywheel()
    
    elif command == 'status':
        show_status()
    
    elif command == 'sprint':
        if len(sys.argv) < 3:
            print("Error: Please provide a sprint goal")
            print('Usage: python agent_manager.py sprint "Your goal here"')
            return
        goal = " ".join(sys.argv[2:])
        start_sprint(goal)
    
    elif command == 'resume':
        print("Resuming flywheel after CRITICAL event review...")
        emit_event(
            emitter="founder",
            event_type="founder_decision_made",
            severity="NOTABLE",
            payload={"action": "resume_flywheel"}
        )
        # Start the flywheel
        flywheel = FlywheelManager()
        flywheel.start()
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: start, stop, status, sprint, resume")

if __name__ == "__main__":
    main()
