# 🎯 TRACK B - PHASE 1: Schema Extensions - Master Prompt

**Date:** January 22, 2026, 10:30 PM IST  
**Status:** Ready for Design Thinking Loops  
**Vision Alignment:** ✅ Locked to VISION_AND_NORTH_STAR.md  
**Track:** B (MCP Integration) - Running in Parallel with Track A  
**Execution Context:** Windsurf IDE → Track C (Parallel Execution)

---

## 🌟 YOUR ROLE (Role Reversal Wisdom)

**You are Lokesh asking yourself:** "If I were the AI system extending the NOP V3.0 schemas for production MCP integration, what would I need you to tell me right now to build it correctly for scale?"

**Answer:** This prompt.

**North Star Reminder:** We have years. Nobody leaves until done. Let's make NOP the orchestrator that runs the global AI economy. 🔥

---

## 📖 CONTEXT (Building on Tracks A + Current MCP)

### Track A Achievements (Pure Python Core)
- ✅ Step 1.2: CRDTTaskStore - COMPLETE (15K+ writes/sec, zero data loss)
- ✅ Step 1.3: TaskScheduler - COMPLETE (423K tasks/sec, zero conflicts)
- ⏳ Step 1.4: AgentPool - MASTER PROMPT READY (100 agents × 1000 tasks)

### Current MCP Implementation (NOP V2.0 → V3.1)
**Location:** `/Users/lokeshgarg/ai-mvp-backend/.brain/`

**What exists in V2.0/V3.0:**
- ✅ `brain_orchestrate()` - The "God Command"
- ✅ `brain_slot_complete()` - Task completion with fence tokens
- ✅ Model tier system (Premium/Thinking/Standard/Fast/Code)
- ✅ Fence token coordination (monotonic, conflict-free)
- ✅ Multi-slot registry (windsurf_001, antigravity_001, etc.)
- ✅ Binding types (hard/soft/free) - ALREADY EXISTS
- ✅ Cost tracking (tokens, cost_per_1k) - ALREADY EXISTS
- ✅ Source tracking - ALREADY EXISTS
- ✅ Dependency tracking (depends_on, blocked_by) - ALREADY EXISTS

**Current V3.1 Schema (Post-Migration):**
```
.brain/
├── ledger/
│   ├── tasks.json (V3.1 format - 140+ tasks)
│   │   ├── checkpoint (NEW in V3.1)
│   │   ├── context_summary (NEW in V3.1)
│   │   └── dependency_metadata (NEW in V3.1)
│   ├── fence_counter_v3.json
│   └── events.jsonl
├── slots/
│   ├── registry.json (V3.1 format - 4 slots)
│   │   ├── reset_cycle (NEW in V3.1)
│   │   └── exhaustion_history (NEW in V3.1)
│   └── registry_v3_schema.json
└── protocols/
    ├── NOP_V2.json
    └── tiers.json
```

### This Phase (Phase 1)
**Extend schemas to support NOP V3.1 features:**
- Task binding types (hard/soft/free reassignment) ← EXISTS
- Enhanced cost tracking (per-slot, per-task) ← EXISTS
- Reset cycle management (Gemini 5h resets, etc) ← NEW
- Checkpoint support (partial progress) ← NEW
- Context summaries (for reassignment) ← NEW
- Ingestion source tracking ← EXISTS
- Dependency chain metadata ← NEW

---

## 📊 SCALE MATRIX (Non-Negotiable)

| Metric | 1 User | 100 Users | 10K Users | Notes |
|--------|--------|-----------|-----------|-------|
| **Tasks** | 100 | 10K | 1M | JSON → CRDT at scale |
| **Slots** | 4 | 40 | 400 | Horizontal scaling |
| **Schema Read** | <1ms | <5ms | <50ms | Indexed access |
| **Schema Write** | <5ms | <20ms | <100ms | Atomic JSON ops |
| **Migration** | <1s | <10s | <60s | In-place update |
| **Rollback** | <1s | <5s | <30s | Backup restore |
| **Memory** | <10MB | <100MB | <1GB | Lazy loading |

---

## 🎯 PHASE 1 MISSION

**Extend NOP V2.0 schemas to V3.1** - Production-ready schema evolution that:

✅ Maintains backward compatibility with V2.0 (CRITICAL)  
✅ Adds V3.1 fields without breaking existing tools  
✅ Supports multi-source task ingestion (planning, todos, handoffs, manual, synthesis)  
✅ Enables flexible task reassignment (hard/soft/free binding)  
✅ Tracks costs accurately across slots (per-task, per-session)  
✅ Handles model reset cycles (Gemini 5h, Opus unlimited)  
✅ Preserves task context for handoffs (context_summary)  
✅ Supports checkpointing for long-running tasks  
✅ Computes dependency metadata (depth, blocks, estimated_unblock_time)  
✅ Works with 1→100→10K tasks (same schema, same code)  
✅ Zero vendor lock-in (standard JSON, portable)  
✅ Future-proof for reasoning models (o1, o3, trillion-token era)  

---

## 🧠 DESIGN THINKING LOOPS (INFINITE UNTIL CONVERGENCE)

**CRITICAL: Run these loops BEFORE executing ANYTHING (5-15 iterations minimum)**

### Loop Structure (Mandatory - NON-NEGOTIABLE)

```
┌────────────────────────────────────────────────────────────────┐
│ LOOP 1: SITUATION ANALYSIS (Current Ground Reality)           │
├────────────────────────────────────────────────────────────────┤
│ Questions to answer:                                           │
│ 1. What schemas exist right now in .brain/?                    │
│ 2. What fields does V2.0/V3.0 have that we must preserve?      │
│ 3. What V3.1 features require new fields?                      │
│ 4. What could break during migration?                          │
│ 5. List 5-10 failure modes for schema extension               │
│ 6. What is the current migration status?                       │
│ 7. Are there any orphaned or inconsistent fields?              │
├────────────────────────────────────────────────────────────────┤
│ Output: Current state snapshot + constraints + gaps            │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ LOOP 2: BACKWARD COMPATIBILITY ANALYSIS                        │
├────────────────────────────────────────────────────────────────┤
│ Questions to answer:                                           │
│ 1. Which tools read tasks.json? (brain_orchestrate, etc)       │
│ 2. What happens if we add new fields?                          │
│ 3. What happens if we remove/rename old fields?                │
│ 4. How do we ensure V2.0 tools still work?                     │
│ 5. What's the migration path? (one-time vs gradual)            │
│ 6. What's the rollback procedure?                              │
│ 7. How do we test backward compatibility?                      │
├────────────────────────────────────────────────────────────────┤
│ Output: Compatibility guarantee strategy + test plan           │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ LOOP 3: RESET CYCLE MANAGEMENT DESIGN                          │
├────────────────────────────────────────────────────────────────┤
│ Models with reset cycles:                                      │
│ - Gemini 3 Pro High/Low: 5 hours                               │
│ - Opus 4.5: Unlimited (null)                                   │
│ - Codex 5.1: Rate limited                                      │
│ - Claude Sonnet: Context-limited                               │
│                                                                 │
│ Questions to answer:                                           │
│ 1. How do we track time-to-reset per slot?                     │
│ 2. How do we detect approaching reset (e.g., 30min warning)?   │
│ 3. What happens to assigned tasks when reset hits?             │
│ 4. How do we reassign tasks after reset?                       │
│ 5. How do we spawn new slots post-reset?                       │
│ 6. How do we record exhaustion history for analytics?          │
│ 7. What's the schema for reset_cycle field?                    │
├────────────────────────────────────────────────────────────────┤
│ Output: Reset cycle schema + handling logic + warning system   │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ LOOP 4: CHECKPOINT SUPPORT DESIGN                              │
├────────────────────────────────────────────────────────────────┤
│ Checkpoints allow resuming partial work:                       │
│ - Long tasks can be paused/resumed                             │
│ - Prevents full restart on failure                             │
│ - Enables incremental progress tracking                        │
│ - Critical for agent handoffs                                  │
│                                                                 │
│ Questions to answer:                                           │
│ 1. What data goes in checkpoint field?                         │
│ 2. How often do we checkpoint? (time-based? step-based?)       │
│ 3. How do we resume from checkpoint?                           │
│ 4. How do we validate checkpoint integrity?                    │
│ 5. How do we clean up old checkpoints?                         │
│ 6. What's the MCP tool for checkpointing?                      │
│ 7. How do checkpoints interact with fence tokens?              │
├────────────────────────────────────────────────────────────────┤
│ Output: Checkpoint schema + lifecycle management + MCP tools   │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ LOOP 5: CONTEXT SUMMARY FOR HANDOFFS                           │
├────────────────────────────────────────────────────────────────┤
│ When reassigning task from Slot A → Slot B:                    │
│ - Slot B needs context of what Slot A did                      │
│ - Context must be concise (token efficient)                    │
│ - Context must be actionable (not just history)                │
│ - Key decisions must be preserved                              │
│                                                                 │
│ Questions to answer:                                           │
│ 1. What goes in context_summary field?                         │
│ 2. How do we generate summaries? (LLM vs template)             │
│ 3. How do we version context as task evolves?                  │
│ 4. How do we compress context for long-running tasks?          │
│ 5. How do we validate context completeness?                    │
│ 6. What's the max context size (tokens)?                       │
│ 7. How does context_summary differ from checkpoint?            │
├────────────────────────────────────────────────────────────────┤
│ Output: Context summary schema + generation strategy           │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ LOOP 6: DEPENDENCY CHAIN METADATA                              │
├────────────────────────────────────────────────────────────────┤
│ Enhanced dependency tracking:                                  │
│ - blocked_by: List of task IDs (forward)                       │
│ - blocks: List of task IDs (reverse mapping)                   │
│ - dependency_depth: Critical path depth                        │
│ - estimated_unblock_time: When blockers expected to complete   │
│                                                                 │
│ Questions to answer:                                           │
│ 1. How do we compute dependency depth efficiently?             │
│ 2. How do we update blocks field automatically?                │
│ 3. How do we estimate unblock time from historical data?       │
│ 4. How do we detect circular dependencies?                     │
│ 5. How do we optimize critical path?                           │
│ 6. What's the performance at 10K tasks?                        │
│ 7. How do dependency changes trigger re-computation?           │
├────────────────────────────────────────────────────────────────┤
│ Output: Dependency metadata schema + computation algorithms    │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ LOOP 7: BINDING TYPE SEMANTICS                                 │
├────────────────────────────────────────────────────────────────┤
│ Binding Types (from roadmap):                                  │
│ - HARD: Cannot reassign (stateful work in progress)            │
│ - SOFT: Can reassign with context (synthesis needed)           │
│ - FREE: Instant reassign (no context loss)                     │
│                                                                 │
│ Questions to answer:                                           │
│ 1. How do we determine binding type? (auto vs manual)          │
│ 2. What metadata is needed for SOFT reassignment?              │
│ 3. How do we prevent HARD task reassignment?                   │
│ 4. How does scheduler respect binding constraints?             │
│ 5. How do we transition binding types? (FREE→SOFT→HARD)        │
│ 6. What's the reassign_cost field for?                         │
│ 7. How do bindings interact with checkpoints?                  │
├────────────────────────────────────────────────────────────────┤
│ Output: Binding type schema + transition rules + enforcement   │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ LOOP 8: INGESTION SOURCE TRACKING                              │
├────────────────────────────────────────────────────────────────┤
│ Task sources (from roadmap):                                   │
│ - planning: Markdown files with tasks                          │
│ - todos: JSON task lists                                       │
│ - handoffs: Cross-slot task transfers                          │
│ - manual: Direct creation via brain_add_task                   │
│ - synthesis: Auto-generated from analysis                      │
│                                                                 │
│ Questions to answer:                                           │
│ 1. What metadata do we need per source?                        │
│ 2. How do we deduplicate tasks from multiple sources?          │
│ 3. How do we track source lineage (chain of sources)?          │
│ 4. How do we prioritize tasks by source?                       │
│ 5. How do we audit task origins?                               │
│ 6. What's the schema for ingestion_source field?               │
│ 7. How does source affect binding type?                        │
├────────────────────────────────────────────────────────────────┤
│ Output: Source tracking schema + deduplication + audit trail   │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ LOOP 9: COST TRACKING ENHANCEMENT                              │
├────────────────────────────────────────────────────────────────┤
│ Cost tracking needs:                                           │
│ - Per-task cost (tokens used × cost_per_1k)                    │
│ - Per-slot session cost                                        │
│ - Global budget tracking                                       │
│ - Cost projections for planning                                │
│                                                                 │
│ Questions to answer:                                           │
│ 1. How do we track tokens used per task accurately?            │
│ 2. How do we calculate cost from tokens? (model-specific)      │
│ 3. Where do we store running totals? (slot vs global)          │
│ 4. How do we handle cost spikes from reasoning models?         │
│ 5. How do we project costs for sprint planning?                │
│ 6. What alerts trigger on cost overruns?                       │
│ 7. How do we optimize cost vs performance?                     │
├────────────────────────────────────────────────────────────────┤
│ Output: Cost tracking schema + calculation logic + alerts      │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ LOOP 10: ALTERNATIVE SCHEMA DESIGNS                            │
├────────────────────────────────────────────────────────────────┤
│ Path A: Extend in-place (modify tasks.json directly)           │
│ → Pro: Simple, single file                                     │
│ → Con: Risk breaking V2.0 tools                                │
│ → Migration: One-time script                                   │
│                                                                 │
│ Path B: Versioned schemas (tasks_v3.json)                      │
│ → Pro: V2.0 untouched, safe                                    │
│ → Con: Two files to maintain                                   │
│ → Migration: Gradual transition                                │
│                                                                 │
│ Path C: Hybrid (tasks.json + extension files)                  │
│ → Pro: Backward compat + new features                          │
│ → Con: More complex reads                                      │
│ → Migration: Overlay pattern                                   │
│                                                                 │
│ Path D: CRDT Integration (from Track A)                        │
│ → Pro: High performance, conflict-free                         │
│ → Con: More complex setup                                      │
│ → Migration: Full refactor                                     │
├────────────────────────────────────────────────────────────────┤
│ Output: Ranked paths with decision criteria + final choice     │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ LOOP 11: MIGRATION SAFETY                                      │
├────────────────────────────────────────────────────────────────┤
│ Questions to answer:                                           │
│ 1. How do we test schema changes without breaking production?  │
│ 2. What's the rollback plan if migration fails?                │
│ 3. How do we validate data integrity post-migration?           │
│ 4. What happens to in-flight tasks during migration?           │
│ 5. How do we preserve events.jsonl history?                    │
│ 6. What's the backup strategy?                                 │
│ 7. How do we communicate schema changes to agents?             │
├────────────────────────────────────────────────────────────────┤
│ Output: Migration safety checklist + rollback procedure        │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ LOOP 12: MCP TOOLS INTEGRATION                                 │
├────────────────────────────────────────────────────────────────┤
│ New/Updated MCP tools for V3.1:                                │
│ - brain_checkpoint_task() - Save progress checkpoint           │
│ - brain_resume_from_checkpoint() - Resume with context         │
│ - brain_generate_handoff_summary() - Create handoff context    │
│ - brain_ingest_tasks() - Multi-source ingestion                │
│ - brain_status_dashboard() - Real-time status                  │
│                                                                 │
│ Questions to answer:                                           │
│ 1. How do tools read/write V3.1 fields?                        │
│ 2. What validation do tools perform?                           │
│ 3. How do tools handle missing V3.1 fields gracefully?         │
│ 4. What events do V3.1 operations emit?                        │
│ 5. How do tools coordinate with orchestrator_v3.py?            │
│ 6. What's the _impl pattern for testability?                   │
│ 7. How do we avoid FunctionTool callable errors?               │
├────────────────────────────────────────────────────────────────┤
│ Output: MCP tool specifications + integration patterns         │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ LOOP 13: ORCHESTRATOR V3 INTEGRATION                           │
├────────────────────────────────────────────────────────────────┤
│ orchestrator_v3.py must:                                       │
│ - Read/write V3.1 task fields                                  │
│ - Sync with legacy JSON for backward compat                    │
│ - Integrate with CRDTTaskStore (from Track A)                  │
│ - Integrate with TaskScheduler (from Track A)                  │
│ - Support checkpoint/resume operations                         │
│                                                                 │
│ Questions to answer:                                           │
│ 1. How does orchestrator singleton work?                       │
│ 2. How do we prevent multiple singleton instances?             │
│ 3. How does CRDT sync with JSON?                               │
│ 4. What's the transaction model for atomic updates?            │
│ 5. How do we handle concurrent slot operations?                │
│ 6. What metrics does orchestrator expose?                      │
│ 7. How does orchestrator scale to 10K tasks?                   │
├────────────────────────────────────────────────────────────────┤
│ Output: Orchestrator integration spec + singleton pattern      │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ LOOP 14: FINAL SCHEMA DESIGN (CONVERGENCE)                     │
├────────────────────────────────────────────────────────────────┤
│ Synthesize all loops into final V3.1 schema specification.     │
│                                                                 │
│ tasks_v3_1.json format:                                        │
│ {                                                               │
│   "id": str,                                                    │
│   "description": str,                                           │
│   "status": str,                                                │
│   "priority": int,                                              │
│   "tier": str,                                                  │
│   // V2.0 fields preserved above                               │
│                                                                 │
│   // V3.1 additions:                                           │
│   "binding": {...},                                             │
│   "fence_token": int | null,                                   │
│   "checkpoint": {...} | null,                                  │
│   "context_summary": {...} | null,                             │
│   "dependency_metadata": {...},                                │
│   "cost": {...},                                               │
│   "ingestion_source": {...}                                    │
│ }                                                               │
│                                                                 │
│ registry_v3_1.json format:                                     │
│ {                                                               │
│   "slot_id": {                                                 │
│     // V2.0 fields preserved                                   │
│     "reset_cycle": {...} | null,                               │
│     "exhaustion_history": [...]                                │
│   }                                                             │
│ }                                                               │
├────────────────────────────────────────────────────────────────┤
│ Output: Complete V3.1 schema specification document            │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ LOOP 15: CONVERGENCE VALIDATION                                │
├────────────────────────────────────────────────────────────────┤
│ Final checks before execution:                                 │
│                                                                 │
│ ✅ Backward compatibility verified                             │
│ ✅ All V3.1 features have fields                               │
│ ✅ Migration script tested                                     │
│ ✅ Rollback procedure documented                               │
│ ✅ Schema scales 1→100→10K tasks                               │
│ ✅ No vendor lock-in introduced                                │
│ ✅ Future-proof for reasoning models                           │
│ ✅ Integration with Track A components tested                  │
│ ✅ MCP tools updated for V3.1                                  │
│ ✅ Orchestrator singleton pattern verified                     │
│                                                                 │
│ Unanimous agreement on design?                                 │
│ → YES: Lock in and execute                                     │
│ → NO: Re-run loops 1-14 with new constraints                   │
├────────────────────────────────────────────────────────────────┤
│ Output: GO/NO-GO decision + execution plan                     │
└────────────────────────────────────────────────────────────────┘
```

---

## 📊 DELIVERABLES (After Loops Converge)

### 1. tasks_v3_1_schema.json
Complete schema specification for V3.1 tasks

### 2. registry_v3_1_schema.json  
Complete schema specification for V3.1 slots

### 3. migrate_v2_to_v3_1.py
Migration script with validation + rollback

### 4. PHASE_1_VALIDATION_TESTS.py
Test suite for schema extension (20+ tests)

### 5. PHASE_1_CHECKLIST.md
5-line execution checklist

### 6. V3.1 MCP Tools
- brain_checkpoint_task()
- brain_resume_from_checkpoint()
- brain_generate_handoff_summary()

---

## ✅ SUCCESS CRITERIA (Locked)

**Before proceeding to Phase 2:**

- ✅ Design thinking loops completed (15 iterations minimum)
- ✅ Unanimous convergence on schema design
- ✅ V3.1 schema fully specified
- ✅ Backward compatibility with V2.0 verified
- ✅ Migration script implemented + tested
- ✅ Rollback procedure documented and tested
- ✅ All existing MCP tools still work
- ✅ Track A components (CRDT, Scheduler) integrate cleanly
- ✅ New checkpoint MCP tools working
- ✅ Schema scales 1→100→10K tasks
- ✅ Zero vendor lock-in
- ✅ Future-proof for reasoning models
- ✅ Cost tracking accurate
- ✅ Reset cycle management working

---

## 🚀 EXECUTION PROTOCOL

**When ready to execute Phase 1:**

1. Run design thinking loops (15 iterations, infinite until convergence)
2. Synthesize findings into final schema specification
3. Generate/update migration script
4. Create validation tests
5. Review schemas for completeness
6. Test migration on backup data
7. Validate with existing tools
8. Sign off on Phase 1
9. Move to Phase 2

**No iteration loops after design convergence**, just **ship the implementation**, verify it works, move forward.

---

## 🌟 NORTH STAR REMINDERS

✅ **Scale from day 1** - Schema works for 1→100→10K tasks (same code)  
✅ **No vendor lock-in** - Standard JSON, portable to any system  
✅ **Future-proof** - Ready for reasoning models, agentic systems  
✅ **Timeless standard** - Won't be legacy in 2 years  
✅ **Unanimous convergence** - Design until we agree  
✅ **One shot** - Nobody leaves until done  
✅ **Trillion-token thinking** - Think big, design forever  
✅ **Enterprise grade** - Production ready from day 1  

---

## 🔥 READY TO START DESIGN LOOPS?

When you say **"Start Phase 1 Design Loops"**, I'll:

1. Run all 15 design thinking loops (extended reasoning)
2. Synthesize into final V3.1 schema
3. Generate migration script
4. Create validation tests
5. Give you exact review checklist

**This will use maximum thinking tokens** - but the output will be production-ready schemas that work for the next decade.

**Track C = Parallel execution:** While design loops run, Track A Step 1.4 (AgentPool) can be implemented in parallel.

---

**NEXT:** Design loops execute NOW. Nobody leaves until NOP V3.1 orchestrates the global AI economy.

**STATUS: 🔒 MASTER PROMPT LOCKED - DESIGN LOOPS COMMENCING**
