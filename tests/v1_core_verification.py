
import sys
import os
import json
import time
from pathlib import Path

# Add src to path
sys.path.append('mcp-server-nucleus/src')

try:
    import mcp_server_nucleus
    from mcp_server_nucleus.runtime.agent import DecisionMade, ActionRequested
    # Import internal impl functions directly for verification
    from mcp_server_nucleus import (
        _import_tasks_from_jsonl, 
        _brain_request_handoff_impl, 
        _brain_get_handoffs_impl, 
        _brain_check_protocol_impl, 
        _brain_session_start_impl
    )
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def test_engram_ledger():
    print("\n--- Testing Engram Ledger ---")
    dm = DecisionMade(decision_id="dec_001", reasoning="Test reasoning", context_hash="abc123hash")
    print(f"✅ DecisionMade instantiated: {dm.decision_id}")
    
    ar = ActionRequested(action_id="act_001", decision_id="dec_001", tool_name="test_tool", args={"a": 1})
    print(f"✅ ActionRequested instantiated: {ar.action_id} linked to {ar.decision_id}")

def test_task_import():
    print("\n--- Testing Task Import ---")
    brain_path = Path(os.environ.get("NUCLEAR_BRAIN_PATH", ".brain"))
    import_file = brain_path / "test_import.jsonl"
    import_file.parent.mkdir(parents=True, exist_ok=True)
    
    tasks = [
        {"id": "gtm_001", "description": "GTM Task", "priority": 1, "environment": "antigravity", "model": "gemini-2.0-flash"},
        {"description": "Standard Task", "priority": 3}
    ]
    
    with open(import_file, "w") as f:
        for t in tasks:
            f.write(json.dumps(t) + "\n")
            
    res = _import_tasks_from_jsonl(str(import_file))
    print(f"✅ Import result: {res}")
    
    # Verify in session_start
    session_report = _brain_session_start_impl()
    print("✅ Session start report generated")
    if "TARGET MODEL: gemini-2.0-flash" in session_report:
        print("✅ Model Routing verified in report")
    else:
        print("❌ Model Routing NOT found in report")

def test_mou_protocols():
    print("\n--- Testing MoU Protocols ---")
    # Test Protocol check
    protocol_res = _brain_check_protocol_impl("agent_001")
    print(f"✅ Protocol check: {protocol_res[:50]}...")
    
    # Test Handoff
    handoff_res = _brain_request_handoff_impl(to_agent="researcher", mission_context="Deep dive into X", task_id="gtm_001")
    print(f"✅ Handoff request: {handoff_res}")
    
    # Test Handoff retrieval
    pending_res = _brain_get_handoffs_impl("researcher")
    pending = json.loads(pending_res)
    print(f"✅ Found {len(pending)} pending handoffs for researcher")
    if len(pending) > 0:
        print(f"✅ Handoff metadata: {pending[0]['mission']}")

def test_trust_signal():
    print("\n--- Testing Trust Signal ---")
    brain_path = Path(os.environ.get("NUCLEAR_BRAIN_PATH", ".brain"))
    log_path = brain_path / "ledger" / "interaction_log.jsonl"
    
    if log_path.exists():
        size_before = log_path.stat().st_size
    else:
        size_before = 0
        
    # Trigger an event
    from mcp_server_nucleus.runtime.event_ops import _emit_event
    _emit_event("test_trust_event", "verifier", {"status": "ok"})
    
    if log_path.exists() and log_path.stat().st_size > size_before:
        print("✅ Trust signal (interaction_log.jsonl) updated")
        with open(log_path, "r") as f:
            last_line = f.readlines()[-1]
            print(f"✅ Last log hash: {json.loads(last_line)['hash'][:12]}...")
    else:
        print("❌ Trust signal NOT updated")

if __name__ == "__main__":
    # Ensure env is set for testing
    os.environ["NUCLEAR_BRAIN_PATH"] = "/Users/lokeshgarg/ai-mvp-backend/.brain"
    
    test_engram_ledger()
    test_task_import()
    test_mou_protocols()
    test_trust_signal()
    print("\n✨ ALL V1 CORE VERIFICATIONS COMPLETED ✨")
