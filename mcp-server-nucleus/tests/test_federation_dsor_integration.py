import pytest
import os
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone
import asyncio

try:
    from mcp_server_nucleus.runtime.federation import (
        FederationEngine,
        FederationConfig,
        FederationPeer,
        TrustLevel,
        PeerStatus
    )
    from mcp_server_nucleus.runtime.dsor import DecisionLedger
    from mcp_server_nucleus.runtime.event_stream import EventTypes
except (ImportError, AttributeError):
    pytest.skip("Federation DSOR integration components not available", allow_module_level=True)

# Verify FederationEngine has record_decision (sovereign behavior)
import tempfile as _tf, inspect as _ins
_sig = _ins.signature(FederationConfig)
if 'peers' in _sig.parameters:
    # Sovereign build with peers param
    pass
else:
    # Public build — check if record_decision exists
    _bp = Path(_tf.mkdtemp()) / ".brain"
    _bp.mkdir(); (_bp / "ledger").mkdir(); (_bp / "federation").mkdir()
    _cfg = FederationConfig(brain_id="skip-test", brain_path=_bp)
    _fe = FederationEngine(_cfg)
    if not hasattr(_fe, 'record_decision'):
        pytest.skip("FederationEngine missing record_decision (sovereign build)", allow_module_level=True)

@pytest.fixture
def temp_brain(tmp_path):
    brain_path = tmp_path / ".brain"
    brain_path.mkdir()
    (brain_path / "ledger").mkdir()
    (brain_path / "federation").mkdir()
    return brain_path

@pytest.mark.asyncio
async def test_federation_dsor_recording(temp_brain):
    # 1. Setup Federation Engine with temp brain
    config = FederationConfig(
        brain_id="test-brain-1",
        brain_path=temp_brain,
        address="localhost:5001",
        region="us-east"
    )
    engine = FederationEngine(config)
    
    # 2. Simulate Peer Joined
    peer = FederationPeer(
        peer_id="remote-brain-2",
        address="localhost:5002",
        region="us-west",
        trust_level=TrustLevel.MEMBER,
        status=PeerStatus.ONLINE
    )
    engine._on_peer_joined(peer)
    
    # 3. Simulate Leader Election
    engine._on_leader_change("remote-brain-2")
    
    # 4. Simulate Task Routing
    task = {"task_id": "task-123", "type": "research"}
    await engine.route_task(task)
    
    # 5. Verify DSoR Ledger entries
    decisions_path = temp_brain / "ledger" / "decisions" / "decisions.jsonl"
    assert decisions_path.exists()
    
    decisions = []
    with open(decisions_path, 'r') as f:
        for line in f:
            decisions.append(json.loads(line))
            
    # Verify entries exist for the events
    event_types = [d["metadata"]["event_type"] for d in decisions]
    assert EventTypes.FEDERATION_PEER_JOINED in event_types
    assert EventTypes.FEDERATION_LEADER_ELECTED in event_types
    assert EventTypes.FEDERATION_TASK_ROUTED in event_types
    
    # Verify specific decision details
    routing_decision = next(d for d in decisions if d["metadata"]["event_type"] == EventTypes.FEDERATION_TASK_ROUTED)
    assert routing_decision["metadata"]["task_id"] == "task-123"
    assert "Route task" in routing_decision["intent"]
    
    print("\n✅ DSoR integration tests passed: Decisions recorded for Join, Election, and Routing.")

if __name__ == "__main__":
    # For manual running
    import sys
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        asyncio.run(test_federation_dsor_recording(Path(tmpdir)))
