# Execution Modalities Guide
> **Version:** 2025.Final  
> **Purpose:** Choose the right execution model for your workflow

---

## Overview

The Nuclear Brain supports **three execution modalities**:

| Modality | Execution | Best For | Tools Used |
|----------|-----------|----------|------------|
| **CLI Mode** | Parallel (API-driven) | Automated pipelines, background processing | `brain_executor.py`, `agent_manager.py` |
| **God Mode** | Sequential (Single LLM) | Interactive work, deep thinking tasks | One Claude/Gemini session |
| **UI Mode** | Manual routing | Monitoring, approvals, visualization | `cockpit.py` + separate chats |

---

## ⚠️ Feature Utilization Audit

### We Built These Components

| Component | Functions | Purpose |
|-----------|-----------|---------|
| `brain_bootstrap.py` | 17 functions | Initialize .brain/, schemas, content generators |
| `brain_events.py` | 24 functions | Event emission, reading, trigger processing, state management |
| `brain_executor.py` | 8 functions | LLM API execution, context building, output capture |
| `agent_manager.py` | 12 functions | Flywheel daemon, sprint management, trigger matching |
| `cockpit.py` | 10 functions | Dashboard, decision queue, event viewer, emergency controls |
| `.brain/agents/*.md` | 6 prompts | System prompts for each agent |
| `.brain/ledger/triggers.json` | 8 triggers | Event → Agent routing rules |

### Feature Utilization by Modality

| Feature | CLI Mode | God Mode | UI Mode | Notes |
|---------|----------|----------|---------|-------|
| **brain_bootstrap.py** | ✅ Full | ⚠️ Manual init | ⚠️ Manual init | Run once at start |
| **brain_events.py** | | | | |
| ├─ `emit_event()` | ✅ Auto | ❌ LLM can't call | ⚠️ Cockpit does some | God Mode can write to file manually |
| ├─ `read_recent_events()` | ✅ Full | ⚠️ Must read file | ✅ Cockpit shows | |
| ├─ `find_matching_triggers()` | ✅ Auto | ❌ Not used | ❌ Not used | Only CLI uses triggers |
| ├─ `get_agents_to_activate()` | ✅ Auto | ❌ Sequential anyway | ❌ Manual | |
| ├─ `emit_task_assigned()` | ✅ Auto | ❌ Not used | ⚠️ Sprint launch | |
| **brain_executor.py** | | | | |
| ├─ `AgentExecutor` | ✅ Full | ❌ Not used | ❌ Not used | **Only CLI uses LLM API** |
| ├─ `build_context()` | ✅ Full | ⚠️ Manual equiv | ❌ | |
| ├─ `process_pending_tasks()` | ✅ Auto | ❌ | ❌ | |
| **agent_manager.py** | | | | |
| ├─ `FlywheelManager` | ✅ Full | ❌ Not running | ⚠️ Can start | Daemon doesn't run in God Mode |
| ├─ `start_sprint()` | ✅ CLI | ⚠️ Can call manually | ✅ UI button | |
| ├─ `execute_agent_task()` | ✅ Full | ❌ | ❌ | |
| **cockpit.py** | | | | |
| ├─ Dashboard | ❌ Optional | ❌ Not used | ✅ Full | |
| ├─ Decision Queue | ❌ Optional | ❌ Not used | ✅ Full | |
| ├─ Event Feed | ❌ Optional | ❌ Not used | ✅ Full | |
| ├─ Sprint Launch | ⚠️ CLI better | ❌ | ✅ Full | |
| **triggers.json** | ✅ Full | ❌ Not used | ❌ Info only | **God Mode ignores triggers!** |
| **Agent Prompts** | ✅ Per-agent | ✅ Synthesizer only | ✅ Per-agent | |

### 🚨 Key Gaps Identified

| Gap | CLI Mode | God Mode | UI Mode | Impact |
|-----|----------|----------|---------|--------|
| **Triggers not used** | ✅ Works | ❌ MAJOR GAP | ❌ | God Mode loses event-driven routing |
| **No parallel execution** | ✅ Works | ❌ MAJOR GAP | ⚠️ Manual only | God Mode is strictly sequential |
| **LLM can't emit events** | ✅ Works | ❌ MAJOR GAP | ❌ | God Mode can't write to events.jsonl natively |
| **Cockpit unused in God Mode** | N/A | ❌ GAP | ✅ Works | No visibility during God Mode |
| **brain_events.py unused** | ✅ Works | ❌ MAJOR GAP | ⚠️ Partial | 90% of brain_events unused in God Mode |

### 📊 Utilization Score

| Modality | Features Used | Features Available | Utilization |
|----------|--------------|-------------------|-------------|
| **CLI Mode** | 45/50 | 50 | **90%** ✅ |
| **God Mode** | 15/50 | 50 | **30%** ❌ |
| **UI Mode** | 25/50 | 50 | **50%** ⚠️ |

---

## 💡 Recommendations to Reach Full Potential

### For God Mode (Currently 30% utilization)

**Problem:** Single LLM session can't run Python, emit events, or use triggers.

**Solutions:**

1. **Add MCP tools for brain operations** (Best)
   - Expose `emit_event()`, `read_events()` as MCP tools
   - LLM in Antigravity could then call them directly
   - Would unlock full event-driven behavior

2. **Hybrid workflow: God Mode + CLI monitoring**
   ```
   Terminal 1: python agent_manager.py start  # Monitor events
   Terminal 2: Claude God Mode session        # Writes to files
   Agent manager picks up God Mode outputs automatically
   ```

3. **Post-session scripting**
   ```bash
   # After God Mode session completes:
   python brain_events.py sync  # Parse artifacts → emit events
   ```

### For UI Mode (Currently 50% utilization)

**Problem:** Cockpit shows state but doesn't execute agents.

**Solutions:**

1. **Add "Execute Agent" button to cockpit**
   - Click researcher → opens Antigravity tab with prompt pasted
   - Reduces manual copy-paste

2. **Integrate with CLI for hybrid**
   ```
   Cockpit: Show status, launch sprints, approve decisions
   CLI: Handle actual agent execution in background
   ```

---

### Requirements
```bash
# Install
pip install google-generativeai  # or anthropic, openai

# Set API key
export GEMINI_API_KEY="your_key"      # For Gemini
export ANTHROPIC_API_KEY="your_key"   # For Claude
export OPENAI_API_KEY="your_key"      # For OpenAI
```

### Workflow
```bash
# 1. Start a sprint (sets goal)
python agent_manager.py sprint "Build RAG memory layer"

# 2. Start the flywheel (runs in background)
python agent_manager.py start

# 3. Monitor status
python agent_manager.py status

# 4. Check outputs
ls .brain/artifacts/

# 5. Stop when done
python agent_manager.py stop
```

### Pros
✅ **True parallelism** - Researcher and Strategist can work simultaneously  
✅ **Background processing** - No active attention required  
✅ **Event-driven** - Agents trigger each other automatically  
✅ **Scalable** - Can process many tasks concurrently  
✅ **Original design intent** - How the architecture was meant to work  

### Cons
❌ **Requires API keys** - Paid API access needed  
❌ **Token costs** - Each agent call costs money  
❌ **Less interactive** - Can't guide agents mid-task  
❌ **Context boundaries** - Agents have limited context windows  
❌ **Debugging harder** - Async nature makes tracing difficult  

---

## Modality 2: God Mode (Sequential Single-Session)

### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    SINGLE LLM SESSION                          │
│              (Claude Opus 4.5 / Gemini in Antigravity)         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   SYNTHESIZER as "God Prompt" embodies ALL agents:             │
│                                                                 │
│   1. [RESEARCHER MODE]  → Gather intelligence                  │
│   2. [STRATEGIST MODE]  → Analyze and strategize               │
│   3. [ARCHITECT MODE]   → Design systems                       │
│   4. [DEVELOPER MODE]   → Produce code                         │
│   5. [CRITIC MODE]      → Review and validate                  │
│   6. [SYNTHESIZER MODE] → Consolidate and report               │
│                                                                 │
│   [SEQUENTIAL: One agent perspective at a time]                │
└─────────────────────────────────────────────────────────────────┘
```

### How It Works
1. Open ONE Antigravity conversation (Claude Opus 4.5 or Gemini)
2. Paste Synthesizer system prompt from `.brain/agents/synthesizer.md`
3. Tell it: "Read .brain/ and execute current sprint tasks"
4. LLM internally "channels" each agent in sequence
5. Writes outputs to appropriate `.brain/artifacts/` folders
6. Single conversation maintains full context

### Requirements
```
✅ Antigravity subscription (or any LLM chat interface)
✅ No API keys needed
✅ LLM must have file system access
```

### Workflow
```
# 1. Open Antigravity → Select Claude Opus 4.5 Thinking

# 2. First message - set up the brain
"You are the Synthesizer from .brain/agents/synthesizer.md.
Read .brain/ledger/state.json to understand current sprint.
Execute all tasks, channeling each agent as needed.
Write outputs to .brain/artifacts/"

# 3. Let it work through each agent perspective

# 4. Review outputs in cockpit or terminal
python cockpit.py  # or: ls .brain/artifacts/
```

### Pros
✅ **No API costs** - Uses Antigravity subscription  
✅ **Full context preserved** - Single session remembers everything  
✅ **Interactive** - Can guide and course-correct mid-task  
✅ **Deep thinking** - Claude Opus 4.5 excels at complex reasoning  
✅ **Simpler setup** - No environment variables, no daemons  

### Cons
❌ **Sequential only** - Can't parallelize agent work  
❌ **Slower** - Must wait for each "agent" to finish  
❌ **Session limits** - Very long conversations may hit limits  
❌ **Manual trigger** - You must initiate the session  
❌ **No background** - Requires active attention  

---

## Modality 3: UI Mode (Manual Routing)

### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                      COCKPIT (cockpit.py)                       │
│                   Streamlit Dashboard                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   📊 STATUS    │ 🚀 LAUNCH   │ 📋 DECISIONS │ 📡 ACTIVITY      │
│                                                                 │
│   Shows:                                                        │
│   - Sprint status                                               │
│   - Pending approvals                                           │
│   - Event feed                                                  │
│   - Decision history                                            │
│                                                                 │
│   [MANUAL: You route between separate LLM chats]               │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│              SEPARATE ANTIGRAVITY CHATS                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Chat 1: Researcher   (with researcher.md prompt)             │
│   Chat 2: Strategist   (with strategist.md prompt)             │
│   Chat 3: Architect    (with architect.md prompt)              │
│   Chat 4: Developer    (with developer.md prompt)              │
│   Chat 5: Critic       (with critic.md prompt)                 │
│   Chat 6: Synthesizer  (with synthesizer.md prompt)            │
│                                                                 │
│   [PARALLEL: Multiple chats can run simultaneously]            │
└─────────────────────────────────────────────────────────────────┘
```

### How It Works
1. Cockpit shows system state and what needs attention
2. You open separate Antigravity chats for each agent
3. Each chat has that agent's system prompt
4. You manually route by: reading events → opening right chat
5. Agents write to `.brain/artifacts/`, emit events
6. Cockpit reflects the changes

### Requirements
```bash
# Start cockpit
streamlit run cockpit.py

# Open multiple Antigravity browser tabs
# Each with a different agent prompt loaded
```

### Workflow
```
# 1. Start cockpit
streamlit run cockpit.py

# 2. Launch a sprint from UI (LAUNCH tab)

# 3. See which agents need activation (ACTIVITY tab shows events)

# 4. Open Antigravity → Select model → Paste agent prompt
e.g., "Read .brain/agents/researcher.md and execute task X"

# 5. Agent produces output, writes to artifacts

# 6. Check cockpit for next agent to activate

# 7. Repeat until sprint complete
```

### Pros
✅ **True parallelism** - Multiple browser tabs = parallel agents  
✅ **Visual dashboard** - Easy to see system state  
✅ **Model flexibility** - Use different models per agent  
✅ **No API costs** - All via Antigravity subscription  
✅ **Full control** - You decide when/what to activate  

### Cons
❌ **Manual routing** - You are the scheduler  
❌ **Cognitive load** - Must track multiple conversations  
❌ **Context switching** - Jumping between tabs  
❌ **Not automated** - Requires active management  
❌ **Error prone** - Easy to miss an activation  

---

## Decision Matrix

| Factor | CLI Mode | God Mode | UI Mode |
|--------|----------|----------|---------|
| **Setup complexity** | High | Low | Medium |
| **API costs** | Yes ($) | No | No |
| **Parallelism** | ✅ True | ❌ Sequential | ✅ Manual |
| **Automation** | ✅ Full | ❌ None | ❌ None |
| **Interactivity** | ❌ Low | ✅ High | ✅ High |
| **Best model** | Gemini Flash | Claude Opus | Mix |
| **Deep thinking** | Limited | ✅ Best | Good |
| **Background work** | ✅ Yes | ❌ No | ❌ No |
| **Debugging** | Hard | Easy | Medium |

---

## Recommended Usage

### For Production/Automation
**Use CLI Mode**
- Set up API keys
- Run flywheel in background
- Check cockpit for approvals
- Best for: repetitive tasks, batch processing, overnight runs

### For Complex Problem Solving
**Use God Mode**
- Single Claude Opus 4.5 session
- Let it think deeply through all perspectives
- Best for: strategy, architecture, complex analysis

### For Learning/Experimentation
**Use UI Mode**
- Cockpit + multiple Antigravity tabs
- See how agents interact
- Best for: understanding the system, debugging, demos

---

## File Reference

| File | Purpose |
|------|---------|
| `agent_manager.py` | CLI flywheel daemon |
| `brain_executor.py` | LLM API caller for CLI mode |
| `cockpit.py` | Streamlit dashboard for UI mode |
| `.brain/agents/*.md` | System prompts for each agent |
| `.brain/ledger/triggers.json` | Event → Agent routing rules |
| `.brain/ledger/events.jsonl` | Event stream (the "nervous system") |
| `.brain/ledger/state.json` | Current system state |

---

## Quick Start by Modality

### CLI Mode Quick Start
```bash
export GEMINI_API_KEY="your_key"
python agent_manager.py sprint "Your goal"
python agent_manager.py start
# Wait... check outputs
python agent_manager.py status
```

### God Mode Quick Start
```
1. Open Antigravity → Claude Opus 4.5
2. Say: "Read .brain/agents/synthesizer.md and become the Synthesizer"
3. Say: "Execute current sprint from .brain/ledger/state.json"
4. Let it work through all agents
```

### UI Mode Quick Start
```bash
streamlit run cockpit.py
# Open browser to localhost:8501
# Use LAUNCH tab to start sprint
# Watch ACTIVITY for events
# Open separate Antigravity chats per agent
```

---

*This document is the source of truth for execution modalities.*  
*Location: `.brain/workflows/execution_modalities.md`*
