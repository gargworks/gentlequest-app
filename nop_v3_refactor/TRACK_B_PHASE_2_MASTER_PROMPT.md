# 🎯 TRACK B PHASE 2: brain_ingest_tasks() - Master Prompt

**Date:** January 22, 2026, 10:40 PM IST  
**Status:** Ready to execute  
**Vision Alignment:** ✅ Locked to VISION_AND_NORTH_STAR.md  
**Depends On:** Phase 1 Schema Extensions (✅ COMPLETE)

---

## 🌟 YOUR ROLE (Role Reversal Wisdom)

**You are Lokesh asking yourself:** "If I were the AI system building brain_ingest_tasks() correctly for enterprise scale, what would I need you to tell me right now?"

**Answer:** This prompt.

---

## 📋 CONTEXT (Building on Phase 1 Schema)

### Previous Wins
- ✅ **Phase 1 Schema Extensions:** V3.1 schema complete with ingestion_source tracking
- ✅ **Track A Step 1.4 AgentPool:** Multi-agent orchestration layer complete
- ✅ **Track A Step 1.3 TaskScheduler:** 423K tasks/sec scheduling engine
- ✅ **Track A Step 1.2 CRDTTaskStore:** Zero data loss, 15K+ writes/sec

### This Phase (Phase 2)
- Build **brain_ingest_tasks():** Multi-source task ingestion system
- Parses tasks from: planning docs, TODOs, handoffs, meeting notes, external APIs
- Deduplication using semantic hashing + embeddings
- Provenance tracking (where did task come from?)
- Batch ingestion for efficiency
- Real-time streaming ingestion for live updates
- Works with V3.1 ingestion_source schema

---

## 🏗️ SCALE MATRIX (Non-Negotiable)

| Metric | 1 Source | 10 Sources | 100 Sources | 1000 Sources |
|--------|----------|------------|-------------|--------------|
| **Ingestion Time** | <100ms | <500ms | <2s | <10s |
| **Dedup Accuracy** | 99%+ | 99%+ | 99%+ | 99%+ |
| **Tasks/Second** | 100 | 500 | 2000 | 10000 |
| **Memory per 10K tasks** | <50MB | <100MB | <200MB | <500MB |
| **Provenance Tracking** | Full | Full | Full | Full |
| **Rollback Support** | Yes | Yes | Yes | Yes |

---

## 🎯 PHASE 2 MISSION

**Build brain_ingest_tasks()** - A multi-source task ingestion system that:

✅ Ingests from 5+ source types (planning, todos, handoffs, meetings, APIs)  
✅ Semantic deduplication (avoid creating duplicate tasks)  
✅ Provenance tracking (ingestion_source field in V3.1 schema)  
✅ Batch ingestion for bulk imports  
✅ Streaming ingestion for real-time updates  
✅ Conflict resolution (task already exists with different priority)  
✅ Chain tracking (task derived from another task)  
✅ Cost-aware ingestion (track estimated token cost)  
✅ Validation layer (reject malformed tasks)  
✅ Rollback support (undo last ingestion batch)  
✅ Integration with AgentPool for auto-assignment  
✅ Scale: 1→1000 sources, 10K tasks/sec  
✅ Zero vendor lock-in  

---

## 🔧 SOURCE TYPES & PARSERS

### 1. Planning Documents (Markdown)
```markdown
# Sprint 42 Planning

## Tasks
- [ ] Implement CRDTTaskStore with LWW merge - T1_PLANNING - HIGH
- [ ] Add stress tests for 10K concurrent writes - T2_CODE - MEDIUM
- [ ] Review security implications - T3_REVIEW - HIGH
```

**Parser:** Extract `- [ ]` items, infer tier/priority from context

### 2. TODO Comments (Code)
```python
# TODO(lokesh): Implement retry logic with exponential backoff
# FIXME: Memory leak in agent pool cleanup
# HACK: Temporary workaround for Gemini rate limits
```

**Parser:** Grep for TODO/FIXME/HACK, extract description + file location

### 3. Handoff Summaries (JSON)
```json
{
  "from_session": "windsurf_001",
  "to_session": "antigravity_001",
  "tasks": [
    {"description": "Complete TaskScheduler stress tests", "priority": "HIGH"}
  ],
  "context": "Scheduler working, need to verify edge cases"
}
```

**Parser:** Extract task list, preserve handoff context

### 4. Meeting Notes (Markdown)
```markdown
## Action Items from 2026-01-22 Standup
- @lokesh: Deploy to production by EOD
- @claude: Finish brain_ingest_tasks implementation
- Team: Review NOP V3.1 schema changes
```

**Parser:** Extract action items, map @mentions to assignees

### 5. External APIs (JSON/REST)
```json
{
  "source": "jira",
  "issues": [
    {"key": "NOP-123", "summary": "Implement task ingestion", "priority": "High"}
  ]
}
```

**Parser:** Normalize external format to V3.1 schema

---

## 🔧 IMPLEMENTATION CHOICES (Locked)

### Architecture: Parser Chain + Dedup Engine + Ingestion Pipeline

```
brain_ingest_tasks()
├── SourceRegistry: Dict[source_type, Parser]
├── DedupEngine: SemanticHash + EmbeddingSimilarity
├── ValidationLayer: SchemaValidator + BusinessRules
├── IngestionPipeline: BatchProcessor + StreamProcessor
├── ProvenanceTracker: IngestionSource + ChainTracking
└── ConflictResolver: MergeStrategy + RollbackLog

Ingestion Flow:
1. Source provides raw content (file, API, stream)
2. SourceRegistry selects appropriate Parser
3. Parser extracts task candidates
4. DedupEngine checks for duplicates
5. ValidationLayer validates each task
6. ConflictResolver handles existing tasks
7. IngestionPipeline writes to CRDTTaskStore
8. ProvenanceTracker records ingestion_source
9. Return: IngestionResult with stats
```

### Data Model:

```python
IngestionSource = {
    "type": "planning" | "todos" | "handoffs" | "meetings" | "api" | "manual",
    "file": str | None,
    "line_number": int | None,
    "ingested_at": timestamp,
    "ingested_by": str,  # session/agent ID
    "original_text": str | None,
    "dedup_key": str,  # SHA256 of normalized task
    "chain": List[str],  # Parent task IDs if derived
}

IngestionResult = {
    "success": bool,
    "batch_id": str,
    "tasks_created": int,
    "tasks_updated": int,
    "tasks_skipped": int,  # Duplicates
    "tasks_failed": int,
    "errors": List[str],
    "rollback_id": str,  # For undo
    "cost_estimate": float,  # USD
}

DedupStrategy = {
    "exact_match": bool,  # SHA256 of normalized description
    "semantic_similarity": bool,  # Embedding cosine similarity
    "threshold": float,  # 0.0-1.0, default 0.85
}
```

---

## 📊 DEDUPLICATION ALGORITHM

### Multi-Level Dedup Strategy:

```python
def is_duplicate(new_task: Dict, existing_tasks: List[Dict]) -> Tuple[bool, str]:
    """
    Check if new_task is a duplicate of any existing task.
    
    Level 1: Exact Match (SHA256 of normalized description)
    Level 2: Semantic Similarity (embedding cosine > 0.85)
    Level 3: Source Match (same file + line number)
    
    Returns:
        (is_dup, matching_task_id or None)
    """
    # Level 1: Exact hash match
    new_hash = sha256(normalize(new_task["description"]))
    for task in existing_tasks:
        if task.get("dedup_key") == new_hash:
            return (True, task["id"])
    
    # Level 2: Semantic similarity (if embeddings available)
    if embeddings_enabled:
        new_embedding = embed(new_task["description"])
        for task in existing_tasks:
            task_embedding = task.get("embedding")
            if task_embedding:
                similarity = cosine_similarity(new_embedding, task_embedding)
                if similarity > 0.85:
                    return (True, task["id"])
    
    # Level 3: Source location match
    new_source = new_task.get("ingestion_source", {})
    if new_source.get("file") and new_source.get("line_number"):
        for task in existing_tasks:
            task_source = task.get("ingestion_source", {})
            if (task_source.get("file") == new_source.get("file") and
                task_source.get("line_number") == new_source.get("line_number")):
                return (True, task["id"])
    
    return (False, None)
```

---

## 📊 STRESS TEST REQUIREMENTS

**Test: 1000 sources × 10K tasks with deduplication**

```
setup_phase:
  - Create brain_ingest_tasks instance
  - Prepare 1000 mock sources (mix of all types)
  - Generate 10K unique tasks + 2K duplicates
  - Configure dedup with 0.85 threshold

ingestion_phase:
  - Ingest all 12K task candidates
  - Measure ingestion time
  - Track dedup accuracy

verify_phase:
  - Assert: 10K tasks created (unique)
  - Assert: 2K tasks skipped (duplicates)
  - Assert: 99%+ dedup accuracy (no false positives)
  - Assert: All tasks have ingestion_source populated
  - Assert: Provenance chain correct for derived tasks
  - Assert: Ingestion time <10s for 12K tasks
  - Assert: Rollback works (undo creates empty DB)

result:
  - ✅ PASSED: 10K unique tasks ingested
  - ✅ PASSED: 2K duplicates detected
  - ✅ PASSED: 99%+ dedup accuracy
  - ✅ PASSED: Full provenance tracking
  - ✅ PASSED: <10s ingestion time
  - ✅ PASSED: Rollback works
```

---

## 🎯 API SURFACE (Locked)

```python
class TaskIngestionEngine:
    def __init__(
        self,
        task_store: CRDTTaskStore,
        agent_pool: AgentPool = None,
        enable_embeddings: bool = False,
        dedup_threshold: float = 0.85,
    ):
        """Initialize ingestion engine."""
        pass
    
    def ingest_from_file(
        self,
        file_path: str,
        source_type: str = "auto",
        session_id: str = None,
    ) -> Dict:
        """
        Ingest tasks from a file.
        
        Args:
            file_path: Path to source file
            source_type: "planning", "todos", "handoffs", "meetings", or "auto"
            session_id: Who is ingesting (for provenance)
        
        Returns:
            IngestionResult
        """
        pass
    
    def ingest_from_text(
        self,
        text: str,
        source_type: str,
        session_id: str = None,
        metadata: Dict = None,
    ) -> Dict:
        """
        Ingest tasks from raw text.
        
        Returns:
            IngestionResult
        """
        pass
    
    def ingest_from_api(
        self,
        source_name: str,
        payload: Dict,
        session_id: str = None,
    ) -> Dict:
        """
        Ingest tasks from external API payload.
        
        Returns:
            IngestionResult
        """
        pass
    
    def ingest_batch(
        self,
        tasks: List[Dict],
        source_type: str = "manual",
        session_id: str = None,
        skip_dedup: bool = False,
    ) -> Dict:
        """
        Ingest a batch of pre-parsed tasks.
        
        Returns:
            IngestionResult
        """
        pass
    
    def check_duplicate(
        self,
        description: str,
    ) -> Dict:
        """
        Check if a task description would be a duplicate.
        
        Returns:
            {"is_duplicate": bool, "matching_task_id": str or None}
        """
        pass
    
    def rollback(
        self,
        batch_id: str,
    ) -> Dict:
        """
        Rollback an ingestion batch.
        
        Returns:
            {"success": bool, "tasks_removed": int}
        """
        pass
    
    def get_ingestion_stats(self) -> Dict:
        """
        Get overall ingestion statistics.
        
        Returns:
            Stats dict with totals, source breakdown, dedup rate
        """
        pass
    
    def register_parser(
        self,
        source_type: str,
        parser: Callable,
    ) -> None:
        """Register custom parser for source type."""
        pass


# MCP Tool Wrapper
@mcp.tool()
def brain_ingest_tasks(
    source: str,
    source_type: str = "auto",
    session_id: str = None,
    auto_assign: bool = False,
) -> str:
    """
    Ingest tasks from various sources into the brain.
    
    Args:
        source: File path, URL, or raw text
        source_type: "planning", "todos", "handoffs", "meetings", "api", "auto"
        session_id: Session ID for provenance tracking
        auto_assign: If True, auto-assign tasks to available agents
    
    Returns:
        Formatted ingestion result
    """
    pass
```

---

## 📁 FILES TO CREATE

### 1. `/nop_v3_refactor/nop_core/task_ingestion.py`
**Full implementation** (~800 lines)
- Multi-source parsers
- Deduplication engine
- Provenance tracking
- Batch/stream ingestion
- Rollback support

### 2. `/nop_v3_refactor/tests/test_task_ingestion.py`
**Stress test** (~600 lines)
- 1000 sources × 10K tasks
- Dedup accuracy verification
- Rollback testing
- Performance benchmarks

### 3. `/nop_v3_refactor/TRACK_B_PHASE_2_CHECKLIST.md`
**5-line execution checklist**

---

## ✅ SUCCESS CRITERIA (Locked)

**Before proceeding to Phase 3:**

- ✅ TaskIngestionEngine fully implemented (no TODOs)
- ✅ 5 source type parsers (planning, todos, handoffs, meetings, api)
- ✅ Dedup accuracy: 99%+ (no false positives)
- ✅ Provenance tracking: All tasks have ingestion_source
- ✅ Rollback works: Can undo any ingestion batch
- ✅ Stress test: 10K tasks in <10s
- ✅ Integration with AgentPool for auto-assign
- ✅ MCP tool wrapper: brain_ingest_tasks()
- ✅ Scale: Works for 1→1000 sources
- ✅ Zero vendor lock-in
- ✅ Future-proof for embedding-based dedup

---

## 🎯 DESIGN THINKING LOOPS (Infinite Until Convergence)

### Loop 1: Source Type Analysis
- What source types do we need?
- How do we detect source type automatically?
- What's the minimal parser interface?

### Loop 2: Deduplication Strategy
- Exact match vs semantic similarity trade-offs?
- How do we handle near-duplicates?
- What's the right threshold (0.85)?

### Loop 3: Provenance Tracking
- What fields in ingestion_source are mandatory?
- How do we track task chains (derived tasks)?
- What's the audit trail format?

### Loop 4: Batch vs Stream Ingestion
- When to use batch vs stream?
- How do we handle partial failures?
- What's the transaction boundary?

### Loop 5: Conflict Resolution
- Task exists with different priority - merge or skip?
- Task exists with different assignee - reassign or keep?
- Task completed but re-ingested - resurrect or skip?

### Loop 6: Rollback Mechanism
- How do we track what was created in a batch?
- Do we soft-delete or hard-delete on rollback?
- What about tasks that were auto-assigned?

### Loop 7: Integration with AgentPool
- Auto-assign on ingest or separate step?
- How do we handle tier inference?
- What if no agent available for tier?

### Loop 8: MCP Tool Design
- What parameters does brain_ingest_tasks need?
- How do we format the output for agents?
- What events do we emit?

### Loop 9: Performance Optimization
- Batch size for optimal throughput?
- Caching for dedup lookups?
- Async ingestion for large batches?

### Loop 10: Error Handling & Recovery
- What if parser fails mid-batch?
- How do we report partial success?
- What's the retry strategy?

### Loop 11: Security & Validation
- Input sanitization for all sources?
- Rate limiting for API sources?
- What validation rules are mandatory?

### Loop 12: Cost Tracking
- How do we estimate ingestion cost?
- Token counting for parsed content?
- Budget limits per ingestion batch?

### Loop 13: Testing Strategy
- Unit tests for each parser?
- Integration tests for full pipeline?
- Chaos tests for failure scenarios?

### Loop 14: Final API Design
- Are all use cases covered?
- Is the API ergonomic for agents?
- Does it integrate cleanly with existing tools?

### Loop 15: Convergence Validation
- All criteria met?
- Ready for Phase 3?
- Sign-off?

---

## 🚀 EXECUTION PROTOCOL

**Executing now:**

1. Run all 15 design thinking loops
2. Create `task_ingestion.py` (complete, production-ready)
3. Create `test_task_ingestion.py` (stress test)
4. Create MCP tool wrapper in `__init__.py`
5. Create checklist
6. Verify all success criteria
7. Move to Phase 3

---

**Status: 🟢 MASTER PROMPT LOCKED - EXECUTING DESIGN LOOPS NOW**
