# Nucleus v0.3.0: Solo Templat# Nucleus Implementation Plan

## 1. Safety & Release (v0.2.6) ✅
- [x] Auto-Backup before overwrite
- [x] Stricter Active Brain detection
- [x] Released to PyPI

## 2. Orchestration Automation (The Autopilot) 🚧
**Objective:** Replace manual JSON editing with an intelligent background daemon.

### Design: The "Client-Side" Autopilot
*Principle: Server = State (Data), Autopilot = Compute (LLM).*

- **Component:** `scripts/autopilot.py`
- **Dependencies:** `mcp`, `anthropic` (or `openai`)
- **Logic:**
  1.  Watch `events.jsonl` for changes (Event-Driven).
  2.  If `type == "user_input"`, waking Synthesizer.
  3.  Inject Context: `state.json` + `thread_registry.md`.
  4.  Execute Tool Use: `brain_delegate_task`.

### Implementation Steps
1.  Create `scripts/autopilot.py`.
2.  Implement efficient event polling (cursor-based).
3.  Add "Safety Switch" (Human-in-the-loop mode).

## 3. Thread Identity System ✅
- [x] Registry Schema
- [x] Ledger Task Affinityle:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/cli.py)

**Changes:**
1. Add `--template` CLI argument (default: `default`)
2. Create `SOLO_TEMPLATE` constants (minimal structure)
3. Route `init_brain()` to template-specific logic

**Solo Template Structure:**
```
.brain/
├── ledger/
│   └── state.json         ← Simplified
├── meta/
│   └── thread_registry.md ← NEW: Agent identity
└── memory/
    └── context.md         ← Project context
```

---

### [MODIFY] [pyproject.toml](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/pyproject.toml)

- Bump version: `0.2.4` → `0.3.0`

---

### [MODIFY] [README.md](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/README.md)

- Add template usage section
- Document `nucleus-init --template=solo`

---

### [MODIFY] [CHANGELOG.md](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/CHANGELOG.md)

- Add v0.3.0 release notes

---

## Solo Template Files

**state.json (Simplified):**
```json
{
  "version": "1.0.0",
  "mode": "solo",
  "current_focus": "Getting started",
  "tasks": []
}
```

**thread_registry.md:**
```markdown
# Thread Registry

> **Protocol:** Agents check this file on activation to know their role.

| Thread ID | Role | Focus |
|:----------|:-----|:------|
| *(Add your threads here)* | | |

## How to Use
1. Find your thread ID in your IDE's artifact path
2. Add a row to this table
3. Agent will self-identify on next activation
```

---

## Verification Plan

1. **Local Test:**
   ```bash
   cd mcp-server-nucleus
   pip install -e .
   nucleus-init --template=solo
   ```

2. **Check Files Created:**
   - `.brain/ledger/state.json` exists
   - `.brain/meta/thread_registry.md` exists
   - No `agents/` folder (solo mode = registry only)

3. **Publish:**
   ```bash
   hatch build
   twine upload dist/*
   ```

---

## User Review Required

> [!IMPORTANT]
> Please confirm:
> 1. Is the `solo` template structure correct?
> 2. Should `default` template remain unchanged (current behavior)?
