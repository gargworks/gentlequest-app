#!/usr/bin/env python3
"""
Seed script for Demo B: Engram Recall.
Writes a high-intensity architectural decision to the persistent ledger.
"""
import os
import sys
import json
import time
from pathlib import Path

# Setup Path
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server-nucleus" / "src"))

def seed_engram():
    brain_path = Path("/Users/lokeshgarg/ai-mvp-backend/output/demos/.brain")
    engram_path = brain_path / "engrams" / "ledger.jsonl"
    events_path = brain_path / "ledger" / "events.jsonl"
    audit_path = brain_path / "ledger" / "interaction_log.jsonl"
    
    for p in [engram_path, events_path, audit_path]:
        p.parent.mkdir(parents=True, exist_ok=True)
    
    import hashlib
    from datetime import datetime, timezone
    
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    engrams = [
        {
            "key": "sync_protocol",
            "value": "Use WebSockets (via Socket.io) for real-time synchronization in the AI Buddy app to ensure sub-100ms latency.",
            "context": "Architecture",
            "intensity": 8,
            "timestamp": timestamp,
            "signature": "Architect_Agent"
        },
        {
            "key": "database_preference",
            "value": "PostgreSQL with pgvector for efficient similarity search in long-term AI memory.",
            "context": "Decision",
            "intensity": 9,
            "timestamp": timestamp,
            "signature": "Architect_Agent"
        }
    ]
    
    # Write Engrams
    with open(engram_path, "w") as f:
        for engram in engrams:
            f.write(json.dumps(engram) + "\n")

    # Write Events and Audit Logs
    with open(events_path, "w") as fe, open(audit_path, "w") as fa:
        for engram in engrams:
            event_id = f"evt-{int(time.time())}-{engram['key'][:4]}"
            data = {"key": engram["key"], "value": engram["value"]}
            
            # Event
            event = {
                "event_id": event_id,
                "timestamp": timestamp,
                "type": "engram_written",
                "emitter": "Architect_Agent",
                "data": data,
                "description": f"Committed {engram['key']} to long-term memory."
            }
            fe.write(json.dumps(event) + "\n")
            
            # Audit (Interaction Hash)
            payload = json.dumps({"type": "engram_written", "emitter": "Architect_Agent", "data": data}, sort_keys=True)
            h = hashlib.sha256(payload.encode()).hexdigest()
            audit = {
                "timestamp": timestamp,
                "emitter": "Architect_Agent",
                "type": "engram_written",
                "hash": h,
                "alg": "sha256"
            }
            fa.write(json.dumps(audit) + "\n")

    print(f"✅ Engrams seeded at {engram_path}")
    print(f"✅ Audit records seeded at {audit_path}")

if __name__ == "__main__":
    seed_engram()
