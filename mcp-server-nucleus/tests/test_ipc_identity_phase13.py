"""
Tests for Phase 13: Secured Watchdog Identity (IPC Hardening)
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path

try:
    from mcp_server_nucleus.runtime.auth.ipc_provider import IPCAuthProvider, get_ipc_auth_manager
    from mcp_server_nucleus.hypervisor.locker import Locker
    from mcp_server_nucleus.runtime.hypervisor_ops import _locker, unlock_resource_impl
    # Verify IPCToken has agent_tier (sovereign attribute)
    _p = IPCAuthProvider(brain_path=Path(tempfile.mkdtemp()))
    _t = _p.issue_token(scope="test")
    if not hasattr(_t, 'agent_tier'):
        pytest.skip("IPCToken missing agent_tier attribute (sovereign build)", allow_module_level=True)
except (ImportError, AttributeError, TypeError):
    pytest.skip("IPC identity components not available", allow_module_level=True)

def test_ipc_token_identity_and_tier():
    with tempfile.TemporaryDirectory() as tmpdir:
        brain_path = Path(tmpdir)
        provider = IPCAuthProvider(brain_path=brain_path)
        
        # Issue a T3 token
        token = provider.issue_token(scope="admin", agent_tier="T3")
        
        assert token.agent_tier == "T3"
        # In tests, the parent of the process running pytest might vary, 
        # but issuer and validator are in the same OS process tree.
        assert token.caller_pid == os.getppid() 
        
        # Validate correctly
        is_valid, msg = provider.validate_token(token.token_id, scope="admin", required_tier="T3")
        assert is_valid is True
        
        # Validate with higher tier than token (should fail)
        token_t1 = provider.issue_token(scope="read", agent_tier="T1")
        is_valid, msg = provider.validate_token(token_t1.token_id, scope="read", required_tier="T3")
        assert is_valid is False
        assert "Tier mismatch" in msg

def test_secret_gated_unlock():
    locker = Locker()
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = f.name
    
    try:
        locker.lock(path)
        assert locker.is_locked(path)
        
        # Unlock with wrong secret
        success = locker.unlock(path, secret="wrong")
        assert success is False
        assert locker.is_locked(path)
        
        # Unlock with correct secret
        success = locker.unlock(path, secret=locker._internal_secret)
        assert success is True
        assert not locker.is_locked(path)
    finally:
        if os.path.exists(path):
            locker.unlock(path, secret=locker._internal_secret)
            os.unlink(path)

def test_hypervisor_ops_gate(monkeypatch):
    # This tests the integration in hypervisor_ops.py
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("NUCLEAR_BRAIN_PATH", tmpdir)
        from mcp_server_nucleus.runtime.auth.ipc_provider import get_ipc_auth_manager
        manager = get_ipc_auth_manager()
        
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("secure")
        
        _locker.lock(str(test_file))
        assert _locker.is_locked(str(test_file))
        
        # 1. Attempt unlock without token
        res = unlock_resource_impl(str(test_file))
        assert "UNLOCK DENIED" in res
        assert "token_id required" in res
        
        # 2. Attempt unlock with T1 token
        token_t1 = manager.issue_token(scope="nucleus_governance:unlock", agent_tier="T1")
        res = unlock_resource_impl(str(test_file), token_id=token_t1.token_id)
        assert "UNLOCK DENIED" in res
        assert "Tier mismatch" in res
        
        # 3. Attempt unlock with T3 token
        token_t3 = manager.issue_token(scope="nucleus_governance:unlock", agent_tier="T3")
        res = unlock_resource_impl(str(test_file), token_id=token_t3.token_id)
        assert "🔓 UNLOCKED" in res
        assert not _locker.is_locked(str(test_file))
