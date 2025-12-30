# Launch Posts for mcp-server-nucleus

## 🐦 Twitter/X Launch Thread

### Tweet 1 (Main)
```
🧠 Just shipped mcp-server-nucleus v0.2.1

The first multi-agent orchestration MCP server for Claude Desktop.

→ 10 tools for agent coordination
→ Persistent memory via local .brain/
→ One-command setup: nucleus-init

pip install mcp-server-nucleus

🔗 github.com/LKGargProjects/mcp-server-nucleus
```

### Tweet 2 (Features)
```
What can you do with it?

• Ask Claude about your project sprint
• Store research artifacts
• Trigger agents with tasks
• Coordinate multiple AI agents

All data stays local. Zero-knowledge default.
```

### Tweet 3 (Demo)
```
🎬 [VIDEO]

Watch: Claude remembers my project and lists my artifacts.

This is the future of AI assistants with persistent memory.
```

---

## 📰 Hacker News Post

**Title:** Show HN: mcp-server-nucleus – Multi-agent orchestration for Claude Desktop

**Text:**
```
I built an MCP server that gives Claude persistent memory and multi-agent coordination.

The problem: Every Claude conversation starts from zero. No memory across sessions. No way to coordinate multiple AI agents.

The solution: A local .brain/ folder that stores:
- Event ledger (what happened)
- State (current context)
- Artifacts (agent outputs)
- Triggers (when to activate agents)

Features:
- 10 MCP tools for reading/writing state
- 3 MCP Resources for subscribable data
- 2 MCP Prompts for pre-built orchestration
- One-command setup: python3 -m mcp_server_nucleus.cli init

All data stays local - zero cloud dependency.

Try it: pip install mcp-server-nucleus

Looking for feedback on:
1. What tools would be most useful?
2. Interest in a pattern-sharing cloud layer (opt-in)?

GitHub: https://github.com/LKGargProjects/mcp-server-nucleus
```

---

## 🤖 Reddit Posts

### r/LocalLLaMA
```
[Tool] mcp-server-nucleus - Give Claude Desktop persistent memory

Built an MCP server that connects Claude to a local .brain/ folder for:
- Session memory
- Project state
- Research artifacts
- Multi-agent coordination

100% local, no cloud dependency.

pip install mcp-server-nucleus

GitHub: https://github.com/LKGargProjects/mcp-server-nucleus

Would love feedback from the community!
```

### r/ClaudeAI
```
Built an MCP server for multi-agent orchestration

After getting frustrated with Claude forgetting context between sessions, I built mcp-server-nucleus.

It gives Claude a "brain" - a local folder that persists:
- Your project state
- Research artifacts
- Event history
- Agent coordination rules

Works with Claude Desktop. Setup takes 2 minutes.

pip install mcp-server-nucleus

Anyone else working on persistent memory for Claude?
```
