# Integration Strategy: Build INTO Nucleus, Not Separate

## The Question
Should Autopilot features be:
- **Separate tools** (new scripts, standalone)?
- **Integrated into Nucleus MCP** (new brain tools)?

## The Answer: INTEGRATED

All features should be built into **Nucleus MCP v0.4.0** (or v1.0), not as separate tools.

---

## Why Integration (Not Separation)

### User's Concern from Part 4:
> "I don't know which features are from PyPI MCP vs local vs artifacts. There's no way to segregate the benefit."

**Creating separate tools would make this WORSE:**
- Render Poller script in `scripts/`?
- Feature Map as standalone CLI?
- Proof generator as separate Python package?
- CEO as yet another daemon?

**Result:** Even more confusion about what's compounding where.

---

## The Integration Plan

### Feature → Nucleus Location

| Feature | Where It Lives | How It's Used |
|:--------|:---------------|:--------------|
| **Render Poller** | New brain tools in Nucleus MCP | `brain_poll_render(service_id, commit_sha)` |
| **Feature Map** | `.brain/features.json` + brain tools | `brain_add_feature()`, `brain_list_features()` |
| **Proof System** | New brain tools | `brain_capture_thinking()`, `brain_generate_proof()` |
| **CEO Orchestrator** | Enhanced Synthesizer (from Protocol) | `brain_spawn_agent()`, `brain_escalate()` |

### Benefits:
1. ✅ **Single source of truth** - Everything in Nucleus MCP
2. ✅ **Clear attribution** - All features tagged as "Nucleus v0.4.0"
3. ✅ **No confusion** - Not scattered across scripts, tools, packages
4. ✅ **Easier to maintain** - One codebase
5. ✅ **Better UX** - One install (`pip install mcp-server-nucleus`), everything works

---

## Nucleus v0.4.0 Scope (Proposed)

### Core Features:
1. **Render Polling** - Background deploy validation
2. **Feature Map** - Living inventory of built features
3. **Proof System** - Thinking + URL + screenshot capture
4. **Session Management** - Pathway preservation (Satellite View foundation)

### CEO Orchestrator → v1.0
Reason: More complex, needs multi-agent spawn system. Build foundation first.

---

## Integration vs Separation Trade-offs

### If We Integrate (Recommended):
- ✅ Clean architecture
- ✅ Clear attribution
- ✅ Single install
- ⚠️ Larger v0.4.0 release (but manageable)

### If We Separate:
- ❌ Feature sprawl
- ❌ Attribution confusion (already a problem)
- ❌ Multiple installs/configs
- ✅ Can ship pieces faster (but at what cost?)

---

## Implementation Approach

### Incremental WITHIN Nucleus:
1. **v0.4.0-alpha:** Render Poller only (test integration pattern)
2. **v0.4.0-beta:** Add Feature Map
3. **v0.4.0-rc:** Add Proof System
4. **v0.4.0:** Full release

**Timeline (Agentic Hours):**
- Alpha: 2-4 hours
- Beta: +2 hours
- RC: +3-4 hours
- Polish/docs: +2 hours
- **Total: ~10-12 hours spread across sessions**

---

## Alignment with Existing Architecture

### From NUCLEUS_PROTOCOL_DRAFT.md:
> "New Tooling Required:
> - `brain_claim_task(task_id)`
> - `brain_delegate_task(description, target_role)`
> - `brain_heartbeat(thread_id)`"

**We're extending this with:**
- `brain_poll_render(service_id, commit_sha)`
- `brain_add_feature(name, description, test_steps)`
- `brain_capture_thinking(task, options, choice, reasoning)`
- `brain_generate_proof(task)`

**Same pattern. Consistent with existing design.**

---

## Answer to User's Question

**"Are these separate things or integrated?"**

→ **INTEGRATED into Nucleus MCP.** 

**"What is the right thing?"**

→ **Integration is right because:**
1. Prevents feature attribution confusion (current pain point)
2. Aligns with existing architecture (Protocol Draft)
3. Single source of truth
4. Easier to use and maintain

---

**Next: Should I create implementation_plan.md for Nucleus v0.4.0?**
