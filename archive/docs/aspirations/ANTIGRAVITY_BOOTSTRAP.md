# Antigravity Bootstrap Guide

> **Purpose:** Onboard Antigravity (Technical Creator thread) with full project context.
> **Last Updated:** December 30, 2025

---

## Quick Start (Paste in Antigravity)

```
Read these files in order to understand the full project context:
1. AGENTS.md — The operational constitution (your role is CREATION/Technical Creator)
2. docs/windsurf_chat_history.md — Complete project history (688 lines of decisions, architecture, code changes)

3. .brain/NUCLEUS_HUB.md — Central navigation hub
4. docs/AGENTIC_SOLO_FOUNDER_PLAYBOOK.md — Thread model reference
```

---

## Your Role: Technical Creator

Per AGENTS.md Section 1:

| Domain | Role | Location | Responsibility |
|--------|------|----------|----------------|
| CREATION | Technical Creator | **Antigravity** | The "HOW." Generating code, fixing logic, building files. |

**You handle:**
- Code implementation (Flask backend, Flutter frontend)
- Bug fixes and debugging
- File creation and modification
- Build/deployment commands
- Testing and verification

**You defer to Windsurf (Strategic Architect) for:**
- Roadmap decisions
- Major architecture pivots
- Strategy and "why" questions
- War-gaming and competitive analysis

---

## Key Project Facts

### Tech Stack
- **Frontend:** Flutter (iOS/Android/Web) — `ai_buddy_web/`
- **Backend:** Flask + Gunicorn + Nginx — `app.py`, `providers/`
- **Database:** PostgreSQL (Render, Singapore region) with pgvector
- **AI:** Gemini 2.5 Flash with function calling
- **Hosting:** Render (service ID: `srv-d2r3i1fdiees73dqtov0`)

### Critical Files
| File | Purpose |
|------|---------|
| `app.py` | Main Flask application |
| `providers/gemini.py` | AI chat with function calling |
| `providers/memory.py` | pgvector memory system |
| `providers/session_memory.py` | Intervention variety tracking |
| `nginx.conf` | Reverse proxy config |
| `.brain/ledger/state.json` | Agent state |
| `.brain/ledger/events.jsonl` | Event log |

### Recent Implementation Status
- ✅ Function calling working (breathing, grounding, journaling)
- ✅ Session-aware intervention variety (Stage 1→2→3→4)
- ✅ Crisis detection with geography-specific resources
- ✅ Mobile CI/CD (GitHub Actions for Android/iOS)
- ⏳ RAG memory layer (initialized, needs refinement)

---

## Shared State Protocol

### Reading State
Before starting work, check:
```bash
cat .brain/ledger/state.json
tail -20 .brain/ledger/events.jsonl
```

### Writing State
After completing significant work:
1. Log to `events.jsonl` with your agent ID: `CODE_FORCE`
2. Update `state.json` if sprint/task status changes

### Event Schema
```json
{
  "timestamp": "ISO8601",
  "agent": "CODE_FORCE",
  "event_type": "task_completed|bug_fixed|feature_added",
  "description": "Brief description",
  "files_changed": ["path/to/file"]
}
```

---

## Communication Protocol

### Handoff TO Windsurf (Strategy)
When you encounter:
- "Should we do X or Y?" decisions
- Architecture pivots
- Feature prioritization questions

Say: *"This is a strategy question. Deferring to Strategic Architect thread."*

### Handoff FROM Windsurf
Windsurf will provide tasks like:
- "Implement feature X per spec in docs/Y.md"
- "Fix bug: [description]"
- "Deploy and verify"

---

## Getting Started Checklist

- [ ] Read `AGENTS.md` (constitution)
- [ ] Read `conversation_log.md` (history)
- [ ] Check `.brain/ledger/state.json` (current state)
- [ ] Review recent git commits: `git log --oneline -10`
- [ ] Ask: "What's the current sprint objective?"

---

*This document enables seamless context transfer between AI environments.*
