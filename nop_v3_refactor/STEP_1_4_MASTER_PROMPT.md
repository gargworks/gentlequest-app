# 🎯 STEP 1.4: AgentPool - Master Prompt

**Date:** January 22, 2026, 11:00 PM IST  
**Status:** Ready to execute  
**Vision Alignment:** ✅ Locked to VISION_AND_NORTH_STAR.md

---

## 🌟 YOUR ROLE (Role Reversal Wisdom)

**You are Lokesh asking yourself:** "If I were the AI system building AgentPool correctly for scale, what would I need you to tell me right now?"

**Answer:** This prompt.

---

## 📋 CONTEXT (Building on CRDTTaskStore + TaskScheduler)

### Previous Wins
- ✅ **Step 1.2 CRDTTaskStore:** Zero data loss, 15K+ writes/sec, LWW + hybrid lamport
- ✅ **Step 1.3 TaskScheduler:** 423K tasks/sec, zero conflicts, tier matching, FIFO fairness
- ✅ **Track B Phase 1:** V3.1 schema complete with checkpoint/context_summary/dependency_metadata

### This Step (Step 1.4)
- Build **AgentPool:** Multi-agent orchestration layer
- Manages agent lifecycle (spawn, exhaust, respawn)
- Integrates with TaskScheduler for assignment
- Tracks reset cycles (Gemini 5h, Opus unlimited)
- Handles graceful exhaustion (checkpoint before shutdown)
- Auto-spawns replacement agents
- Supports 100 agents × 1000 tasks

---

## 🏗️ SCALE MATRIX (Non-Negotiable)

| Metric | 1 Agent | 10 Agents | 100 Agents | 1000 Agents |
|--------|---------|-----------|------------|-------------|
| **Tasks per Agent** | 100 | 100 | 100 | 100 |
| **Spawn Time** | <10ms | <50ms | <500ms | <5s |
| **Exhaust Handling** | <100ms | <100ms | <500ms | <5s |
| **Heartbeat Check** | <1ms | <5ms | <50ms | <500ms |
| **Pool Status** | <1ms | <5ms | <50ms | <500ms |
| **Memory** | <10MB | <50MB | <500MB | <5GB |

---

## 🎯 STEP 1.4 MISSION

**Build AgentPool** - A multi-agent orchestration layer that:

✅ Manages 1→100→1000 agents (same code, same API)  
✅ Tracks agent lifecycle (spawned, active, exhausted, offline)  
✅ Handles reset cycles (Gemini 5h, Opus unlimited)  
✅ Auto-checkpoints tasks before exhaustion  
✅ Gracefully handles agent failure (reassign tasks)  
✅ Auto-spawns replacement agents  
✅ Integrates with TaskScheduler for assignment  
✅ Provides real-time pool metrics  
✅ Supports tier-based agent allocation  
✅ Thread-safe for concurrent operations  
✅ Future-proof for distributed multi-node pools  
✅ Zero vendor lock-in  

---

## 🔧 IMPLEMENTATION CHOICES (Locked)

### Architecture: Agent Registry + Lifecycle State Machine

**Why:**
- Simple, deterministic lifecycle management
- Works for 1 agent → 1000 agents
- Exhaustion handling is explicit (checkpoint + reassign)
- Reset cycle tracking is time-based
- Compatible with future distributed pools

**Core Components:**

```
AgentPool
├── agent_registry: Dict[agent_id, Agent]
├── scheduler: TaskScheduler
├── tier_pools: Dict[tier, List[Agent]]
├── exhausted_agents: Dict[agent_id, ExhaustionRecord]
└── metrics: PoolMetrics

Agent Lifecycle State Machine:
  SPAWNING → AVAILABLE → BUSY → EXHAUSTED → RESPAWNING
      │                    │          │
      └─────── OFFLINE ◄───┴──────────┘

Key Operations:
1. spawn_agent(tier, model) → agent_id
2. exhaust_agent(agent_id, reason) → reassign tasks
3. respawn_agent(agent_id) → new capacity
4. get_pool_status() → metrics + health
5. find_available_agent(tier) → agent_id or None
```

### Data Model:

```python
Agent = {
    "id": str,
    "model": str,  # gemini_3_pro_high, claude_opus_4_5, etc.
    "tier": str,  # T1_PLANNING, T2_CODE, T3_REVIEW, T4_DEPLOY
    "status": "SPAWNING" | "AVAILABLE" | "BUSY" | "EXHAUSTED" | "OFFLINE",
    "capacity": int,
    "current_tasks": List[task_id],
    "reset_cycle": {
        "hours": int | None,
        "last_reset_at": timestamp,
        "next_reset_at": timestamp,
        "warning_threshold_minutes": int,
    },
    "exhaustion_history": List[ExhaustionRecord],
    "spawned_at": timestamp,
    "last_heartbeat": timestamp,
    "tasks_completed": int,
    "total_cost": float,
}

ExhaustionRecord = {
    "timestamp": timestamp,
    "reason": "reset_cycle" | "rate_limit" | "error" | "manual",
    "tasks_affected": List[task_id],
    "recovery_time_seconds": int,
    "was_graceful": bool,
}

PoolMetrics = {
    "total_agents": int,
    "by_status": Dict[status, int],
    "by_tier": Dict[tier, int],
    "active_tasks": int,
    "pending_tasks": int,
    "exhaustion_rate": float,
    "utilization": float,
}
```

---

## 📊 STRESS TEST REQUIREMENTS

**Test: 100 agents × 1000 tasks with exhaustion simulation**

```
setup_phase:
  - Create AgentPool with TaskScheduler
  - Spawn 100 agents: 25 T1, 25 T2, 25 T3, 25 T4
  - Set capacity: 10 tasks per agent
  - Set reset cycles: 50% have 1-hour cycle (simulated)
  - Add 1000 tasks to scheduler

execution_phase:
  - Assign all 1000 tasks
  - Simulate 10 exhaustion events (random agents)
  - Verify task reassignment
  - Simulate 5 respawn events

verify_phase:
  - Assert: All tasks eventually assigned or queued
  - Assert: No task lost during exhaustion
  - Assert: Exhausted agents have checkpoint records
  - Assert: Respawned agents are available
  - Assert: Pool metrics accurate
  - Assert: Tier distribution maintained

result:
  - ✅ PASSED: 1000 tasks, 100 agents, 10 exhaustions
  - ✅ PASSED: Zero task loss during exhaustion
  - ✅ PASSED: Graceful checkpointing before exhaust
  - ✅ PASSED: Auto-reassignment working
  - ✅ PASSED: Respawn restores capacity
  - ✅ PASSED: Pool metrics accurate
```

---

## 🎯 API SURFACE (Locked)

```python
class AgentPool:
    def __init__(
        self,
        scheduler: TaskScheduler,
        max_agents: int = 1000,
    ):
        """Initialize agent pool with scheduler reference."""
        pass
    
    def spawn_agent(
        self,
        agent_id: str,
        model: str,
        tier: str,
        capacity: int = 10,
        reset_cycle_hours: int = None,
    ) -> Dict:
        """
        Spawn new agent into pool.
        
        Args:
            agent_id: Unique identifier
            model: Model name (gemini_3_pro_high, etc.)
            tier: Task tier (T1_PLANNING, T2_CODE, etc.)
            capacity: Max concurrent tasks
            reset_cycle_hours: Hours until reset (None = unlimited)
            
        Returns:
            Agent dict with status
        """
        pass
    
    def exhaust_agent(
        self,
        agent_id: str,
        reason: str = "reset_cycle",
        graceful: bool = True,
    ) -> Dict:
        """
        Mark agent as exhausted, handle task reassignment.
        
        If graceful=True:
        1. Checkpoint all in-progress tasks
        2. Generate handoff summaries
        3. Reassign to available agents
        
        Returns:
            Exhaustion record with affected tasks
        """
        pass
    
    def respawn_agent(
        self,
        agent_id: str,
        new_capacity: int = None,
    ) -> Dict:
        """
        Respawn exhausted agent with fresh capacity.
        
        Returns:
            Updated agent dict
        """
        pass
    
    def get_available_agent(
        self,
        tier: str,
        min_capacity: int = 1,
    ) -> Optional[str]:
        """
        Find available agent for tier with minimum capacity.
        
        Returns:
            agent_id or None if no available agent
        """
        pass
    
    def assign_task(
        self,
        task_id: str,
        agent_id: str = None,
    ) -> Dict:
        """
        Assign task to specific agent or auto-select.
        
        Returns:
            Assignment result with agent_id
        """
        pass
    
    def complete_task(
        self,
        task_id: str,
        agent_id: str,
    ) -> Dict:
        """
        Mark task complete, update agent metrics.
        
        Returns:
            Completion result
        """
        pass
    
    def check_reset_warnings(self) -> List[Dict]:
        """
        Check all agents for approaching reset cycles.
        
        Returns:
            List of warning dicts for agents near reset
        """
        pass
    
    def get_pool_status(self) -> Dict:
        """
        Get comprehensive pool status and metrics.
        
        Returns:
            PoolMetrics dict
        """
        pass
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get single agent status."""
        pass
    
    def get_all_agents(self) -> List[Dict]:
        """Get all agents in pool."""
        pass
    
    def get_tier_agents(self, tier: str) -> List[Dict]:
        """Get agents for specific tier."""
        pass
    
    def heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat timestamp."""
        pass
    
    def cleanup_stale_agents(
        self,
        stale_threshold_seconds: int = 300,
    ) -> List[str]:
        """
        Mark agents without recent heartbeat as offline.
        
        Returns:
            List of agent_ids marked offline
        """
        pass
```

---

## 📁 FILES TO CREATE

### 1. `/nop_v3_refactor/nop_core/agent_pool.py`
**Full implementation** (~700 lines)
- Agent lifecycle management
- Reset cycle tracking
- Graceful exhaustion handling
- Task reassignment
- Pool metrics
- Thread-safe operations

### 2. `/nop_v3_refactor/tests/test_agent_pool.py`
**Stress test** (~500 lines)
- 100 agents × 1000 tasks
- Exhaustion simulation
- Respawn verification
- Metrics accuracy

### 3. `/nop_v3_refactor/STEP_1_4_CHECKLIST.md`
**5-line execution checklist**

---

## ✅ SUCCESS CRITERIA (Locked)

**Before proceeding to Step 1.5:**

- ✅ AgentPool fully implemented (no TODOs)
- ✅ Stress test: 100 agents × 1000 tasks → zero task loss
- ✅ Exhaustion handling: Graceful checkpoint + reassign
- ✅ Reset cycle tracking: Warnings at threshold
- ✅ Respawn: Restores full capacity
- ✅ Pool metrics: Accurate real-time stats
- ✅ Thread-safe: No race conditions
- ✅ Integrates with TaskScheduler
- ✅ Compatible with V3.1 schema (reset_cycle, exhaustion_history)
- ✅ Scale: Works for 1→100→1000 agents
- ✅ Zero vendor lock-in
- ✅ Future-proof for distributed pools

---

## 🚀 EXECUTION PROTOCOL

**When ready to start Step 1.4:**

1. Create `agent_pool.py` (complete, production-ready)
2. Create `test_agent_pool.py` (stress test)
3. Create `STEP_1_4_CHECKLIST.md`
4. Run tests
5. Verify zero task loss during exhaustion
6. Sign off on scale matrix
7. Move to Step 1.5

---

**Status: 🟢 MASTER PROMPT LOCKED - EXECUTING NOW**
