
import os
import sys
from pathlib import Path

# Set env var BEFORE importing module
os.environ["NUCLEAR_BRAIN_PATH"] = "/Users/lokeshgarg/dogfood-brain/.brain"

# Add source to path so we can import
sys.path.append("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")

try:
    from mcp_server_nucleus import _get_state, get_brain_path
    
    print(f"Testing with BRAIN_PATH: {get_brain_path()}")
    
    # Test 1: Check if path exists
    path = get_brain_path()
    print(f"Path exists: {path.exists()}")
    print(f"Ledger exists: {(path / 'ledger').exists()}")
    print(f"State file exists: {(path / 'ledger' / 'state.json').exists()}")
    
    # Test 2: validation of state file content
    import json
    with open(path / 'ledger' / 'state.json', 'r') as f:
        content = f.read()
        print(f"State file content length: {len(content)}")
        try:
             json.loads(content)
             print("State file is valid JSON")
        except json.JSONDecodeError as e:
             print(f"State file JSON error: {e}")

    # Test 3: Run _get_state
    print("Running _get_state()...")
    state = _get_state()
    print("State returned successfully:")
    print(json.dumps(state, indent=2))
    
except Exception as e:
    print(f"CRITICAL FAILURE: {e}")
    import traceback
    traceback.print_exc()
