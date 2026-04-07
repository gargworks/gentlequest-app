"""
Tests for Phase 14: Resource Quarantine & Path Confinement
"""

import pytest
import os
import tempfile
from pathlib import Path
try:
    from mcp_server_nucleus.hypervisor.locker import Locker
    from mcp_server_nucleus.hypervisor.injector import Injector
    from mcp_server_nucleus.hypervisor.watchdog import Watchdog
    from mcp_server_nucleus.runtime.auth.ipc_provider import IPCAuthProvider
    from mcp_server_nucleus.runtime.common import assert_path_in_workspace
except ImportError as e:
    pytest.skip(f"Quarantine dependencies not available: {e}", allow_module_level=True)

def resolve_test_path(path: str) -> str:
    """Resolve symlinks (e.g., /var -> /private/var) to avoid pathlib.relative_to failures."""
    return str(Path(path).resolve())

def test_path_confinement_logic():
    with tempfile.TemporaryDirectory() as tmpdir:
        ws_str = resolve_test_path(tmpdir)
        ws = Path(ws_str)
        
        # Valid path
        valid = ws / "test.txt"
        assert assert_path_in_workspace(str(valid), workspace_root=ws_str) == valid
        
        # Invalid path (Escape)
        invalid = ws.parent / "escape.txt"
        with pytest.raises(PermissionError) as exc:
            assert_path_in_workspace(str(invalid), workspace_root=ws_str)
        assert "WORKSPACE ESCAPE BLOCKED" in str(exc.value)

def test_locker_confinement():
    locker = Locker()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Resolve path to avoid /var vs /private/var mismatch on macOS
        tmpdir = resolve_test_path(tmpdir)
        os.environ["NUCLEUS_BRAIN_PATH"] = tmpdir
        
        inside = Path(tmpdir) / "inside.txt"
        inside.write_text("safe")
        
        # Should work
        assert locker.lock(str(inside))
        locker.unlock(str(inside), secret=locker._internal_secret)
        
        # Outside should fail
        outside = Path(tmpdir).parent / "outside.txt"
        with pytest.raises(PermissionError):
            locker.lock(str(outside))

def test_watchdog_lru_eviction():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Resolve path to avoid /var vs /private/var mismatch on macOS
        tmpdir = resolve_test_path(tmpdir)
        # Ensure the 'brain' for this test is the tmpdir so default validation passes
        os.environ["NUCLEUS_BRAIN_PATH"] = tmpdir
        # Small cache for testing
        wd = Watchdog(workspace_root=tmpdir, max_cache_size=2)
        
        # Create 3 files
        f1 = Path(tmpdir) / "f1.txt"
        f2 = Path(tmpdir) / "f2.txt"
        f3 = Path(tmpdir) / "f3.txt"
        
        f1.write_text("1")
        f2.write_text("2")
        f3.write_text("3")
        
        wd.protect("f1.txt")
        wd.protect("f2.txt")
        
        assert len(wd.shadow_cache) == 2
        assert str(f1.resolve()) in wd.shadow_cache
        
        # Protect f3, should evict f1 (LRU)
        wd.protect("f3.txt")
        assert len(wd.shadow_cache) == 2
        assert str(f1.resolve()) not in wd.shadow_cache
        assert str(f3.resolve()) in wd.shadow_cache

def test_token_auto_cleanup():
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = IPCAuthProvider(brain_path=Path(tmpdir))
        
        # Create 101 expired tokens
        for i in range(101):
            tid = f"ipc-old-{i}"
            from mcp_server_nucleus.runtime.auth.ipc_provider import IPCToken
            from datetime import datetime, timezone, timedelta
            expires = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
            token = IPCToken(
                token_id=tid, 
                created_at=expires, 
                expires_at=expires, 
                scope="read"
            )
            provider._active_tokens[tid] = token
            
        assert len(provider._active_tokens) == 101
        
        # Issue a new token, should trigger cleanup
        provider.issue_token(scope="write")
        
        # Should have cleaned up all expired, leaving only the 1 new one
        assert len(provider._active_tokens) == 1
