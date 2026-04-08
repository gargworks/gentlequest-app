import sys
import os
from pathlib import Path
import json
import time
import pytest

# Add src and parent to path
project_root = Path(__file__).resolve().parent.parent # mcp-server-nucleus/
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root.parent)) # ai-mvp-backend/

try:
    from mcp_server_nucleus.runtime.auth.signature_guard import get_signature_guard
    from mcp_server_nucleus.runtime.auth.ipc_provider import get_ipc_auth_manager
    # Verify get_ipc_auth_manager accepts brain_path positional arg
    import inspect as _ins
    _sig = _ins.signature(get_ipc_auth_manager)
    if len(_sig.parameters) == 0:
        pytest.skip("get_ipc_auth_manager signature changed (no brain_path param)", allow_module_level=True)
except (ImportError, AttributeError):
    pytest.skip("Phase 16 security components not available", allow_module_level=True)

def test_signature_compatibility():
    print("Testing Signature Compatibility...")
    guard = get_signature_guard(project_root / ".brain")
    manager = get_ipc_auth_manager(project_root / ".brain")
    
    # Debug: Check secrets
    secret_path = project_root / ".brain" / "secrets" / ".ipc_secret"
    if secret_path.exists():
        print(f"Secret exists at: {secret_path}")
        print(f"Secret prefix: {secret_path.read_bytes()[:4].hex()}...")
    else:
        print(f"Secret NOT FOUND at: {secret_path}")

    # Test 1: Dict signing compatibility
    payload = {"token_id": "test-123", "scope": "admin", "decision_id": "none"}
    sig_from_guard = guard.sign_dict(payload)
    print(f"Guard Signature: {sig_from_guard}")
    
    # Issue a token and check its signature
    token = manager.issue_token(scope="admin", decision_id="none")
    # manager uses sign_dict(payload) internally now
    # We need to extract the payload that manager used
    manager_payload = {"token_id": token.token_id, "scope": "admin", "decision_id": "none"}
    sig_from_manager = token.signature
    print(f"Manager Issued Token ID: {token.token_id}")
    print(f"Manager Signature: {sig_from_manager}")
    
    # Verify manager's token using guard
    valid = guard.verify_dict(manager_payload, sig_from_manager)
    print(f"Token signature valid via Guard: {valid}")
    if not valid:
        # Check if re-signing manager_payload with guard matches
        expected = guard.sign_dict(manager_payload)
        print(f"Guard Expected for Manager Payload: {expected}")
        
    assert valid, "Manager signature should be verifiable by Guard"
    
    # Test 2: Validation delegation
    is_valid, msg = manager.validate_token(token.token_id, required_scope="admin")
    print(f"Manager Validation Result: {is_valid} ({msg})")
    assert is_valid, f"Manager should validate its own issued token: {msg}"
    
    print("✅ Signature Compatibility Verified.\n")

def test_coordinator_handshake():
    print("Testing Coordinator Handshake (Mock)...")
    # Simulate NucleusSecurityManager refresh
    from nucleus.agents.coordinator import NucleusSecurityManager
    sec = NucleusSecurityManager(project_root / ".brain")
    
    headers = sec.get_headers()
    print(f"Generated Headers: {headers}")
    assert "x-nucleus-token" in headers
    assert headers["x-nucleus-agent-tier"] == "T2"
    
    token_id = headers["x-nucleus-token"]
    manager = get_ipc_auth_manager()
    is_valid, msg = manager.validate_token(token_id, required_scope="admin")
    print(f"Handshake Token Validation: {is_valid} ({msg})")
    assert is_valid, "Coordinator handshake token should be valid for admin scope"
    
    print("✅ Coordinator Handshake Verified.\n")

if __name__ == "__main__":
    try:
        test_signature_compatibility()
        test_coordinator_handshake()
        print("🚀 ALL PHASE 16 SECURITY TESTS PASSED")
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
