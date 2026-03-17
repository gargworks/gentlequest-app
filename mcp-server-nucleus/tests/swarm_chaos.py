"""
Swarm Chaos Test (Phase 6 Hardening Proof)
==========================================
Verifies that the FederationEngine correctly handles partitions by:
1. Disabling Class A operations when in MINORITY/ISOLATED status.
2. Rejecting consensus proposals during split-brain.
3. Automatically recovering Class A when majority is restored.
"""

import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from mcp_server_nucleus.runtime.federation import (
    create_federation_engine,
    PeerStatus,
    FederationPeer,
    PartitionStatus
)
from mcp_server_nucleus.runtime.depth_ops import _depth_show, _depth_reset

async def run_chaos_test():
    print("🐝 Starting Swarm Chaos Test...")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        brain_path = Path(tmp_dir)
        (brain_path / "ledger").mkdir()
        (brain_path / "session").mkdir()
        
        # 1. Initialize Engine
        engine = create_federation_engine(
            brain_id="chaos_node_1",
            brain_path=brain_path
        )
        await engine.start()
        
        # 2. Setup a 3-node cluster simulation
        engine.state.peers["p2"] = FederationPeer("p2", "localhost:9001", "us")
        engine.state.peers["p3"] = FederationPeer("p3", "localhost:9002", "us")
        engine.state.peers["p2"].status = PeerStatus.ONLINE
        engine.state.peers["p3"].status = PeerStatus.ONLINE
        
        # Initial state should be NORMAL
        status = engine.recovery.check_partition_status()
        print(f"Status (Normal): {status.name}")
        assert status == PartitionStatus.NORMAL
        assert engine.state.class_a_enabled is True
        
        # 3. Simulate Partition (Isolate self)
        print("⚔️ Simulating partition (Isolating chaos_node_1)...")
        await engine.recovery.handle_peer_failure("p2")
        await engine.recovery.handle_peer_failure("p3")
        
        status = engine.recovery.check_partition_status()
        print(f"Status (Partition): {status.name}")
        assert status == PartitionStatus.ISOLATED
        assert engine.state.class_a_enabled is False
        
        # 4. Verify Proposal Rejection
        print("🛑 Verifying proposal rejection during partition...")
        # Force self to be leader for a moment to test proposal
        engine.consensus.raft_state = engine.consensus.raft_state.LEADER
        success = await engine.consensus.propose({"action": "CRITICAL_STATE_CHANGE"})
        
        print(f"Proposal success: {success}")
        assert success is False, "CRITICAL: Proposal should have been rejected during partition!"
        
        # 5. Simulate Healing
        print("🩹 Simulating healing (Restoring majority)...")
        await engine.recovery.handle_peer_recovery("p2")
        
        status = engine.recovery.check_partition_status()
        print(f"Status (Healed): {status.name}")
        assert status == PartitionStatus.MAJORITY
        assert engine.state.class_a_enabled is True
        
        # 6. Verify Proposal Acceptance
        print("✅ Verifying proposal acceptance after healing...")
        success = await engine.consensus.propose({"action": "NORMAL_OPERATION"})
        assert success is True
        
        await engine.stop()
        print("🏁 Swarm Chaos Test PASSED.")

async def run_depth_hard_test():
    print("\n🕵️ Starting Deep Agency Hardening Test...")
    from mcp_server_nucleus.runtime.orchestrator_v3 import get_orchestrator
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        brain_path = Path(tmp_dir)
        (brain_path / "ledger").mkdir()
        (brain_path / "session").mkdir()
        
        # Mock depth reset
        _depth_reset()
        
        orchestrator = get_orchestrator()
        orchestrator.brain_path = brain_path
        
        # 1. Create a deep task
        print("🔨 Creating deep task...")
        import os
        os.environ["NUCLEUS_AGENT_DEPTH"] = "1"
        result = orchestrator.add_task("Deep sub-task")
        task_id = result["task"]["id"]
        
        # Verify depth recorded
        task = orchestrator.get_task(task_id)
        assert task["dependency_metadata"]["depth"] == 1
        
        # 2. Complete task and verify auto-pop
        print("完成 task and verifying auto-pop...")
        # Push mock depth first to simulate being in the depth
        from mcp_server_nucleus.runtime.depth_ops import _depth_push
        _depth_push("Deep sub-task")
        
        before = _depth_show()["current_depth"]
        print(f"Depth before completion: {before}")
        assert before == 1
        
        orchestrator.complete_task(task_id, "test_agent")
        
        after = _depth_show()["current_depth"]
        print(f"Depth after completion: {after}")
        assert after == 0
        
        print("🏁 Deep Agency Hardening Test PASSED.")

if __name__ == "__main__":
    asyncio.run(run_chaos_test())
    asyncio.run(run_depth_hard_test())
