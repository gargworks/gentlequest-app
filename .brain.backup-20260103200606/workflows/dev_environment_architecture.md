# Development Environment Architecture
> **Version:** 1.1  
> **Date:** December 28, 2025  
> **Purpose:** Official protocol for thread usage, brain access, and MCP testing

---

## 🎯 Quick Visual Summary

### The Two Brains

```
ai-mvp-backend/.brain/  (THE BRAIN)
       │
       ├─── 🧠 SYNTH (direct file access, no MCP)
       │         └── For GentleQuest production work
       │
       └─── 🐕 DOGFOOD (MCP access via brain_* tools)
                 └── For evaluating if MCP adds value


mcp-server-nucleus/  (THE TOOL CODE)
       │
       └─── 🎯 TECH-DIRECTOR (direct editing, no MCP)
                 └── For developing nucleus itself
```

### The Command Structure

```
TECH-DIRECTOR (you're here)
     │
     ├── Direct editing → Nucleus MCP code
     │
     └── Fallback for everything

SYNTH + Agents ─────────┐
                        │
                        ├──→ ai-mvp-backend/.brain/
                        │         (Direct Access)
                        │
DOGFOOD ────────────────┘
                        (MCP Access - Same Brain)
```

---

## 🏗️ The Three Tracks

### Overview

| Track | Thread | Uses MCP? | Brain/Code | Purpose |
|-------|--------|-----------|------------|---------|
| **1** | 🧠 SYNTH + Agents | ❌ No | `ai-mvp-backend/.brain/` | GentleQuest product work |
| **2** | 🎯 TECH-DIRECTOR | ❌ No | Direct file editing | Nucleus MCP development |
| **3** | 🐕 DOGFOOD | ✅ Yes | `ai-mvp-backend/.brain/` (via MCP) | Evaluate MCP value |

---

## 📐 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    ai-mvp-backend/.brain/                       │
│                       (THE BRAIN)                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ledger/  │  agents/  │  artifacts/  │  memory/  │ meta/ │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                      │
│           ┌──────────────┼──────────────┐                      │
│           │              │              │                      │
│           ▼              ▼              ▼                      │
│    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐             │
│    │ 🧠 SYNTH    │ │ Other      │ │ 🐕 DOGFOOD │             │
│    │ + Agents   │ │ Agents     │ │            │             │
│    │            │ │            │ │            │             │
│    │ DIRECT     │ │ DIRECT     │ │ VIA MCP   │             │
│    │ FILE ACCESS│ │ FILE ACCESS│ │ brain_*   │             │
│    └─────────────┘ └─────────────┘ └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    mcp-server-nucleus/                          │
│                      (THE TOOL CODE)                            │
│                          │                                      │
│                          ▼                                      │
│                  ┌─────────────┐                                │
│                  │ 🎯 TECH-    │                                │
│                  │ DIRECTOR    │                                │
│                  │             │                                │
│                  │ DIRECT      │                                │
│                  │ FILE/CMD    │                                │
│                  └─────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Track 1: GentleQuest Product Work

### Configuration

| Setting | Value |
|---------|-------|
| **Threads** | 🧠 SYNTH, 📈 STRAT, 🏗️ ARCH, 💻 DEV, 🔍 CRITIC, 🔬 RESEARCH |
| **Brain Location** | `ai-mvp-backend/.brain/` |
| **Access Method** | Direct file access (view_file, write_to_file) |
| **Uses MCP?** | ❌ No |

### Purpose

- GentleQuest feature development
- Sprint execution
- Agent coordination
- Production-ready work

### How Agents Access Brain

```
# Example: SYNTH reading state
view_file("/Users/lokeshgarg/ai-mvp-backend/.brain/ledger/state.json")

# Example: Researcher writing artifact
write_to_file("/Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/research/new_finding.md")
```

---

## Track 2: Nucleus MCP Development

### Configuration

| Setting | Value |
|---------|-------|
| **Thread** | 🎯 TECH-DIRECTOR |
| **Code Location** | `mcp-server-nucleus/` |
| **Access Method** | Direct file editing + run_command |
| **Uses MCP?** | ❌ No (to avoid circular dependency) |

### Purpose

- Develop nucleus MCP code
- Fix bugs in nucleus
- Run commands (pytest, pip install, etc.)
- General founder work

### Why No MCP Here

| Reason | Explanation |
|--------|-------------|
| **Circular dependency** | Can't use nucleus to fix nucleus |
| **Fallback safety** | Always have direct access if MCP breaks |
| **Clean separation** | Tool dev ≠ Tool usage |

### How TECH-DIRECTOR Works

```
# Example: Editing nucleus code
write_to_file("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/server.py")

# Example: Running tests
run_command("pytest mcp-server-nucleus/tests/")

# Example: Publishing
run_command("cd mcp-server-nucleus && python -m build && twine upload dist/*")
```

---

## Track 3: MCP Dogfood Testing

### Configuration

| Setting | Value |
|---------|-------|
| **Thread** | 🐕 DOGFOOD |
| **Brain Location** | `ai-mvp-backend/.brain/` (same as Track 1) |
| **Access Method** | MCP tools (`brain_*`) |
| **Uses MCP?** | ✅ Yes |

### Purpose

- Evaluate if MCP tools add value
- Compare MCP access vs direct access
- Log findings to `dogfood_log.md`
- Test real-world MCP behavior

### MCP Configuration Required

```json
{
  "nucleus": {
    "command": "python3.11",
    "args": ["-m", "mcp_server_nucleus"],
    "env": {
      "NUCLEAR_BRAIN_PATH": "/Users/lokeshgarg/ai-mvp-backend/.brain"
    }
  }
}
```

### How DOGFOOD Accesses Brain (Via MCP)

```
# Instead of view_file, use:
brain_get_state()
brain_read_artifact("test/dogfood_log.md")
brain_list_artifacts()

# Instead of write_to_file, use:
brain_write_artifact("test/notes.md", content)
brain_emit_event(event_type, emitter, data)
brain_update_state(updates)
```

### ❄️ Cold Start Testing (New User Experience)

> **Problem:** Testing on `ai-mvp-backend/.brain/` tests MCP with EXISTING data.  
> It doesn't test what a NEW user experiences with an EMPTY brain.

#### Solution: Two Test Modes

| Mode | Brain | Purpose |
|------|-------|---------|
| **Warm Test** | `ai-mvp-backend/.brain/` | Real-world usage with existing data |
| **Cold Test** | `~/dogfood-brain/.brain/` | New user experience with empty brain |

#### Cold Start Test Protocol

```bash
# Create fresh brain for cold start testing
rm -rf ~/dogfood-brain
mkdir -p ~/dogfood-brain
cd ~/dogfood-brain
python3.11 -m mcp_server_nucleus init
```

#### MCP Config for Cold Start

```json
{
  "nucleus": {
    "env": {
      "NUCLEAR_BRAIN_PATH": "/Users/lokeshgarg/dogfood-brain/.brain"
    }
  }
}
```

#### What Cold Start Tests

| Test | What We Learn |
|------|---------------|
| `brain_get_state()` on empty | Does it fail gracefully? |
| `brain_list_artifacts()` | Returns empty list? |
| `brain_emit_event()` first event | Creates events.jsonl? |
| `brain_write_artifact()` first file | Creates directory? |

#### Cold Start Frequency

| When | How Often |
|------|-----------|
| **During active dev** | Once per week |
| **Before release** | Every time |
| **After major changes** | Every time |

---

## 🧪 The Comparison Test

### Same Brain, Different Access

| Operation | SYNTH (Direct) | DOGFOOD (MCP) |
|-----------|----------------|---------------|
| Read state | `view_file(.../state.json)` | `brain_get_state()` |
| Write artifact | `write_to_file(...)` | `brain_write_artifact(...)` |
| List files | `list_dir(...)` | `brain_list_artifacts()` |
| Log event | `write_to_file(events.jsonl)` | `brain_emit_event(...)` |

### What We're Evaluating

| Question | Measure |
|----------|---------|
| Is MCP faster? | Time per operation |
| Is MCP cleaner? | Code complexity |
| Does MCP reduce errors? | Typos, wrong paths |
| Does MCP add friction? | Extra steps needed |

---

## 📋 Thread Quick Reference

| Thread | What It Does | Uses MCP? | Fallback? |
|--------|--------------|-----------|-----------|
| 🎯 TECH-DIRECTOR | Nucleus dev, commands, general | ❌ | This IS the fallback |
| 🧠 SYNTH | GentleQuest orchestration | ❌ | TECH-DIRECTOR |
| 📈 STRAT | Strategy work | ❌ | TECH-DIRECTOR |
| 🏗️ ARCH | Architecture work | ❌ | TECH-DIRECTOR |
| 💻 DEV | Code implementation | ❌ | TECH-DIRECTOR |
| 🔍 CRITIC | Quality review | ❌ | TECH-DIRECTOR |
| 🔬 RESEARCH | Intelligence | ❌ | TECH-DIRECTOR |
| 🐕 DOGFOOD | MCP evaluation | ✅ | TECH-DIRECTOR |
| 🧬 GENESIS | Philosophy reference | N/A | Read-only |

---

## 🚦 Decision Rules

### When to Use TECH-DIRECTOR

- ✅ Editing nucleus code
- ✅ Running shell commands
- ✅ Quick file operations
- ✅ When MCP is broken/unavailable
- ✅ General questions
- ✅ This type of architectural discussion

### When to Use SYNTH + Agents

- ✅ GentleQuest feature work
- ✅ Sprint execution
- ✅ Cross-agent coordination
- ✅ When you want "hands-off" delegation

### When to Use DOGFOOD

- ✅ Testing MCP functionality
- ✅ Evaluating brain_* tools
- ✅ Logging to dogfood_log.md
- ✅ Comparing MCP vs direct access

---

## 📁 File Locations Summary

| Item | Path |
|------|------|
| GentleQuest Brain | `/Users/lokeshgarg/ai-mvp-backend/.brain/` |
| Nucleus MCP Code | `/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/` |
| Dogfood Log | `/Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/test/dogfood_log.md` |
| Thread Manifesto | `/Users/lokeshgarg/ai-mvp-backend/.brain/workflows/thread_identity_manifesto.md` |
| This Document | `/Users/lokeshgarg/ai-mvp-backend/.brain/workflows/dev_environment_architecture.md` |
| MCP Config | `/Users/lokeshgarg/.gemini/antigravity/mcp_config.json` |

---

## ⚡ Quick Start Commands

### Initialize a New DOGFOOD Session

```
ROLE: DOGFOOD - MCP Evaluation Tester

Read .brain/ via MCP tools only.
Log all observations to .brain/artifacts/test/dogfood_log.md

First test: Run brain_get_state() and brain_list_artifacts()
Rate the experience (1-5).
```

### Reset an Agent Thread

```
ROLE RESET: [AGENT_NAME] Agent, Level 5 Autonomy.

Read: .brain/agents/[agent_name].md
Read: .brain/ledger/state.json
Read: .brain/memory/context.md

Confirm: "[AGENT_NAME] online. Sprint: [X]. Awaiting tasks."
```

### TECH-DIRECTOR Reminder

```
You are TECH-DIRECTOR. 
Direct file access only. Do NOT use MCP tools.
You are the fallback when MCP fails.
```

---

*This is the official development environment architecture.*
*Keep this document updated as the system evolves.*
