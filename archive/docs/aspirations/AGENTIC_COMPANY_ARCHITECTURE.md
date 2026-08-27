# Agentic Company Architecture
> **For:** Solo Founders Running AI-First Startups  
> **Derived From:** First Principles + Research on Multi-Agent Systems  
> **Date:** December 26, 2025

---

## The Core Insight

> **"Agents coordinate through artifacts, not conversations. The founder is not the orchestrator of agents, but the curator of artifacts."**

---

## First Principles Derivation

### Axioms

1. **Information is the substrate of all coordination** — Agents need shared context to work together
2. **Founder attention is the scarcest resource** — Cannot supervise every agent interaction  
3. **Asynchronous > Synchronous for scale** — Real-time agent collaboration is complex; async via artifacts is simple and auditable

### The Problem with Direct Agent-to-Agent Communication

```
Agent A → Agent B → Agent C

Each hop = information loss (compression, hallucination, context drift)
No audit trail
No way for founder to see what happened
New agent must be re-explained everything
```

### The Solution: Document-Centric Architecture

```
Agent A → ARTIFACT ← Agent B ← ARTIFACT ← Agent C
              ↑
          FOUNDER
        (reviews diffs)
```

- **Source of truth persists** in artifacts
- **Founder reviews diffs**, not agent chatter
- **New agents inherit full context** from artifacts
- **Auditability built-in** via version control

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FOUNDER (You)                             │
│                                                                   │
│   • Reviews artifact changes (code, docs, content)               │
│   • Makes critical decisions at checkpoints                      │
│   • Synthesizes insights across domains weekly                   │
│   • Updates shared strategy based on learnings                   │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SHARED ARTIFACT LAYER                         │
│                                                                   │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│   │   Strategy   │ │     Code     │ │     Data     │            │
│   │   Documents  │ │   Repository │ │   & Metrics  │            │
│   │              │ │              │ │              │            │
│   │ • Roadmaps   │ │ • Python/    │ │ • PostgreSQL │            │
│   │ • Specs      │ │   Dart files │ │ • Analytics  │            │
│   │ • Plans      │ │ • Tests      │ │ • User       │            │
│   │ • Pitches    │ │ • Configs    │ │   feedback   │            │
│   └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                   │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                   Knowledge Base                          │  │
│   │   • Decision logs  • Context docs  • Learnings           │  │
│   └──────────────────────────────────────────────────────────┘  │
└───────────┬───────────────┬───────────────┬───────────────┬──────┘
            │               │               │               │
            ▼               ▼               ▼               ▼
    ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
    │  BACKEND  │   │  MOBILE   │   │ STRATEGY  │   │  GROWTH   │
    │   Thread  │   │  Thread   │   │  Thread   │   │  Thread   │
    │           │   │           │   │           │   │           │
    │ Reads:    │   │ Reads:    │   │ Reads:    │   │ Reads:    │
    │ • API     │   │ • Designs │   │ • Metrics │   │ • Strategy│
    │   specs   │   │ • Specs   │   │ • Feedback│   │ • Analytics│
    │           │   │           │   │           │   │           │
    │ Writes:   │   │ Writes:   │   │ Writes:   │   │ Writes:   │
    │ • Python  │   │ • Dart    │   │ • Plans   │   │ • Content │
    │ • Tests   │   │ • Widgets │   │ • Docs    │   │ • Emails  │
    └───────────┘   └───────────┘   └───────────┘   └───────────┘
```

---

## Why This Pattern Wins (Comparison)

| Pattern | Description | Verdict |
|---------|-------------|---------|
| **Hierarchical** | Meta-agent orchestrates workers | ❌ Meta-agent = bottleneck, founder loses visibility |
| **Decentralized** | Agents talk peer-to-peer | ❌ Coordination chaos, no clear owner |
| **Hub-and-Spoke** | Founder is hub, agents are spokes | ❌ Founder becomes bottleneck |
| **Document-Centric** | Agents share artifacts, founder reviews | ✅ Async, auditable, scalable |

### Document-Centric Advantages

| Property | Why It Matters |
|----------|----------------|
| **Auditability** | Every decision documented in artifacts |
| **Continuity** | Context persists across sessions/days |
| **Parallelism** | Agents work independently, no blocking |
| **Quality** | Artifacts are reviewed, refined over time |
| **Scalability** | Add more agents, same pattern works |

---

## Artifact Ownership Matrix

| Artifact Type | Primary Writer | Readers | Review Trigger |
|---------------|---------------|---------|----------------|
| Strategy docs | Strategy Thread | All threads | Weekly |
| API specs | Backend Thread | Mobile, Strategy | Before implementation |
| UI designs | Mobile Thread | Backend | Before implementation |
| Code files | Backend/Mobile | All | PR review |
| Content drafts | Growth Thread | Strategy | Before publishing |
| Analytics data | System | All threads | On-demand |
| Roadmaps | Strategy Thread | All threads | Monthly |

---

## Founder Checkpoints (When to Review)

| Decision Type | Review Required | Approval Need |
|---------------|-----------------|---------------|
| **Design decisions** | Before major code changes | Yes |
| **Public content** | Before publishing | Yes |
| **User communications** | Before sending | Yes |
| **Budget/spend** | Always | Yes |
| **Routine code** | Post-commit | Optional |
| **Internal docs** | Async review | Optional |

---

## Weekly Sync Ritual

The founder is the only entity that sees across all threads. Weekly synthesis is critical.

### Monday: Cross-Thread Review (1 hour)
1. **Backend Thread:** What shipped? What's blocked?
2. **Mobile Thread:** UI changes? New screens?
3. **Strategy Thread:** Roadmap changes? Investor updates?
4. **Growth Thread:** What content performed? What outreach sent?

### Synthesis Actions
- Update `strategy.md` with cross-thread insights
- Resolve any conflicting priorities
- Set next week's focus for each thread

---

## Practical Implementation for GentleQuest

### Current State
```
ai-mvp-backend/
├── docs/                          ← Strategy Thread artifacts
│   ├── strategy.md
│   ├── STRATEGIC_AI_CAPABILITIES_ROADMAP.md
│   ├── AGENTIC_SOLO_FOUNDER_PLAYBOOK.md
│   └── AGENTIC_COMPANY_ARCHITECTURE.md (this file)
├── providers/                     ← Backend Thread artifacts
│   ├── gemini.py
│   ├── memory.py
│   └── session_memory.py
├── ai_buddy_web/lib/              ← Mobile Thread artifacts
│   ├── screens/
│   └── widgets/
└── growth/                        ← Growth Thread (to create)
    ├── reddit_posts/
    └── outreach_emails/
```

### Thread Responsibilities

| Thread | Domain | Artifacts | Frequency |
|--------|--------|-----------|-----------|
| **Backend** | AI capabilities, API, deployment | `providers/`, `app.py`, tests | Daily during sprints |
| **Mobile** | UI, app features, animations | `ai_buddy_web/lib/` | Daily during sprints |
| **Strategy** | Planning, investors, roadmap | `docs/*.md` | 2-3x/week |
| **Growth** | Content, outreach, marketing | `growth/` (future) | 2-3x/week |

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Agent chatting** | Decisions lost, no audit trail | Write decisions to docs |
| **Founder as bottleneck** | Everything waits for approval | Define approval tiers |
| **Siloed threads** | No cross-pollination | Weekly sync ritual |
| **Abandoned artifacts** | Stale docs cause confusion | Date + review cadence |
| **Oral tradition** | "We discussed this" but not documented | If not written, didn't happen |

---

## Scaling the Architecture

### Phase 1: Current (3 Threads)
```
Backend + Mobile + Strategy
```
- Covers product development
- Founder can context-switch between 3 domains

### Phase 2: Growth Mode (4 Threads)
```
Backend + Mobile + Strategy + Growth
```
- Add when ready for active user acquisition
- Growth reads Strategy, writes Content

### Phase 3: Scale Mode (5-6 Threads)
```
+ Operations/Finance (grants, metrics, legal)
+ Partnerships/BD (enterprise, universities)
```
- Add as business complexity grows
- Each thread = clear artifact ownership

---

## Conway's Law Application

> "Organizations produce designs that are copies of their communication structures."

| Traditional Org | Agentic Org |
|-----------------|-------------|
| Team structure → Software architecture | Agent structure → System capabilities |
| Meetings → Decisions | Agent work → Artifact updates |
| Institutional memory | Knowledge base artifacts |

**Implication:** To build modular, well-integrated capabilities, structure modular, artifact-connected agents.

---

## Validation: Why This Is Already Working

This document describes the pattern we're **already using**:

1. **Separate threads** = Independent agents with bounded domains
2. **Shared filesystem** = Artifact layer for coordination  
3. **You review changes** = Founder checkpoint
4. **Agents don't talk to each other** = No hidden state
5. **Context flows through docs** = Each thread reads existing artifacts

**This is proof the pattern works.** This document formalizes what emerged naturally.

---

## Research References

This architecture synthesizes insights from:

- **Multi-Agent Architecture Patterns:** Orchestrator-Specialist, Hierarchical, Decentralized, Actor-Critic
- **Conway's Law:** System design reflects org structure
- **Solo Founder AI-First Model:** 36% of 2024 startups are solo-founded
- **GitOps Principles:** Infrastructure/operations as version-controlled artifacts

---

*Created: December 26, 2025*  
*Review: Monthly*  
*Owner: Strategy Thread*
