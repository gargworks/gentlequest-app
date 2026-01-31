# NOP V3.1 Feature Prioritization Matrix
## Ship vs Defer Decision Framework
### January 23, 2026 | Phase 6A Deliverable

---

# EXECUTIVE SUMMARY

**Decision Framework:** MoSCoW (Must/Should/Could/Won't) + Impact/Effort Matrix

**Launch Target:** February 1, 2026 (8 days)

**Guiding Principle:** Ship what enables first 50 users. Defer what can wait for user feedback.

---

# PART 1: FEATURE INVENTORY

## 1.1 Track A - Pure Python Core (Complete ✅)

| Component | Lines | Status | v3.1 Ship |
|-----------|-------|--------|-----------|
| CRDT Task Store | ~800 | ✅ Complete | ✅ Ship |
| Task Scheduler | ~600 | ✅ Complete | ✅ Ship |
| Agent Pool | ~700 | ✅ Complete | ✅ Ship |
| Orchestrator V3 | ~500 | ✅ Complete | ✅ Ship |
| **Total Track A** | **~2,600** | ✅ | ✅ |

## 1.2 Track B - MCP Integration (Complete ✅)

| Component | Lines | Status | v3.1 Ship |
|-----------|-------|--------|-----------|
| Task Ingestion Engine | ~1,000 | ✅ Complete | ✅ Ship |
| Dashboard Engine | ~1,000 | ✅ Complete | ✅ Ship |
| Autopilot Engine | ~1,000 | ✅ Complete | ✅ Ship |
| Federation Engine | ~1,000 | ✅ Complete | 🟡 Defer |
| **Total Track B** | **~4,000** | ✅ | 🟡 |

## 1.3 MCP Tools (110+ Tools)

| Category | Count | Status | v3.1 Ship |
|----------|-------|--------|-----------|
| Core brain_* tools | 40+ | ✅ Complete | ✅ Ship |
| Orchestration tools | 15+ | ✅ Complete | ✅ Ship |
| Autopilot tools | 10+ | ✅ Complete | ✅ Ship |
| Dashboard tools | 10+ | ✅ Complete | ✅ Ship |
| Ingestion tools | 5+ | ✅ Complete | ✅ Ship |
| Federation tools | 7+ | ✅ Complete | 🟡 Defer |
| Memory tools | 10+ | ✅ Complete | ✅ Ship |
| Session tools | 8+ | ✅ Complete | ✅ Ship |
| **Total MCP Tools** | **110+** | ✅ | 🟡 |

---

# PART 2: MoSCoW CLASSIFICATION

## MUST HAVE (Feb 1 Launch)

These features are **non-negotiable** for launch. Without them, users cannot get value.

| Feature | Rationale | Status |
|---------|-----------|--------|
| `pip install mcp-server-nucleus` | Entry point for all users | ✅ v0.4.0 live |
| `brain_session_start()` | First command users run | ✅ Complete |
| `brain_add_task()` | Core value proposition | ✅ Complete |
| `brain_list_tasks()` | View what's pending | ✅ Complete |
| `brain_orchestrate()` | Multi-agent coordination | ✅ Complete |
| CRDT Task Store | Persistent, conflict-free | ✅ Complete |
| Event Logging | Audit trail | ✅ Complete |
| Session Management | Save/resume context | ✅ Complete |
| README.md | Users need docs | 🟡 Needs polish |
| Quick Start Guide | 5-minute onboarding | 🟡 Not created |

## SHOULD HAVE (Feb 1 Launch)

These features significantly improve user experience but users can survive without them.

| Feature | Rationale | Status |
|---------|-----------|--------|
| `brain_autopilot_sprint_v2()` | Autonomous execution | ✅ Complete |
| `brain_dashboard()` | Visibility | ✅ Complete |
| `brain_ingest_tasks()` | Import from other sources | ✅ Complete |
| Dockerfile | Easy deployment | 🟡 Not created |
| docker-compose.yml | Full stack deploy | 🟡 Not created |
| Health endpoint | Monitoring | 🟡 Partial |
| API Reference | Developer docs | 🟡 Not created |

## COULD HAVE (v3.2 Post-Launch)

These features would be nice but can absolutely wait for user feedback.

| Feature | Rationale | Defer To |
|---------|-----------|----------|
| Federation Engine | Multi-brain coordination | v3.2 |
| mTLS Security | Overkill for local-first | v3.2 |
| OAuth/RBAC | Enterprise feature | v3.2 |
| Prometheus metrics | Advanced monitoring | v3.2 |
| Jaeger tracing | Distributed tracing | v3.2 |
| Agent marketplace | Network effects | v3.2 |

## WON'T HAVE (v4.0+)

These features are out of scope for the foreseeable future.

| Feature | Rationale | Revisit |
|---------|-----------|---------|
| Kubernetes deployment | Docker sufficient for now | v4.0 |
| Multi-region federation | Scale problem we don't have | v4.0 |
| Enterprise SSO | No enterprise customers yet | v4.0 |
| Mobile app | Focus on developer CLI | Never |

---

# PART 3: IMPACT/EFFORT MATRIX

```
                           HIGH IMPACT
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        │  QUICK WINS ✅       │  MAJOR PROJECTS 🟡   │
        │                      │                      │
        │  • brain_session_    │  • Federation        │
        │    start()           │    Engine            │
        │  • brain_add_task()  │  • Kubernetes        │
        │  • brain_list_tasks()│  • Enterprise SSO    │
        │  • CRDT Store        │                      │
        │  • Event Logging     │                      │
LOW     │  • Session Mgmt      │                      │  HIGH
EFFORT  │                      │                      │  EFFORT
        ├──────────────────────┼──────────────────────┤
        │                      │                      │
        │  FILL-INS 🟢         │  THANKLESS TASKS ❌  │
        │                      │                      │
        │  • README polish     │  • Full test suite   │
        │  • Quick Start guide │  • Perf optimization │
        │  • Dockerfile        │  • Code refactoring  │
        │  • Health endpoint   │  • 100% coverage     │
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                           LOW IMPACT
```

**Prioritization:**
1. **Quick Wins** (High Impact, Low Effort) → Ship immediately ✅
2. **Fill-Ins** (Low Impact, Low Effort) → Ship if time permits 🟢
3. **Major Projects** (High Impact, High Effort) → Defer to v3.2 🟡
4. **Thankless Tasks** (Low Impact, High Effort) → Deprioritize ❌

---

# PART 4: DETAILED FEATURE ANALYSIS

## 4.1 Core Tools (MUST SHIP ✅)

### brain_session_start()
- **Impact:** Critical (first command users run)
- **Effort:** Done
- **Decision:** SHIP ✅
- **Notes:** Returns briefing with pending tasks, identity, recommendations

### brain_add_task()
- **Impact:** Critical (core value proposition)
- **Effort:** Done
- **Decision:** SHIP ✅
- **Notes:** Creates tasks with priority, dependencies, skills

### brain_orchestrate()
- **Impact:** High (multi-agent coordination)
- **Effort:** Done
- **Decision:** SHIP ✅
- **Notes:** The "God command" - auto-assigns best task to slot

### brain_autopilot_sprint_v2()
- **Impact:** High (autonomous execution)
- **Effort:** Done
- **Decision:** SHIP ✅
- **Notes:** Runs sprints without human in loop

### brain_dashboard()
- **Impact:** Medium (visibility)
- **Effort:** Done
- **Decision:** SHIP ✅
- **Notes:** ASCII visualization of system state

## 4.2 Infrastructure (MUST SHIP ✅)

### CRDT Task Store
- **Impact:** Critical (persistence, conflict-free)
- **Effort:** Done (800 lines)
- **Decision:** SHIP ✅
- **Notes:** 423K tasks/sec, survives concurrent writes

### Task Scheduler
- **Impact:** High (prioritization)
- **Effort:** Done (600 lines)
- **Decision:** SHIP ✅
- **Notes:** Dependency-aware, skill-matching

### Agent Pool
- **Impact:** High (resource management)
- **Effort:** Done (700 lines)
- **Decision:** SHIP ✅
- **Notes:** Slot registry, utilization tracking

### Orchestrator V3
- **Impact:** Critical (integration point)
- **Effort:** Done (500 lines)
- **Decision:** SHIP ✅
- **Notes:** Unifies all components

## 4.3 Deployment (SHOULD SHIP 🟡)

### Dockerfile
- **Impact:** Medium (easy deployment)
- **Effort:** Low (2-4 hours)
- **Decision:** SHIP 🟡
- **Phase:** 6B
- **Notes:** Single-command install for Docker users

### docker-compose.yml
- **Impact:** Medium (full stack deploy)
- **Effort:** Low (1-2 hours)
- **Decision:** SHIP 🟡
- **Phase:** 6B
- **Notes:** MCP server + example configuration

### Health Endpoint
- **Impact:** Low-Medium (monitoring)
- **Effort:** Low (1 hour)
- **Decision:** SHIP 🟡
- **Phase:** 6B
- **Notes:** /health returns status, version, uptime

## 4.4 Documentation (SHOULD SHIP 🟡)

### README.md
- **Impact:** High (first impression)
- **Effort:** Medium (4-6 hours)
- **Decision:** SHIP 🟡
- **Phase:** 6D
- **Notes:** Compelling, clear, comprehensive

### Quick Start Guide
- **Impact:** High (user onboarding)
- **Effort:** Medium (2-4 hours)
- **Decision:** SHIP 🟡
- **Phase:** 6D
- **Notes:** 5-minute path to first value

### API Reference
- **Impact:** Medium (developer docs)
- **Effort:** Medium (4-6 hours)
- **Decision:** SHIP 🟡
- **Phase:** 6D
- **Notes:** All 110+ tools documented

## 4.5 Federation (DEFER to v3.2 🟡)

### Federation Engine
- **Impact:** Low for first 50 users (too advanced)
- **Effort:** Done (1000 lines)
- **Decision:** DEFER 🟡
- **Rationale:** No one needs multi-brain coordination yet
- **Revisit:** After 50+ users request it

### mTLS Security
- **Impact:** Low (overkill for local-first)
- **Effort:** Medium (4-8 hours)
- **Decision:** DEFER 🟡
- **Rationale:** Local-first = no network = no mTLS needed
- **Revisit:** When federation is enabled

### Raft Consensus
- **Impact:** Low (distributed systems feature)
- **Effort:** Done (included in federation.py)
- **Decision:** DEFER 🟡
- **Rationale:** Single-brain is default for v3.1
- **Revisit:** When multi-brain is requested

---

# PART 5: PHASE 6 IMPLEMENTATION SCHEDULE

## Phase 6A: Strategic Integration (Jan 23-24) ✅

| Deliverable | Status | Notes |
|-------------|--------|-------|
| Read 7 GTM files | ✅ Complete | Context absorbed |
| Design Thinking Loops | ✅ Complete | 8 loops, 95% convergence |
| Strategic Integration Doc | ✅ Complete | PHASE_6A_STRATEGIC_INTEGRATION.md |
| Trinity Positioning Guide | ✅ Complete | TRINITY_POSITIONING_GUIDE.md |
| Feature Prioritization | ✅ Complete | This document |

## Phase 6B: Production Hardening (Jan 25-27) 🟡

| Deliverable | Effort | Priority |
|-------------|--------|----------|
| Dockerfile | 2-4h | P0 |
| docker-compose.yml | 1-2h | P0 |
| Health endpoint | 1h | P1 |
| E2E test critical path | 4-6h | P0 |
| Error handling review | 2-3h | P1 |

## Phase 6C: Testing (Jan 28-29) 🟡

| Deliverable | Effort | Priority |
|-------------|--------|----------|
| Verify all 110 tools | 4-6h | P0 |
| Integration tests | 4-6h | P1 |
| Performance validation | 2-3h | P2 |
| Stability testing | 2-3h | P1 |

## Phase 6D: Documentation (Jan 30-31) 🟡

| Deliverable | Effort | Priority |
|-------------|--------|----------|
| README.md polish | 2-3h | P0 |
| Quick Start guide | 2-3h | P0 |
| API Reference | 4-6h | P1 |
| Reddit post finalize | 1h | P0 |
| HN post draft | 1h | P1 |

---

# PART 6: RISK-BASED PRIORITIZATION

## P0 - Launch Blockers (Must Fix)

| Risk | Feature Gap | Fix |
|------|-------------|-----|
| Install fails | MCP config confusing | Quick Start guide |
| No first value | Empty .brain/ | Seed example tasks |
| Crashes | Untested code paths | E2E tests |
| No docs | Users confused | README + Quick Start |

## P1 - User Experience (Should Fix)

| Risk | Feature Gap | Fix |
|------|-------------|-----|
| Deployment hard | No Docker | Dockerfile |
| No monitoring | No health check | Health endpoint |
| Incomplete docs | No API reference | API Reference |

## P2 - Nice to Have (Could Fix)

| Risk | Feature Gap | Fix |
|------|-------------|-----|
| Can't scale | No K8s | v3.2 |
| No multi-brain | Federation disabled | v3.2 |
| Advanced monitoring | No Prometheus | v3.2 |

---

# PART 7: DECISION SUMMARY

## v3.1 SHIP (Feb 1, 2026)

### Core (110+ tools)
- ✅ brain_session_start, brain_add_task, brain_list_tasks
- ✅ brain_orchestrate, brain_autopilot_sprint_v2
- ✅ brain_dashboard, brain_ingest_tasks
- ✅ All memory, session, depth tracking tools

### Infrastructure
- ✅ CRDT Task Store (423K ops/sec)
- ✅ Task Scheduler (dependency-aware)
- ✅ Agent Pool (slot management)
- ✅ Orchestrator V3 (integration)
- ✅ Autopilot Engine (autonomous)
- ✅ Dashboard Engine (visualization)
- ✅ Ingestion Engine (multi-source)

### Deployment (Phase 6B)
- 🟡 Dockerfile
- 🟡 docker-compose.yml
- 🟡 Health endpoint

### Documentation (Phase 6D)
- 🟡 README.md (polish)
- 🟡 Quick Start guide (new)
- 🟡 API Reference (new)

## v3.2 DEFER (Post-Launch)

### Federation
- 🟡 Federation Engine (1000 lines, complete but disabled)
- 🟡 SWIM peer discovery
- 🟡 Raft consensus
- 🟡 Merkle sync

### Security
- 🟡 mTLS
- 🟡 OAuth/RBAC
- 🟡 Audit logs

### Scale
- 🟡 Kubernetes
- 🟡 Prometheus/Jaeger
- 🟡 Multi-region

---

# CONCLUSION

**Total Lines of Code:** 18,000+
**Total MCP Tools:** 110+
**Ship for v3.1:** ~103 tools (all except federation)
**Defer to v3.2:** ~7 tools (federation)

**Key Insight:**
The infrastructure is 90% complete. The bottleneck is NOT more features.
The bottleneck is GTM execution (docs, deployment, user onboarding).

**Phase 6 Focus:**
- 6B: Make it installable (Docker)
- 6C: Make it reliable (testing)
- 6D: Make it understandable (docs)

**Then SHIP. Get 50 users. Learn. Iterate.**

---

*Feature Prioritization Matrix | Phase 6A Deliverable*
*Generated: January 23, 2026*
*Decision: SHIP NOW | Confidence: 95%*
