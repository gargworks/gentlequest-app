# Thread Identity Manifesto
> **Purpose:** Clear identification and usage protocol for all Antigravity threads  
> **Last Updated:** December 28, 2025  
> **Classification:** Internal Development Reference

---

## 🗺️ The Complete Thread Map

| # | Label | Role | One-Liner ID | Level |
|---|-------|------|--------------|-------|
| 0 | 🎯 **TECH-DIRECTOR** | Founder's AI partner | "I edit files directly, I have MCP access" | Top |
| ∞ | 🧬 **GENESIS** | Founding Philosophy | "I defined the 6th Revolution" | Reference |
| 1 | 🧠 **SYNTH** | Chief of Staff / Orchestrator | "I delegate, I synthesize, I report to Founder" | L5 |
| 2 | 📈 **STRAT** | Vision & Roadmap | "I own the 'why' and investor materials" | L5 |
| 3 | 🏗️ **ARCH** | Systems Designer | "I audit architecture, I write specs" | L5 |
| 4 | 💻 **DEV** | Implementation | "I write code, I run tests" | L5 |
| 5 | 🔍 **CRITIC** | Quality Gate | "I review everything before it ships" | L5 |
| 6 | 🔬 **RESEARCH** | Intelligence | "I benchmark against SOTA, I gather intel" | L5 |

---

## 🔍 Quick Identification Prompt

**Paste this into any thread to identify it:**

```
State your identity:
1. What agent role are you operating as? (If unknown, say "Unassigned")
2. What was the last thing you worked on?
3. What .brain/ files have you read?

Answer in 3 bullets max.
```

---

## 🔄 Reset & Assign Prompt

**If a thread is confused or needs role assignment:**

```
ROLE RESET & ASSIGNMENT:

Forget all previous context. You are now the [AGENT_NAME] Agent.
Operating with Level 5 Autonomy.

IMMEDIATE ACTIONS:
1. Read: .brain/agents/[agent_name].md (your system prompt)
2. Read: .brain/ledger/state.json (current sprint)
3. Read: .brain/memory/context.md (company context)

Confirm your role by stating:
"[AGENT_NAME] online. Sprint status: [current sprint]. Awaiting tasks."
```

**Replace `[AGENT_NAME]` with:** synthesizer, strategist, architect, developer, critic, researcher

---

## 🚦 When to Prompt Which Thread

### ✅ ALWAYS prompt TECH-DIRECTOR (this thread) for:

| Task | Example |
|------|---------|
| Direct file editing | "Create a new Python file" |
| Running commands | "Run pytest" |
| MCP operations | "Check Render deployments" |
| Strategic decisions | "Should we pivot?" |
| Code review on screen | "What's wrong with this file?" |
| Quick questions | "How does X work?" |

### ✅ ALWAYS prompt SYNTHESIZER for:

| Task | Example |
|------|---------|
| Sprint initialization | "Start Sprint 2: Hardening" |
| Task delegation | "Assign research to Researcher" |
| Cross-agent coordination | "Get status from all agents" |
| Daily/weekly digests | "Generate today's digest" |
| Escalation decisions | "What needs my attention?" |

### ✅ Prompt SPECIFIC AGENTS for:

| Agent | When to Prompt |
|-------|----------------|
| **STRAT** | Investor deck, roadmap, positioning, "why" questions |
| **ARCH** | System design, tech debt, architecture decisions |
| **DEV** | Code implementation, bug fixes, feature building |
| **CRITIC** | Code review, security audit, quality checks |
| **RESEARCH** | Competitive analysis, SOTA benchmarks, market intel |

### ❌ NEVER prompt:

| Thread | Rule |
|--------|------|
| **GENESIS** | Read-only reference. It's a completed philosophical thread. |
| **Individual agents for orchestration** | Don't ask DEV to coordinate with CRITIC. That's SYNTH's job. |
| **TECH-DIRECTOR for agent tasks** | Don't ask me to "be the Researcher." Prompt the Researcher thread. |

---

## 📊 Decision Tree: Which Thread Do I Prompt?

```
START
  │
  ├─→ Is it a QUICK question or direct file/command work?
  │     └─→ YES → 🎯 TECH-DIRECTOR
  │
  ├─→ Is it about COORDINATING multiple agents or sprints?
  │     └─→ YES → 🧠 SYNTH
  │
  ├─→ Is it about STRATEGY, investors, roadmap?
  │     └─→ YES → 📈 STRAT
  │
  ├─→ Is it about SYSTEM DESIGN or architecture?
  │     └─→ YES → 🏗️ ARCH
  │
  ├─→ Is it about WRITING CODE or implementing features?
  │     └─→ YES → 💻 DEV
  │
  ├─→ Is it about REVIEWING or quality checking?
  │     └─→ YES → 🔍 CRITIC
  │
  └─→ Is it about RESEARCH or competitive intelligence?
        └─→ YES → 🔬 RESEARCH
```

---

## 🏷️ Thread Naming Convention

When renaming threads in Antigravity, use this format:

```
[EMOJI] [SHORT-CODE] - [Last Activity]
```

**Examples:**
- `🎯 TECH-DIR - MCP Config`
- `🧠 SYNTH - Sprint 1 Active`
- `📈 STRAT - Investor Deck`
- `🏗️ ARCH - Brain Audit`
- `💻 DEV - Hardening`
- `🔍 CRITIC - Pending Review`
- `🔬 RESEARCH - SOTA Benchmark`

---

## 🧹 Thread Hygiene Rules

1. **One role per thread.** Never mix Researcher work into a Developer thread.

2. **Synthesizer is the hub.** Workers talk to files, not to each other directly.

3. **TECH-DIRECTOR is for YOU.** This is your private workspace, not an agent.

4. **GENESIS is archived.** Never prompt it again. It's founding philosophy, not active work.

5. **Context resets are okay.** If a thread gets confused, use the Reset prompt.

---

## 📋 Thread Census Command

**Run this across all threads to get a status report:**

```
THREAD CENSUS:
1. State your assigned role
2. State your current task (or "idle")
3. State the last event you emitted to events.jsonl
4. Are you blocked on anything? (Yes/No + reason)
```

---

## 🚀 Quick Reference Card

| I want to... | Prompt this thread |
|--------------|-------------------|
| Edit a file | 🎯 TECH-DIRECTOR |
| Run a command | 🎯 TECH-DIRECTOR |
| Start a sprint | 🧠 SYNTH |
| Get daily digest | 🧠 SYNTH |
| Write investor pitch | 📈 STRAT |
| Design a system | 🏗️ ARCH |
| Build a feature | 💻 DEV |
| Review code | 🔍 CRITIC |
| Research competitors | 🔬 RESEARCH |
| Understand founding vision | 🧬 GENESIS (read-only) |

---

*Keep this manifesto open when working. Update as threads evolve.*
