# Lead Agent Model: Multi-Tool Coordination
> **Date:** December 30, 2025  
> **Status:** Active

---

## The Problem with Strict Roles

| Strict Model (Windsurf's Bootstrap) | Reality |
|:------------------------------------|:--------|
| Antigravity = Code only | You do strategy here too |
| Windsurf = Strategy only | It also handles code (CI/CD) |
| Context lives in one place | You switch mid-session |

**Strict separation causes context fragmentation.**

---

## Lead Agent Model

### Principle
> **Whoever you're talking to RIGHT NOW is the Lead Agent.** The other is Async Support.

### How It Works

| Your Focus | Lead (Active) | Async (Background) |
|:-----------|:--------------|:-------------------|
| Feature coding | Antigravity | Windsurf (CI/CD if needed) |
| Strategy session | Antigravity | — |
| DevOps/Release | Windsurf | — |
| Research task | Gemini CLI | Both idle |

---

## State Sync Protocol

Both tools stay coordinated via `.brain/`:

```
┌─────────────────┐         ┌─────────────────┐
│   Antigravity   │         │    Windsurf     │
│   (Lead Now)    │         │    (Async)      │
└────────┬────────┘         └────────┬────────┘
         │                           │
         ▼                           ▼
    ┌─────────────────────────────────────┐
    │          .brain/ledger/             │
    │  ├── state.json (current sprint)    │
    │  └── events.jsonl (task log)        │
    └─────────────────────────────────────┘
```

**Before starting work in either tool:**
```bash
cat .brain/ledger/state.json  # Check current state
```

**After completing work:**
```bash
# Append to events.jsonl
```

---

## Handoff Protocol

### Cold Start (New Session)
```
1. Read state.json
2. Ask: "What's the current sprint?"
3. Become Lead Agent for that session
```

### Warm Handoff (Mid-Task)
When you need to switch tools:
1. State clearly: "Handing off to [other tool] for [reason]"
2. Paste context summary in other tool
3. Other tool becomes Lead Agent

### No Handoff Needed
If both tools have MCP access to `.brain/`, they can read state independently. No manual paste needed.

---

## Role Capabilities (Not Restrictions)

| Capability | Antigravity | Windsurf | Gemini CLI |
|:-----------|:-----------:|:--------:|:----------:|
| Code | ✅ | ✅ | ❌ |
| Strategy | ✅ | ✅ | ❌ |
| Research | ✅ | ✅ | ✅ |
| CI/CD | ✅ | ✅ (primary) | ❌ |
| MCP Access | ✅ | ✅ | Configurable |
| Proactive Lead | ✅ | ✅ | Cron-triggered |

**Key difference from Windsurf's model:** No hard restrictions, just preferences.

---

## Daily Workflow Example

| Time | Activity | Lead Agent |
|:-----|:---------|:-----------|
| 9:00 | Check state, plan day | Antigravity |
| 9:30 | Feature coding | Antigravity |
| 11:00 | Hit rate limit | Switch to Windsurf |
| 12:00 | CI/CD pipeline fix | Windsurf continues |
| 14:00 | Strategy session | Antigravity (fresh) |
| 16:00 | Reddit comments | Perplexity (separate) |
| 17:00 | Research runs | Gemini CLI (cron) |

---

## Summary

| Model | Pros | Cons |
|:------|:-----|:-----|
| **Strict Separation** | Clear roles | Context lost on switch |
| **Lead Agent (This)** | Fluid, context-preserved | Requires state discipline |

**Recommendation:** Use Lead Agent Model with `.brain/` sync.
