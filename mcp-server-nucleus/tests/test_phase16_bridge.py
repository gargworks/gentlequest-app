import sys
import os
from pathlib import Path
import json
import time
import subprocess

# Add src and parent to path
project_root = Path(__file__).resolve().parent.parent # mcp-server-nucleus/
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root.parent)) # ai-mvp-backend/

from mcp_server_nucleus.runtime.auth.signature_guard import get_signature_guard
from mcp_server_nucleus.runtime.auth.ipc_provider import get_ipc_auth_manager

def test_bridge_enforcement():
    print("Testing Bridge Enforcement (Zero Shortcut)...")
    brain_path = project_root / ".brain"
    bridge_path = brain_path / "session" / "bridge.task"
    bridge_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Test Insecure/Old-style Task (Plaintext)
    bridge_path.write_text("rm -rf / # insecure task", encoding="utf-8")
    
    from nucleus.agents.coordinator import TaskBridge
    bridge = TaskBridge(brain_path)
    
    task = bridge.read_task()
    print(f"Read Plaintext Task: {task}")
    assert task is None, "Plaintext task should be REJECTED in Phase 16"
    
    # 2. Test Malformed JSON
    bridge_path.write_text("{\"invalid\": \"json\"", encoding="utf-8")
    task = bridge.read_task()
    assert task is None, "Malformed JSON should be REJECTED"
    
    # 3. Test Invalid Signature
    payload = json.dumps({"task": "echo 'hack'", "signature": "bad-sig"})
    bridge_path.write_text(payload, encoding="utf-8")
    task = bridge.read_task()
    assert task is None, "Invalid signature should be REJECTED"
    
    # 4. Test Valid Signature
    guard = get_signature_guard(brain_path)
    task_text = "echo 'secure task'"
    sig = guard.sign_payload("bridge", task_text)
    payload = json.dumps({"task": task_text, "signature": sig})
    bridge_path.write_text(payload, encoding="utf-8")
    
    task = bridge.read_task()
    print(f"Read Signed Task: {task}")
    assert task == task_text, "Valid signed task should be ACCEPTED"
    
    print("✅ Bridge Enforcement Verified.\n")

if __name__ == "__main__":
    try:
        test_bridge_enforcement()
        print("🚀 BRIDGE SECURITY TESTS PASSED")
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
