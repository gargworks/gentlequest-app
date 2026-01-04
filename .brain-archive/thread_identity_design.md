# Thread Identity System Design

> **Problem:** Thread names auto-rename in Antigravity/Windsurf. Users can't tell "which agent is which." Agents can't self-identify what tasks suit them.

---

## Core Insight

**Thread_id is the ONLY stable identifier.** Thread name, label, title - all ephemeral.

```
Thread Name: "Fixing Deployment" → "Streamlining Tasks" → "Queue Cleanup"
Thread ID:   7c654df4-b83e-43f9-8620-f15868ec39d1  ← STABLE
```

---

## Proposed Architecture

```
.brain/
  agents/
    7c654df4-b83e.../           ← keyed by thread_id
      identity.md               ← "I am Lead Systems Architect"
      capabilities.json         ← ["infrastructure", "mcp", "nucleus"]
    853a0b7e-9052.../
      identity.md
      capabilities.json
  ledger/
    state.json
      tasks: [
        {
          "id": "task-001",
          "description": "Fix API endpoint",
          "category": ["code", "backend"],
          "preferred_agent_role": "Developer",  ← soft affinity
          "claimed_by_thread": null | "<thread_id>"
        }
      ]
```

---

## Agent Activation Protocol

When a thread wakes up (user sends first message):

1. **Read thread_id** from system context (`.gemini` path or MCP state)
2. **Lookup identity** in `.brain/agents/<thread_id>/identity.md`
3. **Self-announce** to user:
   ```
   🤖 **Lead Systems Architect** | Focus: infrastructure, MCP, nucleus
   📋 Pending tasks matching my specialty: 2
   ```
4. **Filter tasks** by capability overlap

---

## Implementation Phases

### Phase 1: Self-Identification (Now)
- Create `.brain/agents/<thread_id>/identity.md` for active threads
- Agent reads and prints banner on activation
- User always knows which agent they're talking to

### Phase 2: Task Affinity Matching (Next Sprint)
- Add `category` and `preferred_agent_role` to tasks
- Agent filters queue by capability match
- `claimed_by_thread` provides audit trail

### Phase 3: Smart Routing (Future)
- Agent detects "wrong thread" for task type
- Suggests: "This is a code task. Hand off to Developer thread?"
- Optional auto-redirect via Nucleus IPC

---

## User Experience

| Scenario | Before | After |
|:---------|:-------|:------|
| User opens random thread | "What was this for again?" | "🤖 I am Developer. Ready for code tasks." |
| User asks about infra in Developer thread | Agent struggles | Agent suggests redirect |
| Reviewing task history | "Who did this?" | `claimed_by_thread` shows ID |

---

## Files to Create

| File | Purpose |
|:-----|:--------|
| `.brain/agents/7c654df4-.../identity.md` | Lead Systems Architect identity |
| `.brain/agents/853a0b7e-.../identity.md` | Synthesizer identity |
| `.brain/agents/482f5f52-.../identity.md` | Researcher identity |

---

## Nucleus MCP Product Differentiator

> **Agent identity persistence across IDE renaming.** Users trust the banner, not the thread name.
