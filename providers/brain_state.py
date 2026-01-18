"""
Brain State Provider
====================
Database-backed state management for the Nuclear Brain system.
Enables production functionality without requiring .brain/ directory.

Usage:
    from providers.brain_state import get_brain_state, set_brain_state, emit_brain_event
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy import text
from models import db, BrainState, BrainEvent


# Default state structure
DEFAULT_STATE = {
    "current_sprint": {
        "id": "none",
        "name": "No Sprint",
        "status": "INACTIVE",
        "focus": "Start a sprint with /sprint <goal>",
        "objectives": [],
        "tasks": []
    },
    "active_agents": ["synthesizer"],
    "counters": {
        "total_events": 0,
        "tasks_completed": 0
    },
    "top_3_leverage_actions": [
        {"action": "Start a sprint", "agent": "founder", "impact": "Focus work"}
    ],
    "founder_queue": [],
    "pending_events": []
}


def init_brain_tables() -> bool:
    """
    Deprecated: Brain tables are now managed via ORM and db.create_all().
    """
    return True


def get_brain_state() -> Dict[str, Any]:
    """
    Get current brain state from database.
    Returns default state if not initialized.
    """
    try:
        state = BrainState.query.filter_by(id=1).first()
        
        if state and state.state_data:
            return state.state_data
        
        # Initialize with defaults if empty
        _init_default_state()
        return DEFAULT_STATE.copy()
        
    except Exception as e:
        print(f"Get brain state error: {e}")
        return DEFAULT_STATE.copy()


def _init_default_state():
    """Insert default state if table is empty."""
    try:
        state = BrainState(id=1, state_data=DEFAULT_STATE.copy())
        db.session.add(state)
        db.session.commit()
    except Exception:
        db.session.rollback()


def set_brain_state(updates: Dict[str, Any]) -> bool:
    """
    Update brain state with new values (shallow merge).
    """
    try:
        state = BrainState.query.filter_by(id=1).first()
        
        if not state:
            state = BrainState(id=1, state_data=DEFAULT_STATE.copy())
            db.session.add(state)
            # Must commit to ensure it exists for subsequent queries if necessary
            db.session.commit() 
            state = BrainState.query.get(1)
        
        # Create a deep copy to ensure SQLAlchemy detects the change
        current = json.loads(json.dumps(state.state_data)) if state.state_data else DEFAULT_STATE.copy()
        
        # Shallow merge updates
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(current.get(key), dict):
                current[key].update(value)
            else:
                current[key] = value
        
        state.state_data = current
        state.last_updated = datetime.utcnow()
        
        db.session.commit()
        return True
        
    except Exception as e:
        print(f"Set brain state error: {e}")
        db.session.rollback()
        return False


def emit_brain_event(
    emitter: str,
    event_type: str,
    payload: Dict[str, Any],
    severity: str = "NOTABLE",
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Emit an event to the brain event log.
    """
    import uuid
    event_id = str(uuid.uuid4())[:8]
    
    try:
        event = BrainEvent(
            event_id=event_id,
            event_type=event_type,
            emitter=emitter,
            severity=severity,
            payload=payload,
            event_metadata=metadata
        )
        db.session.add(event)
        
        # Increment event counter
        _increment_event_counter()
        
        db.session.commit()
        return event_id
        
    except Exception as e:
        print(f"Emit brain event error: {e}")
        db.session.rollback()
        return event_id


def _increment_event_counter():
    """Increment the total event counter in state."""
    try:
        state = get_brain_state()
        counters = state.get("counters", {})
        counters["total_events"] = counters.get("total_events", 0) + 1
        set_brain_state({"counters": counters})
    except Exception:
        pass


def get_recent_brain_events(count: int = 10) -> List[Dict[str, Any]]:
    """
    Get most recent events from the log.
    """
    try:
        results = BrainEvent.query.order_by(BrainEvent.created_at.desc()).limit(count).all()
        
        events = []
        for event in results:
            events.append({
                "event_id": event.event_id,
                "event_type": event.event_type,
                "emitter": event.emitter,
                "severity": event.severity,
                "payload": event.payload or {},
                "metadata": event.event_metadata or {},
                "timestamp": event.created_at.isoformat() if event.created_at else None
            })
        
        return events
        
    except Exception as e:
        print(f"Get recent events error: {e}")
        return []
