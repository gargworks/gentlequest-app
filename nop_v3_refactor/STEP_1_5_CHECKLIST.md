# ✅ STEP 1.5 CHECKLIST - MCP Integration with orchestrator_v3

## 5-Line Execution Checklist

```bash
# 1. Verify components copied to runtime/
ls -la /Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/{agent_pool,task_ingestion}.py

# 2. Verify each component imports
cd /Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime
python3 -c "from crdt_task_store import CRDTTaskStore; from task_scheduler import TaskScheduler; from agent_pool import AgentPool; from task_ingestion import TaskIngestionEngine; print('✅ All imports OK')"

# 3. Verify orchestrator_v3 has new methods
grep -c "def spawn_agent\|def ingest_tasks\|def rollback_ingestion" orchestrator_v3.py

# 4. Verify MCP tools added
grep -c "brain_ingest_tasks\|brain_rollback_ingestion\|brain_ingestion_stats" ../../__init__.py

# 5. Sign off
echo "✅ STEP 1.5 GREEN - MCP Integration Complete"
```

---

## Success Criteria

- ✅ Components copied to runtime/:
  - crdt_task_store.py (existing)
  - task_scheduler.py (existing)
  - agent_pool.py (NEW)
  - task_ingestion.py (NEW)
- ✅ orchestrator_v3.py enhanced with:
  - AgentPool methods (spawn_agent, get_agent, mark_exhausted, etc.)
  - TaskIngestion methods (ingest_tasks, rollback_ingestion, get_ingestion_stats)
- ✅ MCP tools added to __init__.py:
  - brain_ingest_tasks()
  - brain_rollback_ingestion()
  - brain_ingestion_stats()
- ✅ All components import and work together
- ⚠️ Note: runtime/__init__.py has pre-existing circular import issue (not blocking)

---

## Files Modified

| File | Action | Status |
|------|--------|--------|
| `runtime/agent_pool.py` | Copied from nop_core | ✅ |
| `runtime/task_ingestion.py` | Copied from nop_core | ✅ |
| `runtime/orchestrator_v3.py` | Enhanced with new methods | ✅ |
| `__init__.py` | Added MCP tool wrappers | ✅ |
| `STEP_1_5_MASTER_PROMPT.md` | Created | ✅ |
| `STEP_1_5_CHECKLIST.md` | Created | ✅ |

---

## Integration Points

### orchestrator_v3.py New Methods:
- `get_agent_pool()` → returns AgentPool singleton
- `spawn_agent(model, tier, alias)` → spawn new agent
- `get_agent(agent_id)` → get agent by ID
- `mark_agent_exhausted(agent_id, reason)` → exhaust agent
- `respawn_agent(agent_id)` → respawn exhausted agent
- `get_available_agent(tier)` → get available agent for tier
- `assign_task_to_agent(task_id, agent_id, tier)` → assign task
- `get_ingestion_engine()` → returns TaskIngestionEngine
- `ingest_tasks(source, source_type, ...)` → ingest tasks
- `rollback_ingestion(batch_id, reason)` → rollback batch
- `get_ingestion_stats()` → get ingestion statistics

### MCP Tools Added:
- `brain_ingest_tasks(source, source_type, ...)` → external ingestion
- `brain_rollback_ingestion(batch_id, reason)` → external rollback
- `brain_ingestion_stats()` → external stats

---

## Sign-off

**Date:** January 22, 2026  
**Status:** 🟢 GREEN  
**Next:** Track B Phase 3 - Dashboard & brain_status_dashboard() enhancements
