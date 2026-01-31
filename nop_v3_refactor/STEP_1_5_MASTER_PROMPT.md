# 🎯 STEP 1.5: MCP Integration with orchestrator_v3 - Master Prompt

**Date:** January 22, 2026, 11:00 PM IST  
**Status:** Ready to execute  
**Vision Alignment:** ✅ Locked to VISION_AND_NORTH_STAR.md  
**Depends On:** Step 1.4 AgentPool (✅ COMPLETE)

---

## 🌟 YOUR ROLE (Role Reversal Wisdom)

**You are Lokesh asking yourself:** "If I were the AI system building the unified orchestrator_v3 MCP integration correctly for enterprise scale, what would I need you to tell me right now?"

**Answer:** This prompt.

---

## 📋 CONTEXT (Building on Previous Steps)

### Completed Components
- ✅ **Step 1.1 CRDTTaskStore:** 15K+ writes/sec, zero data loss
- ✅ **Step 1.2 TaskScheduler:** 423K tasks/sec scheduling
- ✅ **Step 1.4 AgentPool:** Multi-agent lifecycle management
- ✅ **Phase 2 TaskIngestionEngine:** Multi-source ingestion, 10K tasks/sec

### This Step (1.5)
- Integrate all V3.1 components into unified orchestrator_v3
- Copy CRDTTaskStore, TaskScheduler, AgentPool to runtime/
- Create unified get_orchestrator() singleton
- Wire MCP tools to use orchestrator_v3
- Ensure checkpoint, handoff, binding all work through orchestrator

---

## 🏗️ SCALE MATRIX (Non-Negotiable)

| Metric | Target | Verified |
|--------|--------|----------|
| **Orchestrator Init** | <100ms | Pending |
| **Task Operations** | 10K/sec | ✅ (via CRDT) |
| **Scheduling** | 423K/sec | ✅ (via Scheduler) |
| **Agent Ops** | 1K/sec | ✅ (via Pool) |
| **Singleton Consistency** | 100% | Pending |
| **MCP Tool Latency** | <50ms | Pending |

---

## 🎯 STEP 1.5 MISSION

**Unify all V3.1 components into orchestrator_v3** with:

✅ Copy `nop_core/` components to `runtime/`  
✅ Create unified `orchestrator_v3.py` that uses all components  
✅ Single `get_orchestrator()` singleton across all MCP tools  
✅ Wire existing MCP tools to use orchestrator_v3 methods  
✅ Verify checkpoint, handoff, binding through orchestrator  
✅ Preserve backward compatibility with existing API  
✅ Add comprehensive error handling  
✅ Performance: <100ms init, <50ms per operation  

---

## 🔧 CURRENT STATE ANALYSIS

### Problem Statement
Currently, the MCP tools in `__init__.py` have:
1. Scattered implementations (some direct, some via orchestrator)
2. Two singleton patterns (`get_orch()` and `get_orchestrator()`)
3. No integration with new V3.1 components

### Target State
```
__init__.py (MCP Tools)
    │
    ├── get_orch() ──────────────────────────────┐
    │                                             │
    ▼                                             ▼
orchestrator_v3.py (Unified Orchestrator)   (SAME INSTANCE)
    │
    ├── CRDTTaskStore (15K writes/sec)
    ├── TaskScheduler (423K tasks/sec)
    ├── AgentPool (lifecycle management)
    └── TaskIngestionEngine (10K ingest/sec)
```

---

## 📁 FILES TO CREATE/MODIFY

### 1. Copy to Runtime (Symlink or Copy)
```
mcp-server-nucleus/src/mcp_server_nucleus/runtime/
├── crdt_task_store.py  ← from nop_v3_refactor/nop_core/
├── task_scheduler.py   ← from nop_v3_refactor/nop_core/
├── agent_pool.py       ← from nop_v3_refactor/nop_core/
├── task_ingestion.py   ← from nop_v3_refactor/nop_core/
└── orchestrator_v3.py  ← UNIFIED (enhance existing)
```

### 2. Update orchestrator_v3.py
- Import all V3.1 components
- Initialize in `__init__`
- Delegate methods to components
- Single singleton pattern

### 3. Update __init__.py
- Remove duplicate implementations
- All tools use `get_orch()` → `orchestrator_v3.get_orchestrator()`

---

## 🔧 ORCHESTRATOR_V3 API SURFACE

```python
class NucleusOrchestratorV3:
    """Unified orchestrator for all NOP V3.1 operations."""
    
    def __init__(self, brain_path: Path = None):
        self.brain_path = brain_path or self._get_default_brain_path()
        
        # Initialize V3.1 components
        self.task_store = CRDTTaskStore()
        self.scheduler = TaskScheduler(self.task_store)
        self.agent_pool = AgentPool()
        self.ingestion_engine = TaskIngestionEngine(
            task_store=self.task_store,
            agent_pool=self.agent_pool,
            brain_path=self.brain_path,
        )
        
        # Load initial state
        self._load_state()
    
    # ═══════════════════════════════════════════════════════════════
    # TASK OPERATIONS (delegated to CRDTTaskStore)
    # ═══════════════════════════════════════════════════════════════
    
    def get_task(self, task_id: str) -> Optional[Dict]: ...
    def get_all_tasks(self) -> List[Dict]: ...
    def create_task(self, task: Dict) -> Dict: ...
    def update_task(self, task_id: str, updates: Dict) -> Dict: ...
    def delete_task(self, task_id: str) -> bool: ...
    
    # ═══════════════════════════════════════════════════════════════
    # CHECKPOINT & CONTEXT (V3.1 schema)
    # ═══════════════════════════════════════════════════════════════
    
    def checkpoint_task(self, task_id: str, data: Dict) -> Dict: ...
    def resume_from_checkpoint(self, task_id: str) -> Dict: ...
    def generate_context_summary(self, task_id: str, summary: str, ...) -> Dict: ...
    
    # ═══════════════════════════════════════════════════════════════
    # SCHEDULING (delegated to TaskScheduler)
    # ═══════════════════════════════════════════════════════════════
    
    def get_next_task(self, agent_id: str, skills: List[str]) -> Optional[Dict]: ...
    def schedule_batch(self, tasks: List[Dict]) -> List[Dict]: ...
    
    # ═══════════════════════════════════════════════════════════════
    # AGENT POOL (delegated to AgentPool)
    # ═══════════════════════════════════════════════════════════════
    
    def spawn_agent(self, model: str, tier: str, ...) -> Dict: ...
    def get_agent(self, agent_id: str) -> Optional[Dict]: ...
    def mark_agent_exhausted(self, agent_id: str, reason: str) -> Dict: ...
    def respawn_agent(self, agent_id: str) -> Dict: ...
    def get_pool_metrics(self) -> Dict: ...
    
    # ═══════════════════════════════════════════════════════════════
    # INGESTION (delegated to TaskIngestionEngine)
    # ═══════════════════════════════════════════════════════════════
    
    def ingest_tasks(self, source: str, **kwargs) -> Dict: ...
    def rollback_ingestion(self, batch_id: str) -> Dict: ...
    
    # ═══════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ═══════════════════════════════════════════════════════════════
    
    def _load_state(self) -> None: ...
    def _save_state(self) -> None: ...
    def _sync_to_legacy_json(self) -> None: ...


# SINGLETON
_orchestrator: Optional[NucleusOrchestratorV3] = None

def get_orchestrator(brain_path: Path = None) -> NucleusOrchestratorV3:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = NucleusOrchestratorV3(brain_path)
    return _orchestrator
```

---

## 🔧 INTEGRATION CHECKLIST

### Phase A: Copy Components
1. [ ] Copy crdt_task_store.py to runtime/
2. [ ] Copy task_scheduler.py to runtime/
3. [ ] Copy agent_pool.py to runtime/
4. [ ] Copy task_ingestion.py to runtime/
5. [ ] Verify imports work

### Phase B: Enhance orchestrator_v3.py
1. [ ] Import all components
2. [ ] Initialize in __init__
3. [ ] Delegate task operations
4. [ ] Delegate scheduling
5. [ ] Delegate agent pool
6. [ ] Delegate ingestion
7. [ ] Add _load_state/_save_state

### Phase C: Wire MCP Tools
1. [ ] Verify get_orch() delegates to get_orchestrator()
2. [ ] All checkpoint tools use orchestrator
3. [ ] All handoff tools use orchestrator
4. [ ] All scheduling tools use orchestrator
5. [ ] New ingestion tools use orchestrator

### Phase D: Verify
1. [ ] Singleton consistency test
2. [ ] Checkpoint persistence test
3. [ ] Full agent handoff test
4. [ ] Performance benchmark

---

## ✅ SUCCESS CRITERIA (Locked)

**Before proceeding to Phase 3:**

- ✅ All V3.1 components copied to runtime/
- ✅ orchestrator_v3.py uses all components
- ✅ Single singleton pattern (no dual instances)
- ✅ All MCP tools route through orchestrator
- ✅ Checkpoint persistence works end-to-end
- ✅ Agent handoff works end-to-end
- ✅ Init time <100ms, operation latency <50ms
- ✅ Backward compatible with existing tools

---

## 🚀 EXECUTION PROTOCOL

1. Copy components to runtime/
2. Enhance orchestrator_v3.py
3. Verify integration
4. Run performance benchmarks
5. Create checklist
6. Move to Phase 3

---

**Status: 🟢 MASTER PROMPT LOCKED - EXECUTING NOW**
