# Clarifying Questions - ALL LOCKED ✅

> **Status:** All decisions finalized (2026-01-05 ~9pm)  
> **Ready to build:** Depth Tracker Tier 1

---

## 1. Depth Tracker (✅ LOCKED)

| Question | Decision | Reasoning |
|:---------|:---------|:----------|
| Indicator visible | **After every response** | "Reminded all the time" for ADHD support |
| Max safe depth | **5 levels** (warn at 3, danger at 4+) | You said "5 viewers around" - allow deep exploration with warnings |
| Session boundary | **Manual reset only** | Preserve pathways, no auto-clearing |
| Storage | `.brain/session/depth.json` | Centralized for future pattern analysis |

**Behavior:**
- 🟢 Level 1-2: Safe (green)
- 🟡 Level 3: Caution warning (yellow)
- 🔴 Level 4-5: Danger zone (red) - strong warnings but NOT blocked

---

## 2. Render Poller (✅ LOCKED)

| Question | Decision | Reasoning |
|:---------|:---------|:----------|
| Service to test | **Auto-discover via API** | RENDER_API_KEY added to .env, will find services |
| Smoke test | `/api/health` | Already implemented, returns JSON status |
| Notifications | **Ledger only** | You said "thinking only" - quiet logging, not spammy |

**Behavior:**
- Log all poll results to `.brain/ledger/events.jsonl`
- Only surface errors/failures visibly (not every success)

---

## 3. Feature Map (✅ LOCKED)

| Question | Decision | Reasoning |
|:---------|:---------|:----------|
| Feature ID format | **Hybrid** | Auto-suggest, user can override |
| Initial features | **Expand later** | Start minimal, add as needed |

---

## 4. Proof System (✅ LOCKED - Deferred)

| Question | Decision | Reasoning |
|:---------|:---------|:----------|
| Commit format | System infers | Fallback to template if not found |
| Rollback risk | **Default "Low"** | Most changes additive |

> **Note:** You said "more information later" - Proof System is lowest priority for now. Depth Tracker > Render Poller > Feature Map > Proof System.

---

## 5. Priority Order (✅ LOCKED)

1. **Depth Tracker Tier 1** (2-3h) - Priority #0, most important
2. **Render Poller** (2-4h) - After Depth Tracker
3. **Feature Map** (1-2h) - Expand later
4. **Proof System** (3-4h) - Deferred, want more info

---

## 6. Technical (✅ LOCKED)

| Question | Decision |
|:---------|:---------|
| Python version | 3.9+ (compatibility) |
| Testing strategy | **Hybrid** - Unit tests for Depth Tracker logic, manual for rest |
| Version naming | **Incremental** - Keep simple, early user, don't overthink |

---

## Summary: What I Heard

From your voice input:
1. ✅ Render API key added - will auto-discover services
2. ✅ Notifications: Ledger only (not both) - quiet logging
3. ✅ Feature ID: Hybrid, expand later
4. ✅ Proof System: Default low, want more info later (deferred)
5. ✅ Depth Tracker is #1 priority, more important than all others
6. ✅ Max depth: 5 allowed, with warnings starting at 3
7. ✅ Version naming: Incremental, keep simple
8. ✅ Testing: Hybrid (unit + manual)

---

## Ready to Build

**Next step:** Implement Depth Tracker Tier 1 (2-3h)

All questions answered. No blockers.
