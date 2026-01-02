# 🛫 THE FULL AIRCRAFT — System Integration Map
> **Date:** 2026-01-02 02:17 IST
> **Purpose:** One document showing ALL components, their status, and how they connect

---

## 🎯 TWO PRODUCTS, ONE BRAIN

You are building **two products** that share infrastructure:

| Product | Target | Status | Revenue Model |
|---------|--------|--------|---------------|
| **GentleQuest** | B2B Mental Health (Universities, HR) | 🟡 MVP Live | Per-seat licensing |
| **Nucleus** | MCP Brain for AI Agents | 🔴 Pre-PMF | Pro subscriptions |

**Shared Infrastructure:**
- `.brain/` folder structure
- MCP server
- Agent definitions
- Event/trigger system

---

## 🔧 COMPONENT INVENTORY

### GENTLEQUEST COMPONENTS

| Component | File/Location | Status | Stress Test Needed |
|-----------|---------------|--------|-------------------|
| **Production API** | gentlequest.onrender.com | ✅ Healthy | Load test |
| **Luna Chat (Gemini)** | `providers/gemini.py` | ✅ Working | Function call rate |
| **Memory System** | `providers/memory.py` | 🔴 DEAD (pgvector) | Enable extension |
| **Function Calling** | gemini.py:L200+ | ✅ Working | Edge case tests |
| **Flutter UI** | `ai_buddy_web/` | ✅ Built | Production test |
| **Breathing Widget** | `widgets/breathing_exercise_widget.dart` | ✅ Animated | User feedback |
| **Grounding Widget** | `widgets/grounding_exercise_widget.dart` | ✅ Built | Tap flow test |
| **Clinical Assessments** | `PHQ-9, GAD-7` routes | ✅ Implemented | UI integration |
| **Crisis Detection** | 11-country resources | ✅ Working | Edge case validate |
| **Telegram Alerts** | `@gentlequest_alerts_bot` | ✅ Working | Load test |

### NUCLEUS COMPONENTS

| Component | File/Location | Status | Stress Test Needed |
|-----------|---------------|--------|-------------------|
| **MCP Server** | `mcp_server_nucleus/` | ✅ Running | Multi-client test |
| **State Management** | `.brain/ledger/state.json` | 🟡 Stale | Update sprint |
| **Event Ledger** | `.brain/ledger/events.jsonl` | ✅ Working | Replay test |
| **Triggers** | `.brain/ledger/triggers.json` | ✅ Defined | Execution test |
| **6 Agents** | `.brain/agents/*.md` | ✅ Defined | Activation test |
| **Telegram Commands** | `brain_telegram.py` | 🟡 Direct file access | Refactor to MCP |
| **Hub Navigation** | `.brain/NUCLEUS_HUB.md` | ✅ Complete | Keep current |

### SHARED ARTIFACTS (137 files)

| Category | Count | Location | Health |
|----------|-------|----------|--------|
| Research | 14 | `.brain/artifacts/research/` | ✅ Valuable |
| Strategy | 13 | `.brain/artifacts/strategy/` | ✅ Valuable |
| Marketing | 5 | `.brain/artifacts/marketing/` | 🟡 Needs refresh |
| Test | 10 | `.brain/artifacts/test/` | ✅ Reference |
| Synthesis | 4 | `.brain/artifacts/synthesis/` | ✅ Historical |
| Architecture | 5 | `.brain/artifacts/architecture/` | ✅ Reference |
| Docs | 50 | `docs/` | 🟡 Some stale |

---

## 🔴 CRITICAL BLOCKERS (Fix These First)

| # | Issue | Impact | Fix Time | Command |
|---|-------|--------|----------|---------|
| 1 | **pgvector not enabled** | Memory DEAD | 2 min | `psql $DATABASE_URL -c "CREATE EXTENSION vector;"` |
| 2 | **Sprint state stale** | Misleading status | 1 min | Update `state.json` |
| 3 | **Telegram uses direct files** | Can't scale | 2 hours | Refactor to MCP calls |
| 4 | **No user interviews done** | No PMF proof | 1 week | Find 5 users |

---

## 🟡 INTEGRATION GAPS (Wire These Together)

| Gap | From | To | Status |
|-----|------|----|----|
| Memory → Chat | `memory.py` | `gemini.py` | 🔴 Not wired |
| Telegram → MCP | `brain_telegram.py` | MCP Server | 🔴 Direct file |
| Dashboard → State | `dashboard.py` | `state.json` | 🟡 Direct file |
| Flutter → Clinical | UI | `/api/self_assessment` | ⚡ Need button |

---

## ✅ WHAT'S FLYING (Don't Touch)

1. **Production API** - Leave it alone
2. **Function Calling** - Proven working
3. **Crisis Detection** - Life-critical, tested
4. **Agent Definitions** - Well documented
5. **Research Artifacts** - Valuable intel

---

## 🧪 STRESS TEST PLAN

### Phase 1: Enable Core (Tonight)
- [ ] Enable pgvector: `psql $DATABASE_URL -c "CREATE EXTENSION vector;"`
- [ ] Update sprint state
- [ ] Test memory retrieval

### Phase 2: Integration (Tomorrow)
- [ ] Wire memory into gemini.py
- [ ] Test cross-session recall
- [ ] Verify Flutter widgets on prod

### Phase 3: Load Test (This Week)
- [ ] 100 concurrent chat sessions
- [ ] Telegram alert flood test
- [ ] MCP multi-client test

### Phase 4: User Validation (Next Week)
- [ ] 5 user interviews (per board_decision.md)
- [ ] Template feedback
- [ ] Pro waitlist test

---

## 🗺️ THE BOEING 747 VIEW

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              THE INTEGRATED SYSTEM                               │
├──────────────────────────────────────────┬──────────────────────────────────────┤
│          GENTLEQUEST (B2B/B2C)           │           NUCLEUS (Dev Tool)         │
├──────────────────────────────────────────┼──────────────────────────────────────┤
│                                          │                                      │
│  ┌──────────┐  ┌──────────┐              │  ┌──────────┐  ┌──────────┐          │
│  │ Flutter  │  │ Telegram │              │  │ Telegram │  │   CLI    │          │
│  │   Web    │  │  Alerts  │              │  │ Commands │  │ nucleus  │          │
│  └────┬─────┘  └────┬─────┘              │  └────┬─────┘  └────┬─────┘          │
│       │             │                    │       │             │                │
│       └──────┬──────┘                    │       └──────┬──────┘                │
│              │                           │              │                       │
│              ▼                           │              ▼                       │
│     ┌────────────────┐                   │     ┌────────────────┐               │
│     │  Flask API     │                   │     │  MCP SERVER    │               │
│     │  (Render)      │                   │     │  (Local)       │               │
│     └───────┬────────┘                   │     └───────┬────────┘               │
│             │                            │             │                        │
│             ▼                            │             │                        │
│     ┌────────────────┐                   │             │                        │
│     │    GEMINI      │                   │             │                        │
│     │   + Memory     │◄──────────────────┼─────────────┘                        │
│     │   + Functions  │                   │                                      │
│     └───────┬────────┘                   │                                      │
│             │                            │                                      │
│             ▼                            │                                      │
│     ┌────────────────┐                   │     ┌────────────────┐               │
│     │   POSTGRES     │                   │     │    .brain/     │               │
│     │   + pgvector   │                   │     │   (Files)      │               │
│     └────────────────┘                   │     └────────────────┘               │
│                                          │                                      │
└──────────────────────────────────────────┴──────────────────────────────────────┘
```

---

## 🎬 IMMEDIATE ACTIONS (This Session)

1. **Enable pgvector** (2 min)
2. **Update state.json** sprint status (1 min)
3. **Test memory endpoint** after restart (5 min)
4. **Verify this document is the source of truth**

---

## 📚 MASTER INDEX (Where Everything Lives)

| Need | Primary Source |
|------|----------------|
| **What to do NOW?** | This file → CRITICAL BLOCKERS |
| **Strategic direction?** | `.brain/artifacts/strategy/board_decision.md` |
| **Research intel?** | `.brain/artifacts/research/` |
| **How system works?** | `.brain/NUCLEUS_HUB.md` |
| **Secrets & creds?** | `docs/ADMIN_OPS.md` |
| **Implementation roadmap?** | `docs/IMPLEMENTATION_ROADMAP.md` |
| **Investor pitch?** | `docs/STRATEGIC_AI_CAPABILITIES_ROADMAP.md` |
| **Quick ideas?** | Telegram `/idea` → `backlog.md` |

---

*This is the only file you need to open. Everything links from here.*
