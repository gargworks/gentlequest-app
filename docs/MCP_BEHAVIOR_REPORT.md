# MCP Server Nucleus: Real-World Behavior Report
> **Date:** December 27, 2025  
> **Source:** Live Claude Desktop testing  
> **Purpose:** Document what the MCP actually does vs. what users expect

---

## TL;DR

**What Nucleus IS:** A structured memory layer for LLMs  
**What Nucleus ISN'T (yet):** An agent orchestration runtime

The LLM (Claude) does the orchestration. Nucleus provides persistence.

---

## Observed Behavior

### Tools That Work
| Tool | Works? | Notes |
|------|--------|-------|
| `brain_list_artifacts` | ✅ | Lists all stored files |
| `brain_read_artifact` | ✅ | Reads any file in artifacts/ |
| `brain_write_artifact` | ✅ | Claude spontaneously creates docs |
| `brain_get_state` | ✅ | Returns current state.json |
| `brain_update_state` | ✅ | Persists new data |
| `brain_emit_event` | ✅ | Logs to events.jsonl |
| `brain_read_events` | ✅ | Returns event history |
| `brain_get_triggers` | ✅ | Shows trigger definitions |
| `brain_evaluate_triggers` | ✅ | Checks which would fire |
| `brain_trigger_agent` | ⚠️ | Emits event, but no actual agent spawns |

### Emergent Patterns
1. **Claude simulates agents** when it can't spawn them
2. **Claude writes specs** it can't execute (trigger files, agent docs)
3. **Hybrid mode** emerges: Claude acts as agent + stores to brain
4. **Voice analysis** from conversation → stored as context

---

## Gap Analysis

| User Expectation | Reality | Gap |
|------------------|---------|-----|
| "Activate writing coach" | Nothing happens | No execution daemon |
| Triggers fire automatically | Triggers are just data | Missing: trigger executor |
| Agents work independently | All Claude, no spawning | Missing: agent runtime |
| 6 agents exist | Claude role-plays them | They're prompts, not processes |

---

## Positioning Recommendation

### Current Honest Value Prop:
> "Persistent memory and context for AI conversations. Your LLM never forgets."

### Future Value Prop (requires Phase B):
> "Autonomous multi-agent orchestration with persistent memory."

---

## Action Items

1. **Messaging:** Don't oversell agent automation in v0.2
2. **Templates:** Add "writer" template based on this use case
3. **Cold start:** Improve empty-brain UX
4. **Phase B:** Consider trigger executor daemon

---

*For internal reference — update as more usage patterns emerge*
