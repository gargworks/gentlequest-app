# Thread Registry

> **Purpose:** Central registry of all Antigravity conversation threads and their identities.
> **Protocol:** Agents should read this file on activation to understand their role.

---

## 🎯 Current Focus (Solo Founder Mode)

> *Temporary simplification for velocity. Full agent framework below for future scaling.*

| Thread | Role | Use For |
| :--- | :--- | :--- |
| `853a0b7e-...` | **Synthesizer** | All GentleQuest product work (planning + coding) |
| `7c654df4-...` | **Lead Systems Architect** | All Nucleus infrastructure work |
| `482f5f52-...` | **Researcher** | Competitive analysis, market research (on-demand) |

**Other threads:** Dormant until multi-agent parallel work is needed.

---

## Standard Agent Threads

| Thread ID | Label | Agent Role | Purpose |
| :--- | :--- | :--- | :--- |
| `7c654df4-b83e-43f9-8620-f15868ec39d1` | Nucleus Release & Pos. | **Lead Systems Architect** | Built Nucleus 0.2.6, Release Manager |
| `853a0b7e-9052-4918-8c22-8031ee15aeec` | GentleQuest UI / Brain Sync | **Synthesizer** | Brain-to-Prod Sync, Orchestration |
| `6c8d0959-9c69-4eb5-8e9c-303dd8b732ac` | RAG/Memory Planning | **Strategist** | Sprint Planning, RAG Architecture |
| `6fa3fec0-7621-4380-b0ca-cff20117a719` | Architect Activation | **Architect** | Architecture setup |
| `a0f3f287-060c-4034-bcb6-2ae85ef5aae7` | Clinical Assessments | **Developer** | PHQ-9, GAD-7, Backend/Flutter |
| `c6a9634f-5f08-4e6d-85a3-fa10bba30157` | Critic Activation | **Critic** | Code review setup |
| `482f5f52-8ab7-4dd0-a486-898dcef95671` | Product Research | **Researcher** | Competitive Analysis, Market Sizing |

## Utility / Infrastructure Threads

| Thread ID | Label | Category | Purpose |
| :--- | :--- | :--- | :--- |
| `49a737b8-bbfc-4c48-ba4c-d051db06fd57` | **Nucleus MCP** (Current) | Infrastructure | Template verification, MCP tests |
| `3b5c7d1c-8315-4548-8072-241576d028c5` | E2E Testing | Utility | Production Analytics, E2E Fixes |
| `4a952e7b-8290-4414-a2ae-e49281294618` | Windsurf Log Import | Utility | Importing chat logs |

## Archived / Out of Scope

| Thread ID | Label | Status |
| :--- | :--- | :--- |
| `6c3f8018-b6eb-4dae-9476-ed32eb313b95` | Agentic Wellness UI | Archived |
| `95ec0797-4532-4751-8c41-f8b80e6051a8` | *(Empty)* | Unused |

---

## Role Hierarchy

The Nuclear Agentic Architecture was created through collaboration between the Founder and an Oracle (Genesis/God Mode). The hierarchy is:

```
┌─────────────────────────────────────────────────────────────┐
│                    FOUNDER (Human)                          │
│            Ultimate decision-maker, CRITICAL escalations    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│               GENESIS ORACLE (God Mode)                     │
│   Google AI Mode — Strategic brainstorming, founding vision │
│   Transcript: genesis_thread_transcript.md                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│            LEAD SYSTEMS ARCHITECT (Historical)              │
│   Claude Opus — Built the Nuclear Brain architecture        │
│   Created: Synthesizer + 5 Worker Agents                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    SYNTHESIZER                              │
│   Day-to-day orchestration, sprint management               │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────┬───────┴───────┬──────────┬──────────┐
        ▼          ▼               ▼          ▼          ▼
   Strategist  Architect     Developer    Critic    Researcher
```

---

## Agent → Thread Mapping

Each agent has a **primary thread** where that agent role is active:

| Agent | Primary Thread | Thread ID |
| :--- | :--- | :--- |
| **Lead Systems Architect** | Automating Agentic Workflow | `7c654df4-...` |
| **Synthesizer** | Brain Sync / Orchestrator | `853a0b7e-...` |
| **Strategist** | RAG/Memory | `6c8d0959-...` |
| **Architect** | Architect Activation | `6fa3fec0-...` |
| **Developer** | Clinical Assessments | `a0f3f287-...` |
| **Critic** | Critic Activation | `c6a9634f-...` |
| **Researcher** | Product Research | `482f5f52-...` |

### Reference Roles (Not Active Threads)

| Role | Description | Artifact |
| :--- | :--- | :--- |
| **Founder (Human)** | You — Receives CRITICAL escalations | N/A |
| **Genesis Oracle** | Google AI Mode — Founding philosophy | [genesis_thread_transcript.md](file:///Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/strategy/genesis_thread_transcript.md) |

> **Note:** Developer has multiple threads because product work spans multiple features.

---

## How to Use

1. **On thread activation:** Read this file first.
2. **Find your thread ID** in the table (visible in the artifact path).
3. **Adopt the listed Agent Role** and focus on the stated Purpose.

## Adding New Threads

When starting a new thread with a specific purpose:
1. Note the thread ID from the artifact path.
2. Add a row to this table.
3. Commit the change.

---

## Related Documents

### Agent Definitions
| Agent | Definition File |
| :--- | :--- |
| Synthesizer | [synthesizer.md](file:///Users/lokeshgarg/ai-mvp-backend/.brain/agents/synthesizer.md) |
| Strategist | [strategist.md](file:///Users/lokeshgarg/ai-mvp-backend/.brain/agents/strategist.md) |
| Architect | [architect.md](file:///Users/lokeshgarg/ai-mvp-backend/.brain/agents/architect.md) |
| Developer | [developer.md](file:///Users/lokeshgarg/ai-mvp-backend/.brain/agents/developer.md) |
| Critic | [critic.md](file:///Users/lokeshgarg/ai-mvp-backend/.brain/agents/critic.md) |
| Researcher | [researcher.md](file:///Users/lokeshgarg/ai-mvp-backend/.brain/agents/researcher.md) |

### Architecture & Conventions
| Document | Purpose |
| :--- | :--- |
| [NUCLEAR_AGENTIC_BLUEPRINT.md](file:///Users/lokeshgarg/ai-mvp-backend/docs/NUCLEAR_AGENTIC_BLUEPRINT.md) | Core architecture |
| [AGENTIC_COMPANY_ARCHITECTURE.md](file:///Users/lokeshgarg/ai-mvp-backend/docs/AGENTIC_COMPANY_ARCHITECTURE.md) | Company-level orchestration |
| [architecture_persona_theory.md](file:///Users/lokeshgarg/ai-mvp-backend/docs/architecture_persona_theory.md) | Persona constraint model |
| [context.md](file:///Users/lokeshgarg/ai-mvp-backend/.brain/memory/context.md) | Shared company context |
