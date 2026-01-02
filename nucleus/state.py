"""
Nucleus State Management
========================
Database-backed state with file fallback.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Determine storage mode
USE_DB = os.getenv("NUCLEUS_USE_DB", "false").lower() == "true"
BRAIN_ROOT = Path(os.getenv("NUCLEUS_BRAIN_PATH", ".brain"))
STATE_FILE = BRAIN_ROOT / "ledger" / "state.json"

DEFAULT_STATE = {
    "current_sprint": {"name": "No Sprint", "status": "IDLE"},
    "counters": {"total_events": 0, "tasks_completed": 0},
    "active_agents": [],
    "last_updated": None
}

def get_state(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get current brain state.
    
    Args:
        path: Optional dot-notation path (e.g., "current_sprint.name")
        
    Returns:
        Full state dict or value at path
    """
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                state = json.load(f)
        else:
            state = DEFAULT_STATE.copy()
        
        if path:
            for key in path.split("."):
                state = state.get(key, {})
            return state
        
        return state
    except Exception as e:
        print(f"State read error: {e}")
        return DEFAULT_STATE.copy()

def set_state(updates: Dict[str, Any]) -> bool:
    """
    Update brain state with shallow merge.
    
    Args:
        updates: Dictionary of fields to update
        
    Returns:
        True if successful
    """
    try:
        state = get_state()
        
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(state.get(key), dict):
                state[key].update(value)
            else:
                state[key] = value
        
        state["last_updated"] = datetime.now().isoformat()
        
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        
        return True
    except Exception as e:
        print(f"State write error: {e}")
        return False
