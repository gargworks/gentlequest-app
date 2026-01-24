# 🧠 Nucleus MCP Server

[![PyPI version](https://badge.fury.io/py/mcp-server-nucleus.svg)](https://badge.fury.io/py/mcp-server-nucleus)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **The Operating System for AI Agents** — Stop re-explaining your project to Claude every time you open a new chat. Give your agents a persistent **Operational Memory**.

`mcp-server-nucleus` is an open-source MCP server that turns your AI assistants into a coordinated team. It provides **110+ MCP tools** for task orchestration, multi-agent swarms, session persistence, and enterprise-grade decision auditing — all stored in a local `.brain/` directory you own.

## 🏛️ The Trinity Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  INTERFACE (Open)     │  ENGINE (Local)    │  BRAIN (Yours) │
│  Python CLI           │  110+ MCP Tools    │  .brain/       │
│  pip install          │  Task Orchestration│  Your Data     │
│  MIT License          │  Swarm Coordination│  Zero Cloud    │
└─────────────────────────────────────────────────────────────┘
```

## ✨ Features

- **110+ MCP Tools** for agent orchestration, swarms, sessions, and federation
- **V3.1 Task Engine** — Priority queue, skill routing, dependency DAG, slot pooling
- **Multi-Agent Swarms** — Spawn recursive agent hierarchies for complex missions
- **Session Persistence** — Save/resume work across conversations
- **Health Monitoring** — Built-in `brain_health()` and `brain_version()` endpoints
- **Event-Driven** — Full event ledger with `DecisionMade` audit trail
- **Zero-Knowledge Default** — Your data stays local. No cloud required.

## 🚀 Quick Start (2 Minutes)

### 1. Install
```bash
pip install mcp-server-nucleus
```

### 2. Initialize (Smart Config)
The `nucleus-init` command automatically detects your system and configures Claude Desktop for you.

```bash
# Create your .brain/ and auto-configure Claude Desktop
nucleus-init
```

### 3. Ask Claude
Restart Claude Desktop and try:
> *"Use the cold_start prompt from nucleus to see our current sprint focus."*

> **v0.2.2+**: Smart Init automatically detects Claude Desktop and adds the config for you!

### Configuration (Claude Desktop)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nucleus": {
      "command": "python3",
      "args": ["-m", "mcp_server_nucleus"],
      "env": {
        "NUCLEAR_BRAIN_PATH": "/path/to/your/.brain"
      }
    }
  }
}
```

Restart Claude Desktop and try: *"What's my current sprint focus?"*

### Configuration (Windsurf)

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "nucleus": {
      "command": "python3",
      "args": ["-m", "mcp_server_nucleus"],
      "env": {
        "NUCLEAR_BRAIN_PATH": "/path/to/your/.brain"
      }
    }
  }
}
```

### Configuration (Cursor)

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "nucleus": {
      "command": "python3",
      "args": ["-m", "mcp_server_nucleus"],
      "env": {
        "NUCLEAR_BRAIN_PATH": "/path/to/your/.brain"
      }
    }
  }
}
```

### ❓ Troubleshooting

**"Show me all tasks" returns nothing?**
Check your config pointer! You might be pointing to an old or temp brain.

1. **Check config:** Open `~/Library/Application Support/Claude/claude_desktop_config.json`
2. **Verify path:** Ensure `NUCLEAR_BRAIN_PATH` points to your active project (e.g., `/Users/me/my-project/.brain`)
3. **Restart:** You MUST restart Claude Desktop after any config change.

## 🛠 Tool Categories (110+ Total)

### 🎯 Core Orchestration
| Tool | Description |
|------|-------------|
| `brain_session_start` | **START HERE** — Get priorities, tasks, and recommendations |
| `brain_orchestrate` | The "God Command" — auto-claim and execute tasks |
| `brain_health` | System health dashboard with component status |
| `brain_version` | Version and capability info |

### 📋 Task Management
| Tool | Description |
|------|-------------|
| `brain_add_task` | Create tasks with priority, skills, dependencies |
| `brain_list_tasks` | Query with filters (status, priority, skill, claimed_by) |
| `brain_get_next_task` | Get highest-priority unblocked task for your skills |
| `brain_claim_task` | Atomically claim (prevents race conditions) |
| `brain_update_task` | Update status, priority, etc. |
| `brain_escalate` | Request human help when stuck |

### 🐝 Swarm Coordination
| Tool | Description |
|------|-------------|
| `brain_orchestrate_swarm` | Launch multi-agent missions |
| `brain_spawn_agent` | Create ephemeral agents for specific tasks |
| `brain_autopilot_sprint` | Orchestrate multiple slots in parallel |

### 💾 Session & Memory
| Tool | Description |
|------|-------------|
| `brain_save_session` | Persist context for later resumption |
| `brain_resume_session` | Restore previous session state |
| `brain_search_memory` | Search long-term memory |
| `brain_read_memory` | Read memory categories |

### 📊 Monitoring & Audit
| Tool | Description |
|------|-------------|
| `brain_satellite_view` | Unified view of depth, activity, health |
| `brain_metrics` | Velocity, closure rates, mental load |
| `brain_open_loops` | All pending tasks, todos, drafts, decisions |

**V2 Task Schema (11 fields):**
```json
{
  "id": "task-abc123",
  "description": "Build landing page",
  "status": "PENDING | READY | IN_PROGRESS | BLOCKED | DONE | FAILED | ESCALATED",
  "priority": 1,
  "blocked_by": ["task-prerequisite"],
  "required_skills": ["python", "frontend"],
  "claimed_by": "agent-thread-id",
  "source": "user | synthesizer",
  "escalation_reason": null,
  "created_at": "2026-01-03T12:00:00",
  "updated_at": "2026-01-03T12:00:00"
}
```

## 📡 MCP Resources

| Resource | Description |
|----------|-------------|
| `brain://state` | Live state.json content |
| `brain://events` | Recent events stream |
| `brain://triggers` | Trigger definitions |
| `brain://context` | **Full context for cold start** — click in sidebar for instant context |

## 💬 MCP Prompts

| Prompt | Description |
|--------|-------------|
| `cold_start` | **Get instant context** — sprint, events, artifacts, workflows |
| `activate_synthesizer` | Orchestrate current sprint |
| `start_sprint` | Initialize a new sprint |

## 🎯 Common Use Cases

### 1. Run a Sprint
```
> "What's my current sprint focus?"
> "Add a task: Build landing page with priority 1"
> "Show me all priority 1 tasks"
```

### 2. Coordinate Multiple Agents
```
> "Claim the next Python task for me"
> "Mark task-abc123 as DONE"
> "List all tasks claimed by agent-1"
```

### 3. Escalate When Stuck
```
> "Escalate task-xyz with reason: Need human approval on pricing"
```
The task is released and flagged for human intervention.

### 4. Check Agent Context
```
> "Use the cold_start prompt from nucleus"
```
Instantly loads sprint, events, and artifacts.

## 🚀 Cold Start (New in v0.2.4)

Start every new session with full context:

```
> Use the cold_start prompt from nucleus
```

Or click `brain://context` in Claude Desktop's sidebar.

**What you get:**
- Current sprint name, focus, and status
- Recent events and artifacts
- Workflow detection (e.g., `lead_agent_model.md`)
- Lead Agent role assignment

## 📁 Expected `.brain/` Structure

```
.brain/
├── ledger/
│   ├── events.jsonl
│   ├── state.json
│   └── triggers.json
├── artifacts/
│   ├── research/
│   ├── strategy/
│   └── ...
└── agents/
    └── *.md
```

## ⚠️ Known Limitations

- **IDE context is separate**: Each MCP client (Claude Desktop, Cursor, Windsurf) connects to the same `.brain/` directory and shares project state. However, IDE-specific context (Cursor's codebase memory, Antigravity's conversation artifacts, etc.) remains separate per editor.
- **No cross-editor sync**: Artifacts created in one IDE's conversation don't automatically sync to another. Manual copy is required for important documents.
- **Python 3.10+ required**: Won't work with older Python versions.

## 🚀 What's New in v0.5.0

- **110+ MCP Tools** (up from 16 in v0.3.0)
- **V3.1 Task Engine** with slot pooling and tier routing
- **Swarm Orchestration** for recursive multi-agent missions
- **Session Persistence** across conversations
- **Health Monitoring** endpoints for production use
- **E2E Test Suite** — 8/8 critical path tests passing

## 📜 License

MIT © Nucleus Team

---

**Built for the AI-native developer.** Star us on GitHub if Nucleus saves you from context amnesia! ⭐

