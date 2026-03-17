
import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from mcp_server_nucleus.runtime.federation import (
    create_federation_engine,
    FederationPeer,
    PeerStatus,
    PartitionStatus,
)

@pytest.mark.asyncio
async def test_governance_vote_lifecycle():
    """Test the full lifecycle of a governance vote."""
    # Use a temporary directory for brain path
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = create_federation_engine(
            brain_id="alpha_brain",
            brain_path=Path(tmp_dir)
        )
        
        # 1. Setup peers to simulate a multi-brain environment
        peer_b = FederationPeer(peer_id="beta_brain", address="localhost:9001", region="us")
        peer_b.status = PeerStatus.ONLINE
        peer_b.last_heartbeat = datetime.now(timezone.utc)
        
        peer_c = FederationPeer(peer_id="gamma_brain", address="localhost:9002", region="us")
        peer_c.status = PeerStatus.ONLINE
        peer_c.last_heartbeat = datetime.now(timezone.utc)
        
        engine.state.peers["beta_brain"] = peer_b
        engine.state.peers["gamma_brain"] = peer_c
        
        assert engine.is_sovereign_mode() is True
        
        # 2. Initiate a vote
        tool_call = {"name": "nucleus_governance", "action": "delete_file", "params": {"path": "test.txt"}}
        vote_id = engine.initiate_vote(tool_call)
        
        assert vote_id.startswith("vote_")
        assert vote_id in engine.consensus.pending_votes
        
        # 3. Check initial tally (should be 1/3: initiator auto-approves)
        vote = engine.consensus.pending_votes[vote_id]
        assert len(vote.approvals) == 1
        assert engine.check_consensus(vote_id) is False
        
        # 4. Cast another vote (now 2/3 - Majority achieved)
        success = engine.cast_vote(vote_id, "beta_brain", approve=True)
        assert success is True
        assert engine.check_consensus(vote_id) is True
        assert vote.status == "APPROVED"

@pytest.mark.asyncio
async def test_governance_vote_rejection():
    """Test that a vote can be rejected if it fails to reach majority."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = create_federation_engine(
            brain_id="alpha_brain",
            brain_path=Path(tmp_dir)
        )
        
        peer_b = FederationPeer(peer_id="beta_brain", address="localhost:9001", region="us")
        peer_b.status = PeerStatus.ONLINE
        engine.state.peers["beta_brain"] = peer_b
        
        # sovereign_mode is True (alpha + beta = 2 brains)
        # majority for 2 brains is (2//2)+1 = 2
        
        vote_id = engine.initiate_vote({"name": "test", "action": "action"})
        
        # Cast rejection
        engine.cast_vote(vote_id, "beta_brain", approve=False)
        
        assert engine.check_consensus(vote_id) is False
        assert "beta_brain" in engine.consensus.pending_votes[vote_id].rejections

@pytest.mark.asyncio
async def test_isolated_mode_bypass():
    """Test that governance consensus is NOT required in standalone/isolated mode."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = create_federation_engine(
            brain_id="standalone_brain",
            brain_path=Path(tmp_dir)
        )
        
        # No peers
        assert engine.is_sovereign_mode() is False
        
        # Add offline peers
        peer_b = FederationPeer(peer_id="beta_brain", address="localhost:9001", region="us")
        peer_b.status = PeerStatus.OFFLINE
        engine.state.peers["beta_brain"] = peer_b
        
        assert engine.is_sovereign_mode() is False
        
        # Simulate partition Isolation
        engine.state.partition_status = PartitionStatus.ISOLATED
        peer_b.status = PeerStatus.ONLINE # Even if online, if we are isolated, we operate solo
        
        assert engine.is_sovereign_mode() is False

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
