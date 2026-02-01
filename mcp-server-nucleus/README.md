# 🧠 Nucleus Sovereign OS

[![PyPI version](https://badge.fury.io/py/mcp-server-nucleus.svg)](https://badge.fury.io/py/mcp-server-nucleus)
[![Website](https://img.shields.io/badge/Website-nucleusos.dev-blueviolet?logo=globe)](https://nucleusos.dev)
[![Watch Launch Trailer](https://img.shields.io/badge/Watch-Launch_Trailer-red?logo=youtube)](https://youtu.be/jI8TUpfjS1A)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **The Operating System for AI Agents** — Persistent Operational Memory, Swarm Orchestration, and Local-First Sovereignty.

Nucleus is the **Recursive Aggregator** that gives your AI agents a persistent brain (`.brain/`) and a file system. It turns stateless chatbots into stateful **Sovereign Agents**.

### Context vs. Control
Claude's `CLAUDE.md` provides **static context**. Nucleus provides **active control**.

| Feature | CLAUDE.md / .cursorrules | Nucleus (Agent Control Plane) |
| :--- | :--- | :--- |
| **State** | Static (read-only text) | **Dynamic** (Stateful DB, Event Ledger) |
| **Memory** | Session-bound (forgotten on close) | **Persistent** (Project-bound, recallable) |
| **Security** | None (Prompt injection risk) | **Enforced** (Auth boundary, Default Deny) |
| **Tools** | Suggestions only | **Orchestrated Execution** (DAGs) |
| **Audit** | None | **Full Decision Trail** (Who/Why/When) |

## ✨ Governance Features (The Moat)

- **Default Deny Security** — All mounted servers start with NO network/filesystem access.
- **Explicit Consent** — You approve every command. No silent execution.
- **Isolation Boundaries** — Tools cannot see each other or the full chat history.
- **Auth Firewall** — Tokens are stored in Nucleus (Host), never passed to agents.
- **Event Ledger** — Immutable audit trail of every agent decision (`DecisionMade`).
- **Decision Provenance** — v0.6.0 DSoR: Full audit trail with context hashing.
- **IPC Security** — Per-request auth tokens prevent socket impersonation (CVE-2026-001).
- **135 Native Tools** — For orchestration, swarms, memory, and DSoR inspection.

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

## ✨ Core Features (Included)

- **Persistent Memory** — `brain_write_engram` / `brain_query_engrams` (Vector-lite).
- **Audit Ledger** — Immutable SHA-256 logs of every action (`brain_audit_log`).
- **Recursive Mounting** — `brain_mount_server` (Basic).
- **Local Sovereignty** — Zero cloud. All data in `~/.nucleus/brain`.

## 🔐 Sovereign Edition (Closed Beta)
*The "Dark Wheel" is reserved for active builders.*

**Early Access Program**
The Sovereign Edition (Task Engine, Swarm, Federation) is currently invite-only to ensure stability.
To join the cohort:
1.  **Install Core** (PyPI).
2.  **DM u/NucleusOS** on Reddit for an invite code.

**Unlockable Features:**

- **Task Engine** — `brain_add_task`, `brain_claim_task`.
- **Swarm Orchestration** — `brain_orchestrate_swarm`.
- **Session Persistence** — `brain_save_session`.
- **Federation** — Peer-to-Peer Agent Mesh.

## 🚀 Quick Start (Core)

### 1. Install
```bash
pip install mcp-server-nucleus
```

### 2. Initialize
```bash
nucleus-init
```

### 3. Use the Memory
Restart Claude and try:
> "Write an engram: 'The project goal is World Domination'. Then audit the ledger."

---

## 🛠 Tool Categories

### 🧠 Core (Public)
| Tool | Description |
|------|-------------|
| `brain_write_engram` | Store persistent knowledge |
| `brain_query_engrams` | Retrieve knowledge |
| `brain_audit_log` | Verify ledger integrity |
| `brain_mount_server` | Mount sub-MCP servers |

### 🔒 Sovereign (Beta Key Required)
| Feature | Capabilities |
|---------|--------------|
| **Task Engine** | Priority queues, dependency DAGs, agent assignment |
| **Swarm** | Multi-agent recursive orchestration |
| **Federation** | Cross-machine agent communication |
| **Deep Monitoring** | Real-time dashboards and metrics |

## �️ Community & Feedback

We represent the **Sovereign Web**. We build in the open, but we protect the signal.

- **🐛 Found a bug?** Open an [Issue on GitHub](https://github.com/eidetic-works/mcp-server-nucleus/issues).
- **💡 Have an idea?** Discuss it on [GitHub Discussions](https://github.com/eidetic-works/mcp-server-nucleus/discussions).
- **🗝️ Want to join the Inner Circle?** Check the **Early Access Program** above.

## �📜 License

MIT © Nucleus Team

---

**Built for the AI-native developer.** Star us on GitHub if Nucleus saves you from context amnesia! ⭐

