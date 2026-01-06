# Open Source vs. Proprietary: The Nucleus IP Strategy

> **MDR_008 Implementation Document**
> **Status:** ACTIVE POLICY
> **Last Updated:** 2026-01-06

---

## The Strategic Framework

The moat is NOT the code. The moat IS the Context (Brain) + Orchestration (Workflow).

---

## What is OPEN SOURCE (NAR)

The Nucleus Agent Runtime (NAR) is open-sourceable:

| Component | Path | Status |
|:----------|:-----|:-------|
| **Runtime Engine** | `mcp_server_nucleus/runtime/` | ✅ Open |
| **Capability Base** | `mcp_server_nucleus/runtime/capabilities/base.py` | ✅ Open |
| **Context Factory** | `mcp_server_nucleus/runtime/factory.py` | ✅ Open |
| **Example Capabilities** | `render_ops.py`, `brain_ops.py` | ✅ Open |
| **CLI Framework** | `mcp_server_nucleus/cli.py` | ✅ Open |
| **Example Schemas** | `commitment_ledger.py` (schema only) | ✅ Open |
| **PyPI Package** | `mcp-server-nucleus` | ✅ Open |

---

## What is PROPRIETARY (Brain)

Your personal data and orchestration logic stays private:

| Component | Path | Status | Reason |
|:----------|:-----|:-------|:-------|
| **Brain Directory** | `.brain/` | 🔒 Private | Contains personal context |
| **Commitments** | `.brain/commitments/` | 🔒 Private | Your task history |
| **Patterns** | `.brain/patterns/` | 🔒 Private | Learned behaviors |
| **Features** | `.brain/features/` | 🔒 Private | Product roadmap |
| **Strategy** | `.brain/strategy/MDR_*` | 🔒 Private | IP and moat documents |
| **Sessions** | `.brain/sessions/` | 🔒 Private | Conversation context |
| **Triggers** | `.brain/triggers.json` | 🔒 Private | Workflow automation |

---

## Export Policy

When sharing the codebase publicly:

### INCLUDE (Open Source)
```
mcp-server-nucleus/
├── src/mcp_server_nucleus/
│   ├── __init__.py          # Core functions
│   ├── cli.py                # CLI
│   ├── commitment_ledger.py  # Schema & API
│   └── runtime/              # NAR Engine
├── pyproject.toml
└── README.md
```

### EXCLUDE (Private)
```
.brain/                       # Never commit
scripts/telegram_briefing.py  # Contains chat IDs
*.env                         # Secrets
*.json (in .brain/)           # Personal data
MDR_*.md                      # Strategic IP
```

---

## .gitignore Rules

```gitignore
# MDR_008: Private Brain
.brain/
!.brain/.gitkeep

# Secrets
*.env
.env*

# Strategy (Private IP)
# (These should live in .brain/strategy/ anyway)
MDR_*.md

# Personal data
feedback_log.json
ledger.json
**/sessions/*
```

---

## .brainignore (New File)

For exports that should strip private content:

```brainignore
# Entries listed here are excluded from brain exports
commitments/
patterns/learned_patterns.json
sessions/
features/
strategy/MDR_001_FOUNDATION/
memory/
```

---

## The Philosophy

> "They can copy the code (NAR). They cannot copy the Context (The Brain). And an Agent without Context is just a tool. An Agent with Context is a Partner."

**Give away the engine. Keep the memory.**
