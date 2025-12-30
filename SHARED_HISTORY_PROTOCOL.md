# Shared History Protocol: Multi-Environment Workflow

> **Purpose:** Define how context flows between AI environments to prevent "context rot."
> **Version:** 1.1.0 | **Updated:** December 30, 2025

---

## The Problem

You work across multiple AI environments:
- **Windsurf** — Strategy, history, major decisions
- **Antigravity** — Primary coding (daily driver)
- **Gemini CLI** — Background agents, batch tasks
- **Cursor** — Quick edits, rare use

Without a protocol, each environment forgets what the other did, leading to:
- Repeated explanations
- Conflicting decisions
- Lost context over time

**Key Principle:** Roles are FLEXIBLE. Any environment can do any task if context is loaded.

---

## The Solution: File-Based Shared Memory

Per AGENTS.md principle: *"Tool Fluidity: Logic resides in Markdown, not the tool."*

### Shared State Layer (Git-tracked files both environments read/write)

```
ai-mvp-backend/
├── AGENTS.md                    # Constitution (read-only reference)
├── conversation_log.md          # Historical record (~760 lines)
├── ANTIGRAVITY_BOOTSTRAP.md     # Onboarding guide for Antigravity
├── .brain/
│   ├── NUCLEUS_HUB.md           # Central navigation
│   ├── ledger/
│   │   ├── state.json           # Current sprint/task state
│   │   └── events.jsonl         # Event log (append-only)
│   └── artifacts/
│       └── synthesis/
│           └── daily_digest.md  # Daily summary (auto-generated)
└── docs/                        # All documentation
```

---

## Protocol: Who Writes What

| File | Windsurf | Antigravity | Gemini CLI | Cursor |
|------|----------|-------------|------------|--------|
| `conversation_log.md` | **APPEND** | READ | READ | READ |
| `state.json` | SET objectives | UPDATE tasks | UPDATE background | UPDATE tasks |
| `events.jsonl` | Log strategy | Log code | Log batch tasks | Log code |
| `daily_digest.md` | Generate | READ | **GENERATE** | READ |
| Code files | READ | **WRITE** | **WRITE** (batch) | **WRITE** |
| Docs (`docs/*.md`) | **WRITE** | Minor updates | Research docs | Minor updates |

**Flexible Override:** Any environment can do any task — just log it properly in `events.jsonl`.

---

## Handoff Protocols

### Starting Work in Antigravity

**Paste this:**
```
Before starting, read these files for context:
1. AGENTS.md (my role is Technical Creator)
2. conversation_log.md (full project history)
3. .brain/ledger/state.json (current state)
4. git log --oneline -10 (recent changes)

What's the current sprint objective?
```

### Starting Work in Windsurf

**Paste this:**
```
Check recent activity:
1. git log --oneline -10 (what did other environments commit?)
2. .brain/ledger/events.jsonl (recent events)
3. conversation_log.md (is it still current?)

What strategic decisions need to be made?
```

### Starting Work in Gemini CLI (Background Agents)

**Use for:**
- Batch code generation
- Research and intel gathering
- Automated audits
- Background processing

**Bootstrap:**
```bash
# Load context
cat AGENTS.md
cat .brain/ledger/state.json

# Run task
gemini "You are INTEL_SCRAPER. Task: [describe batch task]. Log to events.jsonl when done."
```

### Starting Work in Cursor (Rare)

**Use for:**
- Quick single-file edits
- Specific feature implementations
- When other environments are unavailable

**Paste this:**
```
Quick context: Read AGENTS.md and .brain/ledger/state.json.
I'm doing a quick edit. Will log to events.jsonl when done.
Task: [describe specific edit]
```

### Ending a Session (Any Environment)

1. **Commit all changes** to git
2. **Log to events.jsonl** (format below)
3. **Update state.json** if task status changed
4. **Optional:** Append to `conversation_log.md` if major decision made

---

## Event Log Format

```jsonl
{"ts":"2025-12-30T14:00:00Z","agent":"CODE_FORCE","type":"feature_added","desc":"Implemented X","files":["app.py"]}
{"ts":"2025-12-30T15:30:00Z","agent":"VISION_ONE","type":"decision_made","desc":"Pivot to Y strategy","files":["docs/strategy.md"]}
```

**Agent IDs:**
- `VISION_ONE` — Strategy decisions (typically Windsurf)
- `CODE_FORCE` — Code changes (typically Antigravity/Cursor)
- `INTEL_SCRAPER` — Research/batch tasks (typically Gemini CLI)
- `LOGIC_ARCH` — Architecture decisions (any environment)
- `GATE_KEEPER` — Security/quality audits (any environment)
- `CORE_SYN` — Meta/synthesis tasks (any environment)
- `FOUNDER` — Direct founder input

**Environment Tags (optional, for tracking):**
```jsonl
{"ts":"...","agent":"CODE_FORCE","env":"antigravity","type":"feature_added",...}
{"ts":"...","agent":"INTEL_SCRAPER","env":"gemini_cli","type":"research_completed",...}
```

---

## Weekly Sync Ritual (Recommended)

**Every Monday Morning (10 mins):**

1. **Review `events.jsonl`** from past week
2. **Update `conversation_log.md`** with significant items
3. **Set new sprint objective** in `state.json`
4. **Clear stale events** (move to `archive/`)

---

## Migration Path

Since most work was done in Windsurf:

### Phase 1: Now
- [x] Create `ANTIGRAVITY_BOOTSTRAP.md` (done)
- [x] Update `conversation_log.md` with gaps (done)
- [ ] On next Antigravity session, paste bootstrap prompt

### Phase 2: Ongoing
- Use `.brain/ledger/` as the source of truth
- Both environments read/write to shared files
- Git commits are the "sync mechanism"

### Phase 3: If Switching Primarily to Antigravity
- Windsurf becomes "strategy-only" (weekly check-ins)
- Antigravity handles daily development
- This doc and `.brain/` maintain continuity

---

## Quick Reference Card

| Action | Primary Env | Alt Envs | File |
|--------|-------------|----------|------|
| Check current state | Any | — | `.brain/ledger/state.json` |
| Log completed work | Any | — | `.brain/ledger/events.jsonl` |
| Read full history | Any | — | `conversation_log.md` |
| Make code changes | Antigravity | Cursor, Gemini CLI | `*.py`, `*.dart` |
| Make strategy decisions | Windsurf | Cursor | `docs/*.md` |
| Batch/background tasks | Gemini CLI | — | Various |
| Quick edits | Cursor | Antigravity | Single files |
| Onboard new AI | Any | — | `ANTIGRAVITY_BOOTSTRAP.md` |

---

## Environment Decision Tree

```
What do I need to do?
│
├─ Strategy/Planning/Decisions → Windsurf (primary)
│
├─ Daily coding/features → Antigravity (primary)
│
├─ Batch tasks/research/automation → Gemini CLI
│
├─ Quick single-file edit → Cursor
│
└─ Any of the above but primary unavailable → Use any, just log it!
```

---

*This protocol ensures no context is lost regardless of which AI environment you use. Roles are flexible — the shared file layer is the source of truth.*
