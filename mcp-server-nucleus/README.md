# 🧠 Nucleus-MCP

> ⚠️ **Official Repository** → **[nucleus-mcp](https://github.com/eidetic-works/nucleus-mcp)**

[![PyPI version](https://badge.fury.io/py/nucleus-mcp.svg)](https://badge.fury.io/py/nucleus-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-brightgreen)](https://modelcontextprotocol.io)

> **The Sovereign Agent Control Plane** — One brain that syncs Cursor, Claude Desktop, Windsurf, and any MCP-compatible tool.

> [!CAUTION]
> **After the [OpenClaw security crisis](https://www.youtube.com/watch?v=ceEUO_i7aW4) (1.5M API keys leaked, sleeper agents in skills), agent security is no longer optional.**
> Nucleus was built security-first: Hypervisor controls, resource locking, and full audit trails — all 100% local.

---

## 📦 Installation

The clean, open source version of Nucleus is now available at:

**→ [github.com/eidetic-works/nucleus-mcp](https://github.com/eidetic-works/nucleus-mcp)**

```bash
pip install nucleus-mcp
nucleus-init
```

This repository (`mcp-server-nucleus`) is the internal development monorepo. For production use, please use the official open source package above.

---

## 🎯 The Problem

You use **multiple AI tools** daily:
- Cursor for coding
- Claude Desktop for thinking
- Windsurf for exploration
- ChatGPT for quick answers

**But they don't share memory.**

Every time you switch tools, you lose context. You re-explain decisions. You repeat yourself.

---

## ✨ The Solution

**Nucleus syncs them with one brain.**

```
Tell Claude about a decision → Cursor knows it
Make a plan in Windsurf → Claude remembers it
One brain. All your tools.
```

<!-- TODO: Add demo GIF here showing cross-platform sync -->

---

## 🚀 What Makes Nucleus Different

| Feature | Other Solutions | Nucleus |
|---------|-----------------|---------|
| **Cross-Platform Sync** | Single platform only | ✅ Syncs ALL your AI tools |
| **Sovereignty** | Cloud-dependent | ✅ 100% local, your data stays on your machine |
| **Protocol** | Proprietary | ✅ MCP standard (Anthropic-backed) |
| **Security** | Often misconfigured | ✅ Secure by default, audit logs included |
| **Lock-in** | Platform-specific | ✅ MIT license, open standard |

---

## 🛠 140+ MCP Tools Included

- **Memory** — Persistent knowledge that survives sessions
- **Tasks** — Track work across agents
- **Sessions** — Save and resume context
- **Sync** — Multi-agent brain synchronization
- **Hypervisor** — File locking, security, audit trails
- **Orchestration** — Coordinate multiple agents

---

## ⚡ Comparison: Nucleus vs Alternatives

| | OpenClaw | Claude Code | Nucleus |
|---|----------|-------------|---------|
| **Security** | ❌ Sleeper agents, key leaks | ⚠️ Cloud-managed | ✅ Hypervisor + audit trail |
| **What it syncs** | OpenClaw → OpenClaw | Claude → Claude | **Everything ↔ Everything** |
| **Cross-platform** | ❌ | ❌ | ✅ |
| **Local-first** | ⚠️ Some cloud | ⚠️ Some cloud | ✅ 100% local |
| **MCP Native** | ❌ Custom protocol | ⚠️ Limited | ✅ Full MCP |
| **Open Source** | ✅ MIT | ❌ Closed | ✅ MIT |

**OpenClaw trades security for capability. Nucleus gives you both.**
**Nucleus connects ALL your platforms with one brain.**

## 🚀 Quick Start (2 Minutes)

### 1. Install
```bash
pip install nucleus-mcp
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
      "args": ["-m", "nucleus_mcp"],
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
      "args": ["-m", "nucleus_mcp"],
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
      "args": ["-m", "nucleus_mcp"],
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

## 🔄 Multi-Agent Sync (New in v0.7.0)

**The killer feature: Multiple agents, one brain.**

```python
# Agent A (Claude Desktop) makes a decision
brain_sync_now()  # Syncs to shared .brain/

# Agent B (Cursor) automatically sees it
brain_sync_status()  # Shows last sync, active agents
```

**Features:**
- **Intent-Aware Locking** — Files locked with WHO/WHEN/WHY metadata
- **Conflict Detection** — Last-write-wins with manual resolution option  
- **Auto-Sync** — Optional file watcher for real-time sync
- **Audit Trail** — Every sync logged to events.jsonl

---

## 🛠 Tool Categories

### 🧠 Core (Public)
| Tool | Description |
|------|-------------|
| `brain_write_engram` | Store persistent knowledge |
| `brain_query_engrams` | Retrieve knowledge |
| `brain_audit_log` | Verify ledger integrity |
| `brain_mount_server` | Mount sub-MCP servers |

### 🔄 Sync Tools
| Tool | Description |
|------|-------------|
| `brain_sync_now` | Manually trigger brain sync |
| `brain_sync_status` | Check sync state and conflicts |
| `brain_sync_auto` | Enable/disable auto-sync |
| `brain_identify_agent` | Register agent identity |

### 🔒 Enterprise Features
| Feature | Capabilities |
|---------|--------------|
| **Audit Logs** | Full decision trail with context hashing |
| **RBAC** | Role-based access control (coming soon) |
| **SSO** | Enterprise SSO integration (coming soon) |
| **Compliance** | SOC2/HIPAA export reports (coming soon) |

## ❓ How is Nucleus Different?

> **See the full comparison:** [Nucleus vs ContextStream vs mem0 vs OpenClaw →](docs/COMPARISON.md)

| | Nucleus | ContextStream | mem0 |
|---|:-------:|:-------------:|:----:|
| **Architecture** | 100% Local (Git-native) | Cloud SaaS | Cloud API |
| **Audit Trail** | ✅ Full | ❌ | ❌ |
| **Governance** | ✅ Policy engine | ❌ | ❌ |
| **Pricing** | Free (MIT) | Freemium → Paid | Freemium → Paid |

---

## 🤝 Community & Contributing

We're building the universal brain for AI agents. Join us!

- **🐛 Found a bug?** Open an [Issue](https://github.com/eidetic-works/nucleus-mcp/issues)
- **💡 Feature idea?** Start a [Discussion](https://github.com/eidetic-works/mcp-server-nucleus/discussions)
- **🔧 Want to contribute?** See [CONTRIBUTING.md](CONTRIBUTING.md)
- **💬 Join Discord** — [discord.gg/nucleus](https://discord.gg/nucleus) (coming soon)

## �📜 License

MIT © Nucleus Team

---

**Built for the AI-native developer.** Star us on GitHub if Nucleus saves you from context amnesia! ⭐

