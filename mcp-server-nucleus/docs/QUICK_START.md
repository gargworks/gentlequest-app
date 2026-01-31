# Nucleus Quick Start Guide
## Get Running in 5 Minutes
### v0.5.1 | The Agent Control Plane

---

## 🚀 Installation

### Option 1: pip (Recommended)

```bash
pip install mcp-server-nucleus
```

### Option 2: From Source

```bash
git clone https://github.com/nucleus-mcp/nucleus.git
cd nucleus
pip install -e .
```

### Option 3: Docker

```bash
docker pull ghcr.io/nucleus-mcp/nucleus:latest
docker run -v ~/.brain:/data/.brain nucleus
```

---

## ⚙️ Configuration

### 1. Set the Brain Path

Nucleus stores all data in a `.brain/` folder. Set its location:

```bash
# Add to your shell profile (~/.zshrc, ~/.bashrc)
export NUCLEAR_BRAIN_PATH="$HOME/.brain"

# Create the directory
mkdir -p ~/.brain
```

### 2. Configure Your MCP Client

**For Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "nucleus": {
      "command": "mcp-server-nucleus",
      "env": {
        "NUCLEAR_BRAIN_PATH": "/Users/YOUR_USERNAME/.brain"
      }
    }
  }
}
```

**For Cursor** (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "nucleus": {
      "command": "mcp-server-nucleus",
      "env": {
        "NUCLEAR_BRAIN_PATH": "/path/to/your/project/.brain"
      }
    }
  }
}
```

### 3. Restart Your MCP Client

After configuration, restart Claude Desktop or Cursor to load Nucleus.

---

## ✅ Verify Installation

Run these commands in your AI chat to verify Nucleus is working:

```
brain_health()
```

You should see:

```
💚 NUCLEUS HEALTH CHECK
═══════════════════════════════════════

🟢 HEALTHY
[████████████████████] 100%

📋 VERSION
   Nucleus: 0.5.0
   ...

✅ System is healthy
```

---

## 🎯 Your First 5 Minutes

### 1. Start a Session

```
brain_session_start()
```

This shows your current context, pending tasks, and recommendations.

### 2. Create Your First Task

```
brain_add_task(description="Learn Nucleus basics", priority=1)
```

### 3. View Your Tasks

```
brain_list_tasks()
```

### 4. Complete a Task

```
brain_complete_task(task_id="YOUR_TASK_ID")
```

### 5. Check the Dashboard

```
brain_dashboard()
```

---

## 🔧 Core Tools

| Tool | Description |
|------|-------------|
| `brain_session_start()` | Start session, get context |
| `brain_add_task()` | Create a new task |
| `brain_list_tasks()` | View all tasks |
| `brain_claim_task()` | Claim a task to work on |
| `brain_complete_task()` | Mark task as done |
| `brain_orchestrate()` | Auto-assign best task |
| `brain_dashboard()` | View system status |
| `brain_health()` | Check system health |

---

## 📁 Understanding .brain/

Your `.brain/` folder structure:

```
.brain/
├── ledger/
│   ├── tasks.json      # Your task queue
│   └── events.jsonl    # Activity log
├── sessions/           # Saved sessions
├── slots/
│   └── registry.json   # Agent slots
├── artifacts/          # Generated files
└── state.json          # Current state
```

---

## 🎓 Next Steps

1. **Read the full docs:** `brain_version()` for links
2. **Explore tools:** There are 110+ tools available
3. **Try autopilot:** `brain_autopilot_sprint_v2()` for autonomous execution
4. **Save sessions:** `brain_save_session()` to preserve context

---

## 🆘 Troubleshooting

### "NUCLEAR_BRAIN_PATH not set"

```bash
export NUCLEAR_BRAIN_PATH="$HOME/.brain"
mkdir -p ~/.brain
```

### "Brain path does not exist"

```bash
mkdir -p ~/.brain/ledger ~/.brain/sessions ~/.brain/slots
```

### MCP Server Not Loading

1. Check your config file syntax (valid JSON)
2. Verify the path to `mcp-server-nucleus` is correct
3. Restart your MCP client

### Need Help?

- GitHub Issues: https://github.com/nucleus-mcp/nucleus/issues
- Discord: https://discord.gg/nucleus (coming soon)

---

## 🧠 The Trinity Framework

Nucleus is built on three pillars:

```
ORCHESTRATION + CHOREOGRAPHY + CONTEXT = NUCLEUS
   (control)      (autonomy)     (memory)
```

- **Orchestration:** Who does what (task assignment, scheduling)
- **Choreography:** How it happens (autonomous execution)
- **Context:** What we know (Persistent Engrams)

This is what makes Nucleus different from task managers (no autonomy) or AutoGPT (no persistent state).

---

*Happy orchestrating! 🚀*
