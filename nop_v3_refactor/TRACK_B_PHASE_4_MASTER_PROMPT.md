# 🎯 TRACK B PHASE 4: Auto-pilot Sprint Implementation - Master Prompt

**Date:** January 22, 2026, 11:15 PM IST  
**Status:** DESIGN THINKING LOOPS IN PROGRESS  
**Vision Alignment:** ✅ Locked to VISION_AND_NORTH_STAR.md  
**Depends On:** Phase 3 Dashboard (✅ COMPLETE)

---

## 🌟 YOUR ROLE (Role Reversal Wisdom)

**You are Lokesh asking yourself:** "If I were building the ultimate autonomous AI orchestration system that can run entire sprints without human intervention, what would I need you to tell me right now?"

**Answer:** This prompt.

---

## 📋 CONTEXT (Building on All Previous Phases)

### Completed Components
- ✅ **CRDTTaskStore:** 15K+ writes/sec, conflict-free
- ✅ **TaskScheduler:** 423K tasks/sec scheduling
- ✅ **AgentPool:** Multi-agent lifecycle management
- ✅ **TaskIngestionEngine:** Multi-source ingestion, 10K tasks/sec
- ✅ **orchestrator_v3:** Unified integration
- ✅ **DashboardEngine:** Real-time visibility, alerts, snapshots

### This Phase (4) - THE CROWN JEWEL
- Autonomous sprint execution engine
- Multi-slot parallel orchestration
- Intelligent task assignment with tier matching
- Budget-aware execution with cost limits
- Halt conditions (blockers, tier mismatches)
- Progress tracking and reporting
- Mission-based orchestration
- Self-healing and recovery

---

## 🏗️ SCALE MATRIX (Non-Negotiable)

| Metric | Target | Notes |
|--------|--------|-------|
| **Slots per Sprint** | 10+ | Parallel orchestration |
| **Tasks per Sprint** | 100+ | In a single execution |
| **Sprint Duration** | Configurable | 5min to 24hr |
| **Decision Latency** | <100ms | Task assignment |
| **Budget Tracking** | Real-time | $ and tokens |
| **Recovery Time** | <5s | From failures |
| **Concurrent Sprints** | 5 | Isolated missions |

---

## 🎯 PHASE 4 MISSION

**Build an enterprise-grade autonomous sprint execution engine** that:

✅ **Orchestrates multiple slots in parallel** (Sprint Command)  
✅ **Intelligently assigns tasks** based on tier, skills, availability  
✅ **Respects budget limits** with real-time cost tracking  
✅ **Halts on blockers** (circular deps, tier mismatches)  
✅ **Tracks progress** with detailed reporting  
✅ **Supports dry-run mode** for planning  
✅ **Recovers from failures** with retry logic  
✅ **Executes missions** with goals and success criteria  
✅ **Integrates with dashboard** for visibility  

---

## 🧠 DESIGN THINKING LOOPS (Infinite Until Convergence)

### Loop 1: Sprint Execution Model
**Question:** What is the core execution model for autonomous sprints?

**Options:**
1. **Sequential** - One task at a time, simple but slow
2. **Parallel-per-slot** - Each slot executes independently
3. **Wave-based** - Group tasks by dependency layer, execute in waves
4. **Event-driven** - React to task completions, dynamic assignment

**Analysis:**
- Sequential is too slow for enterprise scale
- Parallel-per-slot maximizes throughput but needs coordination
- Wave-based respects dependencies naturally
- Event-driven is most flexible but complex

**Decision:** **Hybrid: Wave-based initialization + Event-driven execution**

**Rationale:** Start with dependency wave analysis, then use event-driven for dynamic adaptation.

---

### Loop 2: Slot Orchestration Strategy
**Question:** How should multiple slots be coordinated?

**Options:**
1. **Round-robin** - Simple rotation through slots
2. **Load-balanced** - Assign to least-loaded slot
3. **Tier-matched** - Match task tier to slot capability
4. **Priority-weighted** - Higher priority tasks to better slots

**Analysis:**
- Round-robin doesn't optimize for capability
- Load-balanced ignores tier requirements
- Tier-matched ensures quality but may leave slots idle
- Priority-weighted optimizes outcomes

**Decision:** **Tier-matched with load-balanced fallback**

**Rationale:** First match tier, then balance load among matching slots.

---

### Loop 3: Task Assignment Algorithm
**Question:** How should tasks be assigned to slots?

**Algorithm Design:**
```python
def assign_task(task, available_slots):
    # Step 1: Filter by tier requirement
    capable_slots = [s for s in available_slots if s.tier >= task.required_tier]
    
    # Step 2: Filter by required skills
    skilled_slots = [s for s in capable_slots if s.has_skills(task.required_skills)]
    
    # Step 3: Prefer idle over busy
    idle_slots = [s for s in skilled_slots if s.status == 'idle']
    if idle_slots:
        return min(idle_slots, key=lambda s: s.current_load)
    
    # Step 4: Force-assign if critical
    if task.priority == 1 and task.force_assign:
        return min(capable_slots, key=lambda s: s.queue_depth)
    
    # Step 5: Queue if no immediate slot
    return None  # Task remains in queue
```

**Decision:** Implement multi-stage filtering algorithm.

---

### Loop 4: Budget Control System
**Question:** How should budget limits be enforced?

**Options:**
1. **Hard limit** - Stop immediately when budget exceeded
2. **Soft limit** - Warn but allow continuation
3. **Per-task budget** - Each task has individual limit
4. **Rolling budget** - Per-hour/per-day limits

**Analysis:**
- Hard limit prevents overspend but may leave work incomplete
- Soft limit risks budget overrun
- Per-task is granular but complex
- Rolling enables sustained operation

**Decision:** **Hard limit with graceful wind-down + per-task estimates**

**Implementation:**
```python
class BudgetController:
    def __init__(self, limit_usd: float):
        self.limit = limit_usd
        self.spent = 0.0
        self.reserved = 0.0  # For in-progress tasks
    
    def can_start_task(self, estimated_cost: float) -> bool:
        return (self.spent + self.reserved + estimated_cost) <= self.limit
    
    def reserve(self, task_id: str, amount: float) -> None:
        self.reservations[task_id] = amount
        self.reserved += amount
    
    def commit(self, task_id: str, actual: float) -> None:
        reserved = self.reservations.pop(task_id, 0)
        self.reserved -= reserved
        self.spent += actual
```

---

### Loop 5: Halt Conditions
**Question:** When should a sprint automatically halt?

**Halt Conditions Identified:**

1. **Budget Exhausted** - No remaining budget
2. **All Slots Exhausted** - Every slot hit rate limits
3. **Circular Dependency Detected** - Infinite loop risk
4. **Critical Task Failed** - Priority 1 task with no retry left
5. **User Interrupt** - Manual halt request
6. **Time Limit** - Sprint duration exceeded
7. **Tier Mismatch (optional)** - No slot can handle required tier

**Halt Response:**
```python
class HaltResponse:
    def __init__(self, reason: str, recoverable: bool, tasks_affected: List[str]):
        self.reason = reason
        self.recoverable = recoverable
        self.tasks_affected = tasks_affected
        self.timestamp = time.time()
        self.recommendation = self._generate_recommendation()
```

**Decision:** Implement all 7 halt conditions with graceful handling.

---

### Loop 6: Sprint Modes
**Question:** What modes of operation should the sprint support?

**Modes:**

1. **auto** - Full autonomous execution
2. **plan** - Show what would happen (dry run)
3. **guided** - Pause for human approval at each step
4. **status** - Report current state only

**Mode Behaviors:**
| Mode | Claim Tasks | Execute | Modify State | Return |
|------|-------------|---------|--------------|--------|
| auto | ✅ | ✅ | ✅ | Results |
| plan | ❌ | ❌ | ❌ | Plan |
| guided | ✅ (on approval) | ✅ | ✅ | Step-by-step |
| status | ❌ | ❌ | ❌ | Current state |

**Decision:** Implement all 4 modes for maximum flexibility.

---

### Loop 7: Progress Tracking
**Question:** How should sprint progress be tracked and reported?

**Metrics to Track:**
- Tasks completed / total
- Time elapsed / estimated
- Budget spent / limit
- Slots active / total
- Errors encountered / recovered
- Current wave / total waves

**Report Format:**
```
🚀 Sprint Progress Report
═══════════════════════════════════════
Mission: Implement NOP V3.1
Duration: 2h 15m / 4h (56%)

📊 TASKS
├── Completed: 45/100 (45%)
├── In Progress: 8
├── Blocked: 5
├── Remaining: 42
└── Failed: 0

🤖 SLOTS
├── Active: 6/10
├── Idle: 2
├── Exhausted: 2
└── Utilization: 80%

💰 BUDGET
├── Spent: $4.20 / $10.00
├── Remaining: $5.80 (58%)
└── Burn Rate: $1.87/hr

⏱️ ETA: 1h 45m
```

---

### Loop 8: Mission-Based Orchestration
**Question:** How should missions (high-level goals) be defined and executed?

**Mission Schema:**
```python
@dataclass
class Mission:
    id: str
    name: str
    goal: str
    success_criteria: List[str]
    tasks: List[str]  # Task IDs
    slots: List[str]  # Slot IDs to use
    budget_limit: float
    time_limit_hours: float
    priority: int
    status: MissionStatus  # PENDING, RUNNING, PAUSED, COMPLETED, FAILED
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    result: Optional[Dict]
```

**Mission Lifecycle:**
1. CREATE - Define mission with tasks and constraints
2. PLAN - Analyze dependencies, estimate costs
3. EXECUTE - Run sprint with configured slots
4. MONITOR - Track progress via dashboard
5. COMPLETE - Evaluate success criteria
6. REPORT - Generate summary

**Decision:** Implement full mission lifecycle with persistence.

---

### Loop 9: Recovery and Retry Strategy
**Question:** How should the system handle failures and recover?

**Failure Types:**
1. **Task Failure** - Single task fails
2. **Slot Failure** - Agent crashes/exhausts
3. **System Failure** - Network, storage issues
4. **Budget Failure** - Unexpected cost spike

**Retry Strategy:**
```python
class RetryPolicy:
    def __init__(self):
        self.max_retries = 3
        self.backoff_base = 2  # seconds
        self.backoff_max = 60
    
    def get_delay(self, attempt: int) -> float:
        delay = self.backoff_base ** attempt
        return min(delay, self.backoff_max)
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        if attempt >= self.max_retries:
            return False
        # Retry on transient errors only
        return isinstance(error, (TimeoutError, ConnectionError, RateLimitError))
```

**Recovery Actions:**
- Task failure → Retry with exponential backoff
- Slot failure → Reassign tasks to available slot
- System failure → Checkpoint and resume
- Budget failure → Halt gracefully, report status

---

### Loop 10: Sprint Result Schema
**Question:** What should the sprint return when complete?

**Result Schema:**
```python
@dataclass
class SprintResult:
    sprint_id: str
    mission_id: Optional[str]
    status: SprintStatus  # COMPLETED, PARTIAL, FAILED, HALTED
    
    # Timing
    started_at: str
    completed_at: str
    duration_seconds: float
    
    # Task Metrics
    tasks_total: int
    tasks_completed: int
    tasks_failed: int
    tasks_skipped: int
    tasks_remaining: int
    
    # Slot Metrics
    slots_used: int
    slot_utilization: float
    slot_exhaustions: int
    
    # Budget Metrics
    budget_limit: Optional[float]
    budget_spent: float
    tokens_used: int
    
    # Details
    completed_tasks: List[str]
    failed_tasks: List[Dict]  # {task_id, error, attempts}
    warnings: List[str]
    halt_reason: Optional[str]
    
    # Recommendations
    next_steps: List[str]
```

---

### Loop 11: Integration with Existing Components
**Question:** How does autopilot integrate with existing V3.1 components?

**Integration Points:**

1. **orchestrator_v3** → Task operations (claim, complete, update)
2. **AgentPool** → Slot management (spawn, exhaust, respawn)
3. **TaskScheduler** → Intelligent routing
4. **DashboardEngine** → Progress visibility
5. **AlertEngine** → Halt condition triggers
6. **CRDTTaskStore** → Conflict-free task state
7. **TrendAnalyzer** → Velocity tracking

**Decision:** Autopilot is a composition layer on top of all components.

---

### Loop 12: MCP Tool Design
**Question:** What MCP tools should expose autopilot functionality?

**MCP Tools:**

1. **brain_autopilot_sprint()** (enhanced existing)
   - Full parameter set for all modes
   - Returns structured result

2. **brain_start_mission()** (new)
   - Create and start a mission
   - Returns mission_id

3. **brain_mission_status()** (new)
   - Get current mission progress
   - Detailed breakdown

4. **brain_halt_sprint()** (new)
   - Emergency stop
   - Graceful wind-down

5. **brain_resume_sprint()** (new)
   - Resume halted sprint
   - From checkpoint

---

### Loop 13: Checkpoint and Persistence
**Question:** How should sprint state be persisted for recovery?

**Checkpoint Contents:**
- Sprint ID and configuration
- Current wave and task positions
- Slot assignments and states
- Budget spent so far
- Completed task IDs
- Failed task details
- Timestamp

**Persistence Location:** `.brain/sprints/<sprint_id>/checkpoint.json`

**Checkpoint Frequency:**
- After each task completion
- After each wave completion
- Every 60 seconds minimum

**Decision:** Automatic checkpointing with configurable frequency.

---

### Loop 14: Testing Strategy
**Question:** How do we test autonomous sprint execution?

**Test Categories:**

1. **Unit Tests**
   - BudgetController calculations
   - Task assignment algorithm
   - Halt condition detection
   - Retry policy logic

2. **Integration Tests**
   - Full sprint with mock slots
   - Mission lifecycle
   - Checkpoint/recovery
   - Dashboard integration

3. **Performance Tests**
   - 100 tasks / 10 slots benchmark
   - Decision latency <100ms
   - Checkpoint overhead

4. **Stress Tests**
   - Continuous sprints for 1 hour
   - Slot exhaustion recovery
   - Budget edge cases

**Decision:** Comprehensive test suite with performance benchmarks.

---

### Loop 15: Convergence Validation
**Question:** Have we achieved unanimous convergence on all design decisions?

**Checklist:**

| Decision | Converged | Rationale |
|----------|-----------|-----------|
| Execution Model | ✅ | Wave-based + event-driven |
| Slot Orchestration | ✅ | Tier-matched + load-balanced |
| Task Assignment | ✅ | Multi-stage filtering |
| Budget Control | ✅ | Hard limit + per-task estimates |
| Halt Conditions | ✅ | 7 conditions with graceful handling |
| Sprint Modes | ✅ | auto, plan, guided, status |
| Progress Tracking | ✅ | Comprehensive metrics |
| Missions | ✅ | Full lifecycle with persistence |
| Recovery | ✅ | Exponential backoff + reassignment |
| Results | ✅ | Structured SprintResult |
| Integration | ✅ | Composition on existing components |
| MCP Tools | ✅ | 5 tools (1 enhanced, 4 new) |
| Checkpointing | ✅ | Automatic with recovery |
| Testing | ✅ | Unit, integration, performance, stress |

**UNANIMOUS CONVERGENCE ACHIEVED** ✅

---

## 📁 FILES TO CREATE

| File | Lines | Description |
|------|-------|-------------|
| `nop_core/autopilot.py` | ~1200 | Autopilot engine implementation |
| `tests/test_autopilot.py` | ~600 | Comprehensive test suite |
| `runtime/autopilot.py` | ~100 | Copy to runtime/ |
| MCP tools in `__init__.py` | ~300 | Enhanced + new tools |

---

## ✅ SUCCESS CRITERIA (Locked)

**Phase 4 is GREEN when:**

- ✅ AutopilotEngine fully implemented
- ✅ 4 sprint modes working (auto, plan, guided, status)
- ✅ Budget controller with real-time tracking
- ✅ 7 halt conditions implemented
- ✅ Mission lifecycle with persistence
- ✅ Checkpoint and recovery working
- ✅ <100ms task assignment latency
- ✅ 5 MCP tools exposed
- ✅ Comprehensive test suite passing
- ✅ 100 tasks / 10 slots benchmark successful

---

## 🚀 EXECUTION PROTOCOL

1. ✅ Design Thinking Loops (15/15 CONVERGED)
2. ⏳ Implement autopilot.py (~1200 lines)
3. ⏳ Implement test_autopilot.py (~600 lines)
4. ⏳ Copy to runtime/
5. ⏳ Add MCP tools to __init__.py
6. ⏳ Run verification checklist
7. ⏳ Create Phase 4 checklist
8. ⏳ NOP V3.1 COMPLETE! 🎉

---

**Status: 🟢 DESIGN CONVERGED - EXECUTING IMPLEMENTATION**
