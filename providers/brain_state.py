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
from models import db


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
    Initialize brain state tables. Call during app startup.
    Returns True if successful.
    """
    try:
        # Create brain_state table (singleton row pattern)
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS brain_state (
                id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
                state_data JSONB NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create brain_events table for event log
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS brain_events (
                id SERIAL PRIMARY KEY,
                event_id VARCHAR(36) NOT NULL,
                event_type VARCHAR(100) NOT NULL,
                emitter VARCHAR(50) NOT NULL,
                severity VARCHAR(20) DEFAULT 'NOTABLE',
                payload JSONB,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create index for event queries
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS brain_events_type_idx ON brain_events (event_type)
        """))
        
        db.session.commit()
        return True
        
    except Exception as e:
        print(f"Brain tables init error: {e}")
        db.session.rollback()
        return False


def get_brain_state() -> Dict[str, Any]:
    """
    Get current brain state from database.
    Returns default state if not initialized.
    """
    try:
        result = db.session.execute(text(
            "SELECT state_data FROM brain_state WHERE id = 1"
        )).fetchone()
        
        if result and result[0]:
            return result[0]
        
        # Initialize with defaults if empty
        _init_default_state()
        return DEFAULT_STATE.copy()
        
    except Exception as e:
        print(f"Get brain state error: {e}")
        db.session.rollback()
        return DEFAULT_STATE.copy()


def _init_default_state():
    """Insert default state if table is empty."""
    try:
        db.session.execute(
            text("""
                INSERT INTO brain_state (id, state_data, last_updated)
                VALUES (1, :state, CURRENT_TIMESTAMP)
                ON CONFLICT (id) DO NOTHING
            """),
            {"state": json.dumps(DEFAULT_STATE)}
        )
        db.session.commit()
    except Exception:
        db.session.rollback()


def set_brain_state(updates: Dict[str, Any]) -> bool:
    """
    Update brain state with new values (shallow merge).
    
    Args:
        updates: Dictionary of fields to update
        
    Returns:
        True if successful
    """
    try:
        current = get_brain_state()
        
        # Shallow merge updates
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(current.get(key), dict):
                current[key].update(value)
            else:
                current[key] = value
        
        db.session.execute(
            text("""
                INSERT INTO brain_state (id, state_data, last_updated)
                VALUES (1, :state, CURRENT_TIMESTAMP)
                ON CONFLICT (id) DO UPDATE SET 
                    state_data = :state,
                    last_updated = CURRENT_TIMESTAMP
            """),
            {"state": json.dumps(current)}
        )
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
    
    Args:
        emitter: Agent or source name
        event_type: Type of event
        payload: Event data
        severity: ROUTINE, NOTABLE, or CRITICAL
        metadata: Optional additional metadata
        
    Returns:
        Event ID
    """
    import uuid
    event_id = str(uuid.uuid4())[:8]
    
    try:
        db.session.execute(
            text("""
                INSERT INTO brain_events 
                (event_id, event_type, emitter, severity, payload, metadata)
                VALUES (:id, :type, :emitter, :severity, :payload, :metadata)
            """),
            {
                "id": event_id,
                "type": event_type,
                "emitter": emitter,
                "severity": severity,
                "payload": json.dumps(payload) if payload else None,
                "metadata": json.dumps(metadata) if metadata else None
            }
        )
        
        # Increment event counter
        _increment_event_counter()
        
        db.session.commit()
        return event_id
        
    except Exception as e:
        print(f"Emit brain event error: {e}")
        db.session.rollback()
        return event_id  # Return ID even on failure


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
    
    Args:
        count: Number of events to return
        
    Returns:
        List of event dictionaries
    """
    try:
        results = db.session.execute(
            text("""
                SELECT event_id, event_type, emitter, severity, payload, metadata, created_at
                FROM brain_events
                ORDER BY created_at DESC
                LIMIT :count
            """),
            {"count": count}
        ).fetchall()
        
        events = []
        for row in results:
            events.append({
                "event_id": row[0],
                "event_type": row[1],
                "emitter": row[2],
                "severity": row[3],
                "payload": row[4] if row[4] else {},
                "metadata": row[5] if row[5] else {},
                "timestamp": row[6].isoformat() if row[6] else None
            })
        
        return events
        
    except Exception as e:
        print(f"Get recent events error: {e}")
        return []
