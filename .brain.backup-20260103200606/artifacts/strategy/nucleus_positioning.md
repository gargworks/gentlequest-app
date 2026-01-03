# Nucleus MCP: Product Positioning

> **Tagline:** Persistent memory for AI coding agents. Works everywhere, breaks nothing.

---

## The Problem

AI coding assistants (Copilot, Cursor, Windsurf) are powerful but **amnesiac**:
- Context resets every session
- No memory of past decisions
- Thread names auto-rename → identity lost
- No coordination between multiple agents/threads

**Solo founders juggle multiple IDEs and threads.** They need an agent that *remembers*.

---

## Nucleus Solution

A **file-based brain** (`.brain/`) that persists across:
- Sessions
- IDEs
- Thread renames
- Agent switches

```
.brain/
├── ledger/state.json      ← Current sprint, tasks, claims
├── meta/thread_registry.md ← Agent identity (stable)
├── memory/context.md       ← Company/project context
└── artifacts/              ← Research, ideas, reviews
```

---

## Competitive Moat

| Competitor | Limitation | Nucleus Advantage |
|:-----------|:-----------|:------------------|
| **Copilot/Cursor/Windsurf** | Single-session memory | Persists across sessions via `.brain/` |
| **LangChain/Pydantic AI** | Requires coding | No-code file protocol |
| **MCP Protocol (Anthropic)** | Just a spec | Opinionated implementation with templates |
| **Memory MCP servers** | Generic, no task mgmt | Sprint/task orchestration built-in |

**Unique Differentiator:**
> Persistent agent identity across IDE thread renames + task affinity routing via simple file protocol.

---

## Solo Founder Flexibility Matrix

| Configuration | Threads | IDEs | How Nucleus Helps |
|:--------------|:--------|:-----|:------------------|
| **a) Focused** | 1 | 1 | Universal Adaptor mode. One thread does all. Fast. |
| **b) Domain Split** | Many | 1 | Registry routes tasks by `preferred_role`. |
| **c) Multi-IDE** | Many | Many | `.brain/` syncs via Git. All IDEs read same state. |
| **d) Hybrid** | Any | Any | Works. `claimed_by_thread` prevents collisions. |

**Core Promise:** Pick any setup. Nothing breaks.

---

## Product Roadmap: Templates

| Template | Target User | Complexity | Key Files |
|:---------|:------------|:-----------|:----------|
| `solo` | Solo founder, indie dev | Low | `thread_registry.md` (1 file) |
| `team` | Agency, multi-dev | Medium | `+ agents/<thread_id>/identity.md` |
| `enterprise` | Org with audit needs | High | `+ claimed_by logs + audit trail` |

### Implementation Priority

1. **v0.3 (Now):** `solo` template with registry-first identity
2. **v0.4 (Next):** `team` template with per-thread identity files
3. **v0.5 (Later):** `enterprise` with audit logging + dashboard

---

## Target User Profile

**Primary:** Solo technical founders building AI-powered products
- Uses 1-3 IDEs (Antigravity, Windsurf, Cursor)
- Wants agent to "remember" across sessions
- Values speed over ceremony
- Will pay for cloud sync later

**Secondary (Future):** Small agencies, dev teams
- Need agent separation by specialty
- Want audit trail for client work

---

## Go-to-Market

1. **Free tier:** Local-only, `solo` template
2. **Pro tier ($X/mo):** Cloud sync, `team` template, priority support
3. **Enterprise:** Custom, `enterprise` template, SSO, audit logs

---

## Key Messages

**For Solo Founders:**
> "Your AI assistant finally remembers what you're building."

**For Teams:**
> "Multi-agent orchestration without the infrastructure."

**Technical Hook:**
> "MCP + `.brain/` = persistent context that survives IDE chaos."
