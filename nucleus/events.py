"""
Nucleus Event Ledger
====================
Append-only event log for brain activity.
"""

import json
import uuid
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

BRAIN_ROOT = Path(os.getenv("NUCLEUS_BRAIN_PATH", ".brain"))
EVENTS_FILE = BRAIN_ROOT / "ledger" / "events.jsonl"

def emit_event(
    emitter: str,
    event_type: str,
    payload: Dict[str, Any],
    severity: str = "NOTABLE"
) -> str:
    """
    Emit an event to the brain ledger.
    
    Args:
        emitter: Agent or source name
        event_type: Type of event
        payload: Event data
        severity: ROUTINE, NOTABLE, or CRITICAL
        
    Returns:
        Event ID
    """
    event_id = str(uuid.uuid4())[:8]
    
    event = {
        "event_id": event_id,
        "timestamp": datetime.now().isoformat(),
        "emitter": emitter,
        "event_type": event_type,
        "severity": severity,
        "payload": payload
    }
    
    try:
        EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(EVENTS_FILE, "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        print(f"Event write error: {e}")
    
    return event_id

def get_events(limit: int = 10, event_type: Optional[str] = None) -> List[Dict]:
    """
    Get recent events from the ledger.
    
    Args:
        limit: Max events to return
        event_type: Optional filter by type
        
    Returns:
        List of events (most recent first)
    """
    try:
        if not EVENTS_FILE.exists():
            return []
        
        events = []
        with open(EVENTS_FILE) as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        
        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]
        
        return list(reversed(events[-limit:]))
    except Exception as e:
        print(f"Event read error: {e}")
        return []
