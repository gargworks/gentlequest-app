# Launch Posts for mcp-server-nucleus

## 🐦 Twitter/X Launch Thread

### Tweet 1 (Main)
```
🧠 Just shipped mcp-server-nucleus v0.3.0

Multi-agent orchestration for Claude Desktop & Windsurf.

→ 16 tools (6 new V2 Task tools!)
→ Priority queues + skill-based routing
→ Atomic task claiming (no race conditions)
→ One command: nucleus-init

pip install mcp-server-nucleus

🔗 github.com/LKGargProjects/mcp-server-nucleus
```

### Tweet 2 (V2 Features)
```
What's new in v0.3.0?

🎯 Task Orchestration System:
• Priority queues (1 = urgent)
• Skill-based routing
• Dependency DAG
• Escalation to humans

Your AI agents can now coordinate like a real team.
```

### Tweet 3 (Demo)
```
🎬 [VIDEO]

Watch: Claude claims a task, updates status, and escalates when stuck.

This is proper multi-agent coordination.
```

---

## 📰 Hacker News Post

**Title:** Show HN: mcp-server-nucleus v0.3.0 – Multi-agent task orchestration for Claude

**Text:**
```
I built an MCP server that gives AI agents persistent memory and real task coordination.

The problem: Every Claude conversation starts from zero. No memory. No way to coordinate multiple agents.

The solution: A local .brain/ folder with:
- Event ledger (what happened)
- State (current context)
- Artifacts (agent outputs)
- V2 Task Queue (priority, skills, dependencies)

New in v0.3.0:
- 6 Task Orchestration tools (claim, escalate, etc.)
- Priority queues (1 = urgent)
- Skill-based routing
- Dependency DAG (task A blocks task B)
- Atomic locking (no race conditions)

Works with Claude Desktop & Windsurf. All data stays local.

Try it: pip install mcp-server-nucleus

Looking for feedback on:
1. What task orchestration patterns do you need?
2. Interest in optional cloud sync for teams?

GitHub: https://github.com/LKGargProjects/mcp-server-nucleus
```

---

## 🤖 Reddit Posts

### r/LocalLLaMA
```
[Tool] mcp-server-nucleus v0.3.0 - Multi-agent task orchestration for Claude

Built an MCP server that gives Claude/Windsurf agents:
- Persistent memory (.brain/ folder)
- Task queue with priorities
- Skill-based routing
- Escalation to humans

New in v0.3.0:
- 6 Task Orchestration tools
- Atomic locking (no race conditions)
- Dependency DAG

100% local, no cloud dependency.

pip install mcp-server-nucleus

GitHub: https://github.com/LKGargProjects/mcp-server-nucleus

Demo video in comments!
```

### r/ClaudeAI
```
Built an MCP server for multi-agent task orchestration (v0.3.0)

After getting frustrated with Claude forgetting context and having no way to coordinate tasks between agents, I built mcp-server-nucleus.

It gives Claude a "brain" - a local folder that persists:
- Project state
- Task queue (with priorities!)
- Event history
- Agent coordination

New in v0.3.0:
- Claim tasks atomically (prevents race conditions)
- Escalate to humans when stuck
- Skill-based routing

Works with Claude Desktop & Windsurf. Setup takes 2 minutes.

pip install mcp-server-nucleus

Anyone else building multi-agent workflows with MCP?
```
