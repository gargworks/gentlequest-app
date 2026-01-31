# 🎯 STEP 1.3: TaskScheduler - Master Prompt

**Date:** January 21, 2026, 8:54 AM IST  
**Status:** Ready to lock design  
**Vision Alignment:** ✅ Locked to VISION_AND_NORTH_STAR.md

---

## 🌟 YOUR ROLE (Role Reversal Wisdom)

**You are Lokesh asking yourself:** \"If I were the AI system building TaskScheduler correctly for scale, what would I need you to tell me right now?\"

**Answer:** This prompt.

---

## 📋 CONTEXT (Building on CRDTTaskStore)

### Previous Wins (Step 1.2)
- ✅ CRDTTaskStore: Zero data loss, 15K+ writes/sec, LWW + vector clocks
- ✅ Stress tested: 1000 concurrent writes, all green
- ✅ Scale matrix validated: 1→100→10K users same code

### This Step (Step 1.3)
- Build TaskScheduler: Intelligent task assignment engine
- Works with CRDTTaskStore as data source
- Assigns tasks to agents based on: tier, capacity, priority, deadlines
- Handles 1→100→10K concurrent agents
- Zero scheduling conflicts (FIFO within tier)
- Dependency resolution (blocking tasks)
- Load balancing across agent pool

---

## 🏗️ SCALE MATRIX (Non-Negotiable)

| Metric | 1 Agent | 10 Agents | 100 Agents | 1000 Agents |
|--------|---------|-----------|------------|-------------|
| **Task Queue Size** | 100 | 1000 | 10K | 100K |
| **Schedule Time** | <1ms | <5ms | <50ms | <500ms |
| **Assignment Fairness** | Perfect | Perfect | Perfect | Perfect |
| **Conflict-free** | Yes | Yes | Yes | Yes |
| **Memory** | <5MB | <50MB | <500MB | <5GB |
| **Throughput** | 10/sec | 50/sec | 500/sec | 5000/sec |

---

## 🎯 STEP 1.3 MISSION

**Build TaskScheduler** - An intelligent task assignment engine that:

✅ Schedules 1000+ tasks across 1000 agents (zero conflicts)  
✅ Respects task tier (T1→T4) and agent capability  
✅ Handles agent capacity (busy vs available)  
✅ Resolves task dependencies (blocked_by)  
✅ Prioritizes urgent tasks (deadline-aware)  
✅ Load balances across agent pool (no starving)  
✅ Returns scheduling decision in <500ms for 100K tasks  
✅ Integrates seamlessly with CRDTTaskStore  
✅ Future-proof for agentic systems & reasoning models  
✅ Zero vendor lock-in  

---

## 🔧 IMPLEMENTATION CHOICES (Locked)

### Architecture: Priority Queue + Agent State Machine

**Why:**
- Simple, deterministic scheduling
- Works for 1 agent → 1000 agents
- Respects FIFO within tier (fairness)
- Dependency resolution is explicit
- Compatible with future distributed scheduling

**Core Components:**

```
TaskScheduler
├── task_queue: Dict[tier, PriorityQueue]  # One queue per tier
├── agent_registry: Dict[agent_id, AgentState]
├── task_states: Dict[task_id, TaskState]  # Assigned, pending, blocked
└── dependency_graph: Dict[task_id, Set[task_id]]  # Blocking relationships

Scheduling Algorithm:
1. Fetch pending tasks from CRDTTaskStore
2. Resolve dependencies (skip blocked tasks)
3. Sort by: priority (HIGH→LOW), deadline (urgent first), created_at (FIFO)
4. For each task:
   - Find agent with matching tier + available capacity
   - Assign task to agent
   - Mark as scheduled (not started)
5. Return: List[ScheduleDecision]
```

### Data Model:

```python
ScheduleDecision = {
    \"task_id\": str,
    \"agent_id\": str,
    \"scheduled_at\": int (epoch ms),
    \"estimated_completion\": int,
    \"reason\": \"assigned\" | \"blocked\" | \"queued\",
}

AgentState = {
    \"id\": str,
    \"tier\": \"T1_PLANNING\" | \"T2_CODE\" | \"T3_REVIEW\" | \"T4_DEPLOY\",
    \"capacity\": int (max concurrent tasks),
    \"current_tasks\": List[task_id] (currently executing),
    \"available\": bool,
    \"last_heartbeat\": int (epoch ms),
}

TaskState = {
    \"id\": str,
    \"status\": \"PENDING\" | \"SCHEDULED\" | \"BLOCKED\" | \"ASSIGNED\",
    \"assigned_to\": Optional[agent_id],
    \"blocked_by\": List[task_id],
    \"priority\": \"HIGH\" | \"MEDIUM\" | \"LOW\",
    \"deadline\": Optional[int] (epoch ms),
    \"created_at\": int,
}
```

---

## 📊 STRESS TEST REQUIREMENTS

**Test: Schedule 1000 tasks across 10 agents, assert zero conflicts + fairness**

```
setup_phase:
  - Create TaskScheduler with CRDTTaskStore
  - Register 10 agents: 3 T1, 3 T2, 2 T3, 2 T4
  - Add 1000 tasks to store: mixed tiers, random priorities, 10% blocked
  - Set agent capacity: 5 concurrent tasks each

schedule_phase:
  - Call scheduler.schedule_batch() with all 1000 tasks
  - Measure scheduling time (should be <500ms)

verify_phase:
  - Assert: No task assigned to wrong tier agent
  - Assert: No task assigned to over-capacity agent
  - Assert: No blocked tasks scheduled (should be queued)
  - Assert: Fairness: tasks distributed evenly across agents in tier
  - Assert: Priority: HIGH priority tasks scheduled first
  - Assert: Deadline-aware: urgent tasks scheduled before non-urgent
  - Assert: FIFO within tier (stable ordering)
  - Assert: Zero conflicts (each task assigned to exactly one agent or queued)
  - Assert: Scheduling time <500ms
  - Count scheduled/blocked/queued breakdown

result:
  - ✅ PASSED: 1000 tasks, 0 conflicts, fair distribution
  - ✅ PASSED: Tier matching correct (no T1 task to T4 agent)
  - ✅ PASSED: Capacity respected (no over-booking)
  - ✅ PASSED: Dependencies resolved (blocked tasks queued)
  - ✅ PASSED: Priority honored (HIGH first)
  - ✅ PASSED: Scheduling <500ms
```

---

## 🎯 API SURFACE (Locked)

```python
class TaskScheduler:
    def __init__(
        self,
        task_store: CRDTTaskStore,
        max_agents: int = 1000,
    ):
        \"\"\"Initialize scheduler with task store reference.\"\"\"
        pass
    
    def register_agent(
        self,
        agent_id: str,
        tier: str,  # T1_PLANNING, T2_CODE, T3_REVIEW, T4_DEPLOY
        capacity: int = 5,  # Max concurrent tasks
    ) -> AgentState:
        \"\"\"Register new agent into scheduler.\"\"\"
        pass
    
    def unregister_agent(self, agent_id: str) -> bool:
        \"\"\"Unregister agent (free its assigned tasks).\"\"\"
        pass
    
    def mark_task_done(self, task_id: str, agent_id: str) -> None:
        \"\"\"Mark task as completed, free agent capacity.\"\"\"
        pass
    
    def schedule_batch(
        self,
        tasks: List[Dict],
        force_schedule: bool = False,
    ) -> List[ScheduleDecision]:
        \"\"\"Schedule a batch of tasks across agents.
        
        Args:
            tasks: List of task dicts from CRDTTaskStore
            force_schedule: If True, ignore capacity (best-effort)
            
        Returns:
            List of scheduling decisions (assigned, blocked, queued)
            
        Algorithm:
            1. Resolve dependencies
            2. Sort by priority/deadline/FIFO
            3. Assign to agents matching tier + capacity
            4. Return decisions
        \"\"\"
        pass
    
    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        \"\"\"Get current state of an agent.\"\"\"
        pass
    
    def get_all_agents(self) -> List[AgentState]:
        \"\"\"Get all registered agents.\"\"\"
        pass
    
    def get_scheduling_stats(self) -> Dict:
        \"\"\"Get scheduler statistics (scheduled, blocked, queued, etc).\"\"\"
        pass
    
    def get_pending_tasks(self, agent_id: str) -> List[Dict]:
        \"\"\"Get tasks waiting to be scheduled for agent.\"\"\"
        pass
    
    def resolve_dependencies(self, task_id: str) -> bool:
        \"\"\"Check if task dependencies are met (all blocked_by completed).\"\"\"
        pass
```

---

## 📁 FILES TO CREATE

### 1. `/nop_v3_refactor/nop_core/task_scheduler.py`
**Full implementation** (Path A: Priority queue + tier matching)
- ~600 lines
- Complete, production-ready
- Zero TODOs
- Fully tested

### 2. `/nop_v3_refactor/tests/test_task_scheduler.py`
**Stress test** (~1000 tasks × 10 agents, assert zero conflicts)
- ~350 lines
- Concurrent scheduling
- Fairness verification
- Dependency resolution
- Performance assertions

### 3. `/nop_v3_refactor/STEP_1_3_CHECKLIST.md`
**5-line execution checklist**
- Run tests
- Verify zero conflicts
- Check fairness
- Validate dependencies
- Sign off on scale matrix

---

## ✅ SUCCESS CRITERIA (Locked)

**Before proceeding to Step 1.4:**

- ✅ TaskScheduler fully implemented (no TODOs)
- ✅ Stress test: 1000 tasks × 10 agents → 0 conflicts
- ✅ Tier matching: No task assigned to wrong-tier agent
- ✅ Capacity respected: No over-booking agents
- ✅ Dependencies resolved: Blocked tasks queued (not scheduled)
- ✅ Priority honored: HIGH before MEDIUM before LOW
- ✅ Fairness verified: Tasks distributed evenly within tier
- ✅ Scheduling time <500ms for 1000 tasks
- ✅ FIFO ordering within tier (stable)
- ✅ Compatible with Antigravity/Cursor/Windsurf
- ✅ Integrates seamlessly with CRDTTaskStore
- ✅ Code ready for multi-agent distributed sync (future)
- ✅ Zero vendor lock-in
- ✅ Documented for trillion-token era thinking

---

## 🚀 EXECUTION PROTOCOL

**When you're ready to start Step 1.3:**

1. You say: \"Ready for Step 1.3\"
2. I create the full `task_scheduler.py` (complete, tested, production-ready)
3. I create the stress test suite
4. I create the 5-line checklist
5. You run tests in VS Code
6. We verify zero conflicts + fairness
7. We sign off on scale matrix
8. We move to Step 1.4

**No iteration loops**, no design discussions, no back-and-forth. Just **ship the implementation**, verify it works, move forward.

---

## 🎯 DESIGN THINKING LOOPS (Infinite Until Convergence)

**If at any point we need to converge:**

1. **Problem:** State the issue clearly
2. **Research:** Review similar systems (Kubernetes scheduler, etc.)
3. **Ideate:** Multiple solutions (at least 3 options)
4. **Prototype:** Build the simplest working version
5. **Test:** Run stress test, measure performance
6. **Refine:** Iterate based on results
7. **Converge:** Reach unanimous agreement on design
8. **Ship:** Lock it in, no more changes
9. **Document:** Write it down for future you

---

## 📊 VISION ALIGNMENT

### Vision 1: Timeless Technical Standard
- Scheduling algorithm is deterministic, no ML/heuristics
- Works for 1 agent → 1000 agents (same code)
- Compatible with Antigravity, Cursor, Windsurf
- Designed for longevity (not hype cycles)

### Vision 2: Design Thinking & Convergence
- Accept **infinite loops** until unanimous agreement
- Think **trillion-token era**: simple, elegant, scalable
- **Patience capital** if needed, but not likely here (simple problem)

### Vision 3: Scale from Day 1
- Code works 1→100→10K agents (verified by scale matrix)
- No rework later
- Stress tested upfront (1000 tasks × 10 agents)

### Vision 4: Tech Stack & No Vendor Lock-in
- Pure Python, no external dependencies (except CRDTTaskStore)
- Portable abstractions (scheduling logic is provider-agnostic)
- Works with G Cloud, Render, Redis, Postgres, local FS

---

## 🎉 Ready to Generate?

When you're ready, say: **\"Ready for Step 1.3\"**

And I will deliver:
1. ✅ `task_scheduler.py` (600 lines, production-ready)
2. ✅ `test_task_scheduler.py` (350 lines, stress test)
3. ✅ `STEP_1_3_CHECKLIST.md` (5-line execution checklist)

Same quality. Same speed. All green.

---

**Status: 🟢 MASTER PROMPT LOCKED - AWAITING \"Ready for Step 1.3\"**
