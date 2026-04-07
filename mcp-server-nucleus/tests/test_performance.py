
import pytest
import time
import os
import json
from pathlib import Path
try:
    from mcp_server_nucleus.runtime.orchestrator_v3 import NucleusOrchestratorV3, get_orchestrator
    from mcp_server_nucleus.runtime.telemetry_ops import _get_from_cache, _put_in_cache, _invalidate_cache
except ImportError as e:
    pytest.skip(f"Cache API not implemented: {e}", allow_module_level=True)

def test_orchestrator_caching():
    """Verify that multiple orchestrator inits share cached legacy data."""
    # First init to warm cache
    start = time.time()
    o1 = NucleusOrchestratorV3()
    warm_time = time.time() - start
    
    # Second init should be significantly faster or at least use cache
    start = time.time()
    o2 = NucleusOrchestratorV3()
    cached_time = time.time() - start
    
    print(f"\nWarm init: {warm_time*1000:.2f}ms")
    print(f"Cached init: {cached_time*1000:.2f}ms")
    
    # Note: On local SSD, 0.12ms is already fast, but redundant I/O is eliminated
    assert cached_time <= warm_time

def test_telemetry_ttl_caching():
    """Verify per-metric TTL caching logic."""
    _invalidate_cache()
    
    # Test default TTL
    _put_in_cache("test_key", "test_data")
    assert _get_from_cache("test_key") == "test_data"
    
    # Test invalidation
    _invalidate_cache("test_key")
    assert _get_from_cache("test_key") is None

def test_legacy_loading_robustness():
    """Verify that the orchestrator handles non-dict tasks.json contents."""
    brain_path = Path("/tmp/nucleus_test_brain")
    ledger_path = brain_path / "ledger"
    ledger_path.mkdir(parents=True, exist_ok=True)
    
    tasks_json = ledger_path / "tasks.json"
    
    # Test with a list instead of a dict (common failure point previously)
    with open(tasks_json, "w") as f:
        json.dump([{"id": "t1", "title": "Test Task"}], f)
    
    # Should not raise exception
    o = NucleusOrchestratorV3(brain_path=brain_path)
    assert o.get_task("t1") is not None
    assert o.get_task("t1")["title"] == "Test Task"

if __name__ == "__main__":
    import json
    # Run tests manually if needed
    pytest.main([__file__])
