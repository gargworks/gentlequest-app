
import sys
import os
import json
import time
from datetime import datetime
from unittest.mock import MagicMock
from pathlib import Path
import tempfile
import shutil

# Setup paths
src_path = os.path.abspath("mcp-server-nucleus/src")
sys.path.append(src_path)

# Mock fastmcp
sys.modules["fastmcp"] = MagicMock()

# Import after mocks
from mcp_server_nucleus import _emit_event
from mcp_server_nucleus.runtime.event_stream import emit_event

def test_timestamps():
    # Setup temp brain
    temp_dir = tempfile.mkdtemp()
    try:
        brain_path = Path(temp_dir)
        os.environ["NUCLEAR_BRAIN_PATH"] = str(brain_path)
        
        # Test 1: _emit_event (Core Logic)
        _emit_event("test_event_core", "tester", {"foo": "bar"})
        
        # Test 2: emit_event (Runtime Stream)
        emit_event(brain_path, "test_event_stream", "tester", {"foo": "baz"})
        
        # Verify
        events_path = brain_path / "ledger" / "events.jsonl"
        with open(events_path, "r") as f:
            lines = f.readlines()
            
        print(f"DEBUG: Found {len(lines)} events")
        
        for line in lines:
            event = json.loads(line)
            ts = event.get("timestamp", "")
            print(f"Event {event['event_type']} timestamp: {ts}")
            
            if not ts.endswith("Z"):
                raise ValueError(f"Timestamp {ts} does not end with Z")
            
            # Verify ISO format basics (parseable)
            # Python 3.11+ handles Z, older might need replacing Z with +00:00
            try:
                # Basic check: YYYY-MM-DD
                if "T" not in ts:
                    raise ValueError("Missing T separator")
            except Exception as e:
                raise ValueError(f"Invalid format: {e}")
                
        print("✅ Timestamps Verified")
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    try:
        test_timestamps()
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)
