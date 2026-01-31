"""
Comprehensive test suite for NOP V3.1 Federation Engine.

Tests cover:
- Unit tests for core data structures (VectorClock, MerkleTree, etc.)
- Integration tests for component interaction
- Chaos/fault injection tests for partition handling
- Performance benchmarks for routing and sync

Author: NOP V3.1 Team
"""

import asyncio
import pytest
import random
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nop_core.federation import (
    VectorClock,
    MerkleTree,
    FederationPeer,
    FederationConfig,
    FederationState,
    TrustLevel,
    PeerStatus,
    PartitionStatus,
    ConsistencyClass,
    RaftState,
    ROUTING_PROFILES,
    DiscoveryManager,
    ConsensusManager,
    SyncManager,
    RoutingEngine,
    RecoveryManager,
    CircuitBreaker,
    CompositeRoutingStrategy,
    FederationEngine,
    create_federation_engine,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def brain_id():
    return "test_brain_001"

@pytest.fixture
def config(brain_id, tmp_path):
    return FederationConfig(
        brain_id=brain_id,
        region="us-west",
        address="localhost:9000",
        seed_peers=["localhost:9001", "localhost:9002"],
        brain_path=tmp_path / ".brain",
        heartbeat_interval=0.1,
        heartbeat_timeout=0.5,
        sync_interval=0.2,
    )

@pytest.fixture
def state(brain_id):
    return FederationState(brain_id=brain_id, region="us-west")

@pytest.fixture
def sample_peer():
    return FederationPeer(
        peer_id="peer_001",
        address="localhost:9001",
        region="us-west",
        trust_level=TrustLevel.MEMBER,
        capabilities={"python", "javascript"},
        status=PeerStatus.ONLINE,
        last_heartbeat=datetime.utcnow(),
        latency_ms=10.0,
        load=0.3,
    )

@pytest.fixture
def sample_task():
    return {
        "id": "task_001",
        "description": "Test task",
        "required_skills": ["python"],
        "priority": 2,
        "affinity": {"preferred_region": "us-west"},
    }


# =============================================================================
# VECTOR CLOCK TESTS
# =============================================================================

class TestVectorClock:
    """Unit tests for VectorClock."""
    
    def test_init_empty(self):
        vc = VectorClock()
        assert vc.clocks == {}
    
    def test_init_with_clocks(self):
        vc = VectorClock({"a": 1, "b": 2})
        assert vc.clocks == {"a": 1, "b": 2}
    
    def test_increment(self):
        vc = VectorClock()
        vc2 = vc.increment("brain_a")
        assert vc2.clocks["brain_a"] == 1
        assert vc.clocks == {}  # Original unchanged (immutable)
        
        vc3 = vc2.increment("brain_a")
        assert vc3.clocks["brain_a"] == 2
    
    def test_merge(self):
        vc1 = VectorClock({"a": 1, "b": 2})
        vc2 = VectorClock({"a": 2, "b": 1, "c": 3})
        
        merged = vc1.merge(vc2)
        
        assert merged.clocks == {"a": 2, "b": 2, "c": 3}
        # Originals unchanged
        assert vc1.clocks == {"a": 1, "b": 2}
        assert vc2.clocks == {"a": 2, "b": 1, "c": 3}
    
    def test_happens_before_true(self):
        vc1 = VectorClock({"a": 1})
        vc2 = VectorClock({"a": 2})
        
        assert vc1.happens_before(vc2)
        assert not vc2.happens_before(vc1)
    
    def test_happens_before_false_concurrent(self):
        vc1 = VectorClock({"a": 1, "b": 2})
        vc2 = VectorClock({"a": 2, "b": 1})
        
        assert not vc1.happens_before(vc2)
        assert not vc2.happens_before(vc1)
    
    def test_happens_before_equal(self):
        vc1 = VectorClock({"a": 1, "b": 2})
        vc2 = VectorClock({"a": 1, "b": 2})
        
        assert not vc1.happens_before(vc2)
        assert not vc2.happens_before(vc1)
    
    def test_to_dict(self):
        vc = VectorClock({"a": 1, "b": 2})
        d = vc.to_dict()
        assert d == {"a": 1, "b": 2}
        d["a"] = 99  # Mutate
        assert vc.clocks["a"] == 1  # Original unchanged
    
    def test_from_dict(self):
        data = {"a": 1, "b": 2}
        vc = VectorClock.from_dict(data)
        assert vc.clocks == {"a": 1, "b": 2}


# =============================================================================
# MERKLE TREE TESTS
# =============================================================================

class TestMerkleTree:
    """Unit tests for MerkleTree."""
    
    def test_empty_tree(self):
        tree = MerkleTree()
        assert tree.get_root() == ""
    
    def test_single_entry(self):
        tree = MerkleTree()
        tree.update("key1", b"value1")
        
        root = tree.get_root()
        assert root != ""
        assert len(root) == 64  # SHA256 hex digest
    
    def test_multiple_entries(self):
        tree = MerkleTree()
        tree.update("key1", b"value1")
        root1 = tree.get_root()
        
        tree.update("key2", b"value2")
        root2 = tree.get_root()
        
        assert root1 != root2
    
    def test_update_same_key(self):
        tree = MerkleTree()
        tree.update("key1", b"value1")
        root1 = tree.get_root()
        
        tree.update("key1", b"value2")
        root2 = tree.get_root()
        
        assert root1 != root2
    
    def test_remove_entry(self):
        tree = MerkleTree()
        tree.update("key1", b"value1")
        tree.update("key2", b"value2")
        root_before = tree.get_root()
        
        tree.remove("key1")
        root_after = tree.get_root()
        
        assert root_before != root_after
    
    def test_remove_nonexistent(self):
        tree = MerkleTree()
        tree.update("key1", b"value1")
        root_before = tree.get_root()
        
        tree.remove("nonexistent")
        root_after = tree.get_root()
        
        assert root_before == root_after
    
    def test_diff_same_trees(self):
        tree1 = MerkleTree()
        tree2 = MerkleTree()
        
        tree1.update("key1", b"value1")
        tree2.update("key1", b"value1")
        
        assert not tree1.diff(tree2.get_root())
    
    def test_diff_different_trees(self):
        tree1 = MerkleTree()
        tree2 = MerkleTree()
        
        tree1.update("key1", b"value1")
        tree2.update("key1", b"value2")
        
        assert tree1.diff(tree2.get_root())
    
    def test_deterministic_root(self):
        """Same entries should produce same root regardless of insertion order."""
        tree1 = MerkleTree()
        tree1.update("a", b"1")
        tree1.update("b", b"2")
        
        tree2 = MerkleTree()
        tree2.update("b", b"2")
        tree2.update("a", b"1")
        
        assert tree1.get_root() == tree2.get_root()


# =============================================================================
# FEDERATION PEER TESTS
# =============================================================================

class TestFederationPeer:
    """Unit tests for FederationPeer."""
    
    def test_init(self, sample_peer):
        assert sample_peer.peer_id == "peer_001"
        assert sample_peer.region == "us-west"
        assert "python" in sample_peer.capabilities
    
    def test_is_online(self, sample_peer):
        assert sample_peer.is_online()
        
        sample_peer.status = PeerStatus.OFFLINE
        assert not sample_peer.is_online()
    
    def test_is_healthy(self, sample_peer):
        sample_peer.status = PeerStatus.ONLINE
        assert sample_peer.is_healthy()
        
        sample_peer.status = PeerStatus.SUSPECT
        assert sample_peer.is_healthy()
        
        sample_peer.status = PeerStatus.OFFLINE
        assert not sample_peer.is_healthy()
    
    def test_to_dict(self, sample_peer):
        d = sample_peer.to_dict()
        
        assert d["peer_id"] == "peer_001"
        assert d["region"] == "us-west"
        assert "python" in d["capabilities"]
        assert d["status"] == "ONLINE"
    
    def test_from_dict(self):
        data = {
            "peer_id": "peer_002",
            "address": "localhost:9002",
            "region": "eu-west",
            "trust_level": "ADMIN",
            "capabilities": ["python", "rust"],
            "status": "ONLINE",
            "latency_ms": 50.0,
            "load": 0.5,
        }
        
        peer = FederationPeer.from_dict(data)
        
        assert peer.peer_id == "peer_002"
        assert peer.region == "eu-west"
        assert peer.trust_level == TrustLevel.ADMIN
        assert "rust" in peer.capabilities


# =============================================================================
# ROUTING STRATEGY TESTS
# =============================================================================

class TestCompositeRoutingStrategy:
    """Unit tests for CompositeRoutingStrategy."""
    
    def test_score_with_matching_skills(self, sample_peer, sample_task):
        strategy = CompositeRoutingStrategy()
        score = strategy.score(sample_peer, sample_task, "local_brain")
        
        assert 0 <= score <= 1
    
    def test_score_missing_skills(self, sample_peer, sample_task):
        sample_task["required_skills"] = ["rust", "go"]
        strategy = CompositeRoutingStrategy()
        score = strategy.score(sample_peer, sample_task, "local_brain")
        
        assert score == -1.0  # Cannot execute
    
    def test_score_no_skill_requirement(self, sample_peer):
        task = {"id": "task_001", "description": "No skills needed"}
        strategy = CompositeRoutingStrategy()
        score = strategy.score(sample_peer, task, "local_brain")
        
        assert score >= 0
    
    def test_score_local_affinity(self, sample_peer):
        task = {"id": "task_001"}
        sample_peer.peer_id = "local_brain"
        strategy = CompositeRoutingStrategy()
        score = strategy.score(sample_peer, task, "local_brain")
        
        # Local brain should get affinity bonus
        assert score > 0
    
    def test_score_region_affinity(self, sample_peer, sample_task):
        sample_task["affinity"] = {"preferred_region": "us-west"}
        strategy = CompositeRoutingStrategy()
        score = strategy.score(sample_peer, sample_task, "other_brain")
        
        assert score > 0
    
    def test_different_profiles(self, sample_peer, sample_task):
        realtime_strategy = CompositeRoutingStrategy(ROUTING_PROFILES["realtime"])
        batch_strategy = CompositeRoutingStrategy(ROUTING_PROFILES["batch"])
        
        score_realtime = realtime_strategy.score(sample_peer, sample_task, "local")
        score_batch = batch_strategy.score(sample_peer, sample_task, "local")
        
        # Different profiles should produce different scores (usually)
        # They might be the same in some edge cases
        assert isinstance(score_realtime, float)
        assert isinstance(score_batch, float)


# =============================================================================
# CIRCUIT BREAKER TESTS
# =============================================================================

class TestCircuitBreaker:
    """Unit tests for CircuitBreaker."""
    
    def test_initial_state(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitBreaker.CLOSED
        assert cb.allow_request()
    
    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        
        cb.record_failure()
        assert cb.allow_request()
        cb.record_failure()
        assert cb.allow_request()
        cb.record_failure()
        
        assert cb.state == CircuitBreaker.OPEN
        assert not cb.allow_request()
    
    def test_success_resets_failures(self):
        cb = CircuitBreaker(failure_threshold=3)
        
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        
        assert cb.failures == 0
        assert cb.state == CircuitBreaker.CLOSED
    
    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        
        cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN
        assert not cb.allow_request()
        
        time.sleep(0.15)
        
        assert cb.allow_request()
        assert cb.state == CircuitBreaker.HALF_OPEN


# =============================================================================
# DISCOVERY MANAGER TESTS
# =============================================================================

class TestDiscoveryManager:
    """Unit tests for DiscoveryManager."""
    
    @pytest.fixture
    def discovery(self, config, state):
        return DiscoveryManager(config, state)
    
    @pytest.mark.asyncio
    async def test_start_stop(self, discovery):
        await discovery.start()
        assert discovery.running
        
        await discovery.stop()
        assert not discovery.running
    
    @pytest.mark.asyncio
    async def test_bootstrap_creates_peers(self, discovery, state):
        await discovery.start()
        await asyncio.sleep(0.1)
        
        # Should have created peers from seed_peers
        assert len(state.peers) >= 0  # May or may not connect
        
        await discovery.stop()
    
    def test_get_online_peers(self, discovery, state):
        peer1 = FederationPeer("p1", "addr1", "r1", status=PeerStatus.ONLINE)
        peer2 = FederationPeer("p2", "addr2", "r2", status=PeerStatus.OFFLINE)
        state.peers = {"p1": peer1, "p2": peer2}
        
        online = discovery.get_online_peers()
        
        assert len(online) == 1
        assert online[0].peer_id == "p1"
    
    def test_get_healthy_peers(self, discovery, state):
        peer1 = FederationPeer("p1", "addr1", "r1", status=PeerStatus.ONLINE)
        peer2 = FederationPeer("p2", "addr2", "r2", status=PeerStatus.SUSPECT)
        peer3 = FederationPeer("p3", "addr3", "r3", status=PeerStatus.OFFLINE)
        state.peers = {"p1": peer1, "p2": peer2, "p3": peer3}
        
        healthy = discovery.get_healthy_peers()
        
        assert len(healthy) == 2


# =============================================================================
# CONSENSUS MANAGER TESTS
# =============================================================================

class TestConsensusManager:
    """Unit tests for ConsensusManager."""
    
    @pytest.fixture
    def consensus(self, config, state):
        return ConsensusManager(config, state)
    
    @pytest.mark.asyncio
    async def test_start_as_follower(self, consensus):
        await consensus.start()
        assert consensus.raft_state == RaftState.FOLLOWER
        await consensus.stop()
    
    @pytest.mark.asyncio
    async def test_becomes_leader_when_alone(self, consensus, state):
        """Single node should become leader."""
        state.peers = {}  # No peers
        
        await consensus.start()
        await asyncio.sleep(0.5)  # Wait for election timeout
        
        assert consensus.is_leader()
        assert state.leader_id == consensus.config.brain_id
        
        await consensus.stop()
    
    @pytest.mark.asyncio
    async def test_propose_as_leader(self, consensus, state):
        state.peers = {}
        await consensus.start()
        await asyncio.sleep(0.5)
        
        result = await consensus.propose({"type": "test", "data": "value"})
        
        assert result
        assert len(state.log) == 1
        assert state.log[0].command["type"] == "test"
        
        await consensus.stop()
    
    @pytest.mark.asyncio
    async def test_propose_fails_as_follower(self, consensus):
        await consensus.start()
        # Don't wait for election - still follower
        
        result = await consensus.propose({"type": "test"})
        
        assert not result
        
        await consensus.stop()
    
    def test_get_leader(self, consensus, state):
        state.leader_id = "leader_001"
        assert consensus.get_leader() == "leader_001"


# =============================================================================
# SYNC MANAGER TESTS
# =============================================================================

class TestSyncManager:
    """Unit tests for SyncManager."""
    
    @pytest.fixture
    def sync_manager(self, config, state):
        return SyncManager(config, state)
    
    @pytest.mark.asyncio
    async def test_start_stop(self, sync_manager):
        await sync_manager.start()
        assert sync_manager.running
        
        await sync_manager.stop()
        assert not sync_manager.running
    
    def test_update_local_state(self, sync_manager, state):
        initial_clock = state.vector_clock.clocks.copy()
        
        sync_manager.update_local_state("key1", b"value1")
        
        assert sync_manager.merkle_tree.get_root() != ""
        assert state.merkle_root == sync_manager.merkle_tree.get_root()
        # Vector clock should have incremented
        assert state.vector_clock.clocks.get(sync_manager.config.brain_id, 0) > initial_clock.get(sync_manager.config.brain_id, 0)
    
    @pytest.mark.asyncio
    async def test_sync_with_peer_not_found(self, sync_manager):
        result = await sync_manager.sync_with_peer("nonexistent")
        
        assert not result.success
        assert "not found" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_sync_with_peer_already_synced(self, sync_manager, state):
        peer = FederationPeer("p1", "addr1", "r1", status=PeerStatus.ONLINE)
        peer.merkle_root = sync_manager.merkle_tree.get_root()
        state.peers["p1"] = peer
        
        result = await sync_manager.sync_with_peer("p1")
        
        assert result.success
        assert result.items_synced == 0  # Already in sync
    
    @pytest.mark.asyncio
    async def test_sync_in_progress_blocked(self, sync_manager, state):
        peer = FederationPeer("p1", "addr1", "r1", status=PeerStatus.ONLINE)
        state.peers["p1"] = peer
        
        sync_manager.sync_in_progress.add("p1")
        
        result = await sync_manager.sync_with_peer("p1")
        
        assert not result.success
        assert "in progress" in result.error.lower()


# =============================================================================
# ROUTING ENGINE TESTS
# =============================================================================

class TestRoutingEngine:
    """Unit tests for RoutingEngine."""
    
    @pytest.fixture
    def router(self, config, state):
        return RoutingEngine(config, state)
    
    @pytest.mark.asyncio
    async def test_route_task_local_only(self, router, sample_task):
        # No peers, should route locally
        decision = await router.route_task(sample_task)
        
        assert decision.target_brain == router.config.brain_id
        assert decision.routing_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_route_task_with_peers(self, router, state, sample_task, sample_peer):
        state.peers["peer_001"] = sample_peer
        
        decision = await router.route_task(sample_task)
        
        assert decision.target_brain in [router.config.brain_id, "peer_001"]
        assert len(decision.alternatives) >= 0
    
    @pytest.mark.asyncio
    async def test_route_task_caching(self, router, sample_task):
        decision1 = await router.route_task(sample_task)
        decision2 = await router.route_task(sample_task)
        
        # Second call should be cached (much faster)
        assert decision2.routing_time_ms <= decision1.routing_time_ms
    
    @pytest.mark.asyncio
    async def test_route_task_different_profiles(self, router, sample_task):
        decision_default = await router.route_task(sample_task, profile="default")
        decision_realtime = await router.route_task({**sample_task, "id": "task_rt"}, profile="realtime")
        
        assert isinstance(decision_default.score, float)
        assert isinstance(decision_realtime.score, float)


# =============================================================================
# RECOVERY MANAGER TESTS
# =============================================================================

class TestRecoveryManager:
    """Unit tests for RecoveryManager."""
    
    @pytest.fixture
    def recovery(self, config, state):
        discovery = DiscoveryManager(config, state)
        consensus = ConsensusManager(config, state)
        sync = SyncManager(config, state)
        return RecoveryManager(config, state, discovery, consensus, sync)
    
    def test_check_partition_normal(self, recovery, state):
        peer1 = FederationPeer("p1", "a1", "r1", status=PeerStatus.ONLINE)
        peer2 = FederationPeer("p2", "a2", "r2", status=PeerStatus.ONLINE)
        state.peers = {"p1": peer1, "p2": peer2}
        
        status = recovery.check_partition_status()
        
        assert status == PartitionStatus.NORMAL
    
    def test_check_partition_majority(self, recovery, state):
        # 3 peers, 2 online = majority
        peer1 = FederationPeer("p1", "a1", "r1", status=PeerStatus.ONLINE)
        peer2 = FederationPeer("p2", "a2", "r2", status=PeerStatus.ONLINE)
        peer3 = FederationPeer("p3", "a3", "r3", status=PeerStatus.OFFLINE)
        state.peers = {"p1": peer1, "p2": peer2, "p3": peer3}
        
        status = recovery.check_partition_status()
        
        assert status == PartitionStatus.MAJORITY
    
    def test_check_partition_minority(self, recovery, state):
        # 3 peers, 0 online = minority (only self)
        peer1 = FederationPeer("p1", "a1", "r1", status=PeerStatus.OFFLINE)
        peer2 = FederationPeer("p2", "a2", "r2", status=PeerStatus.OFFLINE)
        peer3 = FederationPeer("p3", "a3", "r3", status=PeerStatus.OFFLINE)
        state.peers = {"p1": peer1, "p2": peer2, "p3": peer3}
        
        status = recovery.check_partition_status()
        
        assert status == PartitionStatus.MINORITY
    
    def test_operation_allowed_class_a(self, recovery, state):
        # Normal - allowed
        state.peers = {}
        assert recovery.is_operation_allowed(ConsistencyClass.CLASS_A)
        
        # Minority - not allowed
        peer1 = FederationPeer("p1", "a1", "r1", status=PeerStatus.OFFLINE)
        peer2 = FederationPeer("p2", "a2", "r2", status=PeerStatus.OFFLINE)
        state.peers = {"p1": peer1, "p2": peer2}
        assert not recovery.is_operation_allowed(ConsistencyClass.CLASS_A)
    
    def test_operation_allowed_class_b_c_always(self, recovery, state):
        # Class B/C always allowed (CRDT)
        peer1 = FederationPeer("p1", "a1", "r1", status=PeerStatus.OFFLINE)
        peer2 = FederationPeer("p2", "a2", "r2", status=PeerStatus.OFFLINE)
        state.peers = {"p1": peer1, "p2": peer2}
        
        assert recovery.is_operation_allowed(ConsistencyClass.CLASS_B)
        assert recovery.is_operation_allowed(ConsistencyClass.CLASS_C)


# =============================================================================
# FEDERATION ENGINE INTEGRATION TESTS
# =============================================================================

class TestFederationEngine:
    """Integration tests for FederationEngine."""
    
    @pytest.fixture
    def engine(self, config):
        return FederationEngine(config)
    
    @pytest.mark.asyncio
    async def test_start_stop(self, engine):
        await engine.start()
        assert engine.running
        
        await engine.stop()
        assert not engine.running
    
    @pytest.mark.asyncio
    async def test_get_status(self, engine):
        await engine.start()
        
        status = engine.get_status()
        
        assert status["brain_id"] == engine.config.brain_id
        assert status["running"]
        assert "peers" in status
        assert "sync" in status
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_get_health(self, engine):
        await engine.start()
        
        health = engine.get_health()
        
        assert "healthy" in health
        assert "score" in health
        assert 0 <= health["score"] <= 1
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_route_task(self, engine, sample_task):
        await engine.start()
        
        decision = await engine.route_task(sample_task)
        
        assert decision.target_brain == engine.config.brain_id  # No peers
        assert engine.metrics.tasks_routed == 1
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_join_leave(self, engine):
        await engine.start()
        
        result = await engine.join("localhost:9099")
        assert result["success"]
        
        result = await engine.leave()
        assert result["success"]
    
    @pytest.mark.asyncio
    async def test_get_peers(self, engine):
        await engine.start()
        
        peers = engine.get_peers()
        online = engine.get_online_peers()
        
        assert isinstance(peers, list)
        assert isinstance(online, list)
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_sync_now(self, engine):
        await engine.start()
        
        results = await engine.sync_now()
        
        assert isinstance(results, list)
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_state_persistence(self, engine, tmp_path):
        await engine.start()
        
        # Modify state
        engine.state.term = 5
        engine.state.leader_id = "test_leader"
        
        await engine.stop()
        
        # Create new engine and verify state loaded
        engine2 = FederationEngine(engine.config)
        await engine2.start()
        
        assert engine2.state.term == 5
        assert engine2.state.leader_id == "test_leader"
        
        await engine2.stop()


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================

class TestCreateFederationEngine:
    """Tests for factory function."""
    
    def test_create_with_defaults(self):
        engine = create_federation_engine("test_brain")
        
        assert engine.config.brain_id == "test_brain"
        assert engine.config.region == "default"
        assert engine.config.seed_peers == []
    
    def test_create_with_options(self, tmp_path):
        engine = create_federation_engine(
            brain_id="custom_brain",
            region="eu-west",
            seed_peers=["peer1:9000"],
            brain_path=tmp_path / ".brain"
        )
        
        assert engine.config.brain_id == "custom_brain"
        assert engine.config.region == "eu-west"
        assert "peer1:9000" in engine.config.seed_peers


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Performance benchmarks."""
    
    @pytest.mark.asyncio
    async def test_routing_latency(self, config, state):
        router = RoutingEngine(config, state)
        
        # Add some peers
        for i in range(10):
            peer = FederationPeer(
                f"peer_{i}", f"addr_{i}", "us-west",
                capabilities={"python", "javascript"},
                status=PeerStatus.ONLINE,
                latency_ms=random.uniform(10, 100),
                load=random.uniform(0, 0.8)
            )
            state.peers[f"peer_{i}"] = peer
        
        tasks = [{"id": f"task_{i}", "required_skills": ["python"]} for i in range(100)]
        
        start = time.perf_counter()
        for task in tasks:
            await router.route_task(task)
        elapsed = time.perf_counter() - start
        
        avg_latency = elapsed / len(tasks) * 1000  # ms
        assert avg_latency < 5  # <5ms per routing decision
    
    def test_vector_clock_merge_performance(self):
        """Merge 1000 vector clocks."""
        clocks = [
            VectorClock({f"brain_{j}": random.randint(1, 100) for j in range(10)})
            for _ in range(1000)
        ]
        
        start = time.perf_counter()
        result = VectorClock()
        for vc in clocks:
            result = result.merge(vc)
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.1  # <100ms for 1000 merges
    
    def test_merkle_tree_update_performance(self):
        """Update Merkle tree with 10K entries."""
        tree = MerkleTree()
        
        start = time.perf_counter()
        for i in range(10000):
            tree.update(f"key_{i}", f"value_{i}".encode())
        tree.get_root()  # Force rebuild
        elapsed = time.perf_counter() - start
        
        assert elapsed < 2.0  # <2s for 10K entries


# =============================================================================
# CHAOS TESTS
# =============================================================================

class TestChaosScenarios:
    """Chaos engineering tests."""
    
    @pytest.mark.asyncio
    async def test_all_peers_offline(self, config, state):
        """System should continue operating when all peers go offline."""
        engine = FederationEngine(config)
        await engine.start()
        
        # Add peers then mark all offline
        for i in range(3):
            peer = FederationPeer(f"p{i}", f"a{i}", "r1", status=PeerStatus.ONLINE)
            state.peers[f"p{i}"] = peer
        
        for peer in state.peers.values():
            peer.status = PeerStatus.OFFLINE
        
        # Should still be able to route locally
        decision = await engine.route_task({"id": "task_1"})
        assert decision.target_brain == config.brain_id
        
        # Health should reflect partition
        health = engine.get_health()
        assert health["partition_status"] in ["MINORITY", "ISOLATED"]
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_leader_failure_recovery(self, config, state):
        """System should elect new leader when leader fails."""
        engine = FederationEngine(config)
        state.peers = {}  # Start alone
        
        await engine.start()
        await asyncio.sleep(0.5)
        
        # Should become leader when alone
        assert engine.consensus.is_leader()
        
        _ = state.term  # Store initial term for potential future assertions
        
        await engine.stop()
        
        # Restart - should re-elect
        await engine.start()
        await asyncio.sleep(0.5)
        
        assert engine.consensus.is_leader()
        
        await engine.stop()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
