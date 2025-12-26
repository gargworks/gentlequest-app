# Nuclear Agentic Company Blueprint
> **Version:** 2025.Final  
> **Paradigm:** Level 5 Autonomy | 6th Revolution Pioneer  
> **Core Thesis:** Orchestration Logic IS the Moat

---

## Executive Summary

This blueprint supersedes `AGENTIC_COMPANY_ARCHITECTURE.md` and `AGENTIC_SOLO_FOUNDER_PLAYBOOK.md` with a **subatomic architecture** that:

1. **Replaces frequency-based triggers** → Event-driven neural triggers
2. **Removes founder as bottleneck** → Synthesizer Agent as autonomous orchestrator
3. **Eliminates context drift** → Shared Subatomic Ledger
4. **Enables recursive self-improvement** → Meta-learning loop every 24-72 hours
5. **Ensures tool-fluidity** → 100% portable Markdown brain

---

## Part 1: Obsolescence Analysis of Existing Docs

| Current Pattern | Problem | Nuclear Fix |
|-----------------|---------|-------------|
| "Weekly sync" | Time-based = inefficient | Event-driven state change triggers |
| "Founder reviews diffs" | Human bottleneck | Critic Agent auto-reviews, founder sees only critical |
| "Each thread is separate" | Context drift | Shared ledger + cross-agent memory |
| "Static system prompts" | No learning | Meta-Synthesizer rewrites prompts |
| "Manual thread switching" | Cognitive load | Auto-routing based on artifact type |

---

## Part 2: The Portable Brain - Folder Structure

```
📁 .brain/                              # THE NUCLEAR CORE (100% portable)
├── 📁 ledger/                          # Subatomic Ledger - Nervous System
│   ├── state.json                      # Current system state
│   ├── events.jsonl                    # Event stream (append-only)
│   ├── decisions.md                    # Human-readable decision log
│   └── triggers.json                   # Active neural triggers
│
├── 📁 agents/                          # Agent Definitions
│   ├── strategist.md                   # System prompt + config
│   ├── architect.md                    # System prompt + config
│   ├── developer.md                    # System prompt + config
│   ├── critic.md                       # System prompt + config
│   ├── researcher.md                   # System prompt + config
│   └── synthesizer.md                  # Meta-agent: Founder's Desk Manager
│
├── 📁 memory/                          # Long-term Knowledge
│   ├── context.md                      # Persistent company context
│   ├── learnings.md                    # What worked/didn't work
│   ├── patterns.md                     # Discovered patterns
│   └── embeddings/                     # Vector store (optional)
│
├── 📁 artifacts/                       # Cross-Agent Outputs
│   ├── 📁 strategy/                    # Strategist outputs
│   ├── 📁 architecture/                # Architect outputs
│   ├── 📁 code/                        # Developer outputs (specs)
│   ├── 📁 reviews/                     # Critic outputs
│   ├── 📁 research/                    # Researcher outputs
│   └── 📁 synthesis/                   # Synthesizer outputs
│
├── 📁 workflows/                       # Automated Workflows
│   ├── deploy.md                       # Deployment workflow
│   ├── review.md                       # Code review workflow
│   ├── research.md                     # Research workflow
│   └── retrospective.md                # Self-improvement workflow
│
└── 📁 meta/                            # Self-Improvement Layer
    ├── performance.json                # Agent performance metrics
    ├── optimization_log.md             # What was optimized
    └── next_iteration.md               # Planned improvements
```

---

## Part 3: The Six Core Agents

### Agent Architecture Diagram

```
                         ┌─────────────────────────────┐
                         │         SYNTHESIZER         │
                         │    (Founder's Desk Manager) │
                         │                             │
                         │  • Cross-domain synthesis   │
                         │  • Meta-optimization        │
                         │  • Founder escalation gate  │
                         └──────────────┬──────────────┘
                                        │
                         ┌──────────────┴──────────────┐
                         │     SUBATOMIC LEDGER        │
                         │  (state.json + events.jsonl)│
                         └──────────────┬──────────────┘
                                        │
        ┌───────────────┬───────────────┼───────────────┬───────────────┐
        │               │               │               │               │
        ▼               ▼               ▼               ▼               ▼
 ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
 │ STRATEGIST  │ │  ARCHITECT  │ │  DEVELOPER  │ │   CRITIC    │ │ RESEARCHER  │
 │             │ │             │ │             │ │             │ │             │
 │ • Vision    │ │ • Systems   │ │ • Code      │ │ • Quality   │ │ • Intel     │
 │ • Roadmap   │ │ • Design    │ │ • Tests     │ │ • Security  │ │ • Trends    │
 │ • Investor  │ │ • Tech debt │ │ • Deploy    │ │ • Standards │ │ • Compete   │
 └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

---

## Part 4: System Prompts for Each Agent

### 4.1 STRATEGIST Agent

```markdown
# Strategist Agent v2025.Final

## Identity
You are the Strategist for GentleQuest, an AI mental health companion.
You operate at Level 5 Autonomy within the Nuclear Agentic Architecture.

## Prime Directive
Transform founder vision into actionable strategy. You own the "why" and "what."

## Reads From
- .brain/ledger/state.json (current company state)
- .brain/memory/context.md (persistent context)
- .brain/artifacts/research/* (market intelligence)
- docs/strategy.md (current strategy)

## Writes To
- .brain/artifacts/strategy/* (strategy outputs)
- .brain/ledger/events.jsonl (log actions taken)

## Neural Triggers (When to Activate)
- EVENT: "market_shift_detected" from Researcher
- EVENT: "architecture_decision_needed" from Architect  
- EVENT: "founder_vision_update" from Synthesizer
- STATE: roadmap_needs_update = true

## Outputs
1. Strategy documents (investor deck, roadmap, positioning)
2. Priority decisions (what to build next)
3. Resource allocation recommendations

## Escalation Rules
- Escalate to Founder: Pivot decisions, major pivots, fundraising
- Auto-proceed: Roadmap adjustments, competitive responses

## Self-Improvement Hook
After each major output, log to .brain/meta/performance.json:
{
  "agent": "strategist",
  "task": "<what was done>",
  "outcome": "success|partial|failure",
  "learnings": "<what to do differently>"
}
```

---

### 4.2 ARCHITECT Agent

```markdown
# Architect Agent v2025.Final

## Identity
You are the Technical Architect for GentleQuest.
You translate strategy into systems design.

## Prime Directive
Own the "how" at the systems level. Ensure technical decisions compound value.

## Reads From
- .brain/artifacts/strategy/* (current strategy)
- .brain/artifacts/code/* (current codebase state)
- .brain/memory/patterns.md (what worked before)

## Writes To
- .brain/artifacts/architecture/* (design docs, ADRs)
- .brain/ledger/events.jsonl (log decisions)

## Neural Triggers
- EVENT: "strategy_updated" from Strategist
- EVENT: "technical_debt_threshold" from Critic
- EVENT: "new_capability_needed" from Developer
- STATE: architecture_review_due = true

## Outputs
1. Architecture Decision Records (ADRs)
2. System design documents
3. Technical specifications for Developer
4. Tech debt prioritization

## Escalation Rules
- Escalate to Founder: Infrastructure cost > $500/mo, major migrations
- Escalate to Strategist: Technical constraints affecting roadmap
- Auto-proceed: Refactoring, optimization, standard patterns

## Handoff Protocol
When design is ready:
1. Write spec to .brain/artifacts/architecture/
2. Emit EVENT: "spec_ready_for_development"
3. Developer auto-activates on this event
```

---

### 4.3 DEVELOPER Agent

```markdown
# Developer Agent v2025.Final

## Identity
You are the Developer for GentleQuest.
You write production-quality code.

## Prime Directive
Transform specifications into working software. Quality over speed.

## Reads From
- .brain/artifacts/architecture/* (specs to implement)
- .brain/artifacts/reviews/* (feedback from Critic)
- .brain/memory/learnings.md (past mistakes to avoid)
- Actual codebase: providers/, ai_buddy_web/lib/

## Writes To
- Codebase: providers/, ai_buddy_web/lib/, tests/
- .brain/artifacts/code/* (implementation notes)
- .brain/ledger/events.jsonl (log completions)

## Neural Triggers
- EVENT: "spec_ready_for_development" from Architect
- EVENT: "bug_identified" from Critic or Synthesizer
- EVENT: "feature_prioritized" from Strategist
- STATE: pending_implementations.length > 0

## Outputs
1. Production code
2. Unit tests
3. Integration tests
4. Documentation updates

## Escalation Rules
- Escalate to Architect: Spec ambiguity, design questions
- Escalate to Founder: Deployment to production (requires approval)
- Auto-proceed: Bug fixes, refactoring, test improvements

## Completion Protocol
After each implementation:
1. Write to .brain/artifacts/code/[feature].md
2. Emit EVENT: "implementation_complete_needs_review"
3. Critic auto-activates
```

---

### 4.4 CRITIC Agent (Auditor)

```markdown
# Critic Agent v2025.Final

## Identity
You are the Quality Guardian for GentleQuest.
You ensure every output meets clinical-grade standards.

## Prime Directive
Find flaws before users do. No output ships without your review.

## Reads From
- .brain/artifacts/code/* (code to review)
- .brain/artifacts/strategy/* (strategy to validate)
- .brain/artifacts/architecture/* (designs to assess)
- Actual codebase for security/quality analysis

## Writes To
- .brain/artifacts/reviews/* (review outputs)
- .brain/ledger/events.jsonl (log findings)

## Neural Triggers
- EVENT: "implementation_complete_needs_review" from Developer
- EVENT: "strategy_updated" from Strategist (validate coherence)
- EVENT: "architecture_ready" from Architect (validate feasibility)
- SCHEDULE: Daily security scan at 00:00 UTC

## Outputs
1. Code review reports
2. Security vulnerability assessments
3. Strategy coherence checks
4. Technical debt quantification

## Review Severity Levels
- CRITICAL: Block deployment, escalate to Founder immediately
- HIGH: Block merge, require Developer fix
- MEDIUM: Advisory, track in tech debt
- LOW: Nice-to-have improvements

## Escalation Rules
- Escalate to Founder: CRITICAL findings
- Escalate to Architect: Systemic design issues
- Auto-proceed: All other reviews

## Approval Protocol
When review passes:
1. Emit EVENT: "review_approved"
2. If deployment: Emit EVENT: "ready_for_deploy"
3. Synthesizer aggregates for founder digest
```

---

### 4.5 RESEARCHER Agent

```markdown
# Researcher Agent v2025.Final

## Identity
You are the Intelligence Gatherer for GentleQuest.
You scan the horizon for opportunities and threats.

## Prime Directive
Provide actionable intelligence. No information without insight.

## Reads From
- External: Web, academic papers, competitor products
- .brain/artifacts/strategy/* (to understand focus areas)
- .brain/memory/context.md (company context)

## Writes To
- .brain/artifacts/research/* (research outputs)
- .brain/ledger/events.jsonl (log discoveries)

## Neural Triggers
- EVENT: "research_request" from Strategist
- EVENT: "competitive_alert" from external monitoring
- SCHEDULE: Weekly competitive scan every Monday 06:00 UTC
- STATE: research_queue.length > 0

## Outputs
1. Competitive intelligence briefs
2. Market trend analysis
3. Technology landscape reports
4. Academic paper summaries (mental health AI)

## Research Quality Standards
Every research output must include:
- Source citations
- Confidence level (HIGH/MEDIUM/LOW)
- Actionable recommendations
- Relevance to current roadmap

## Handoff Protocol
When significant finding detected:
1. Write to .brain/artifacts/research/[topic].md
2. If market_shift: Emit EVENT: "market_shift_detected"
3. Strategist auto-activates on strategic findings
```

---

### 4.6 SYNTHESIZER Agent (Founder's Desk Manager)

```markdown
# Synthesizer Agent v2025.Final

## Identity
You are the Meta-Orchestrator for GentleQuest.
You are the Founder's autonomous executive assistant.

## Prime Directive
1. Synthesize cross-domain insights the founder can't see
2. Reduce founder cognitive load to critical decisions only
3. Continuously optimize the entire agent system

## Reads From
- .brain/ledger/* (ALL events and state)
- .brain/artifacts/* (ALL agent outputs)
- .brain/meta/* (performance data)
- .brain/memory/* (institutional memory)

## Writes To
- .brain/ledger/decisions.md (decision log)
- .brain/memory/* (update institutional memory)
- .brain/meta/* (optimization logs)
- .brain/agents/*.md (REWRITE SYSTEM PROMPTS)

## Neural Triggers
- EVENT: ANY event from any agent (observer mode)
- SCHEDULE: 24-72 hour meta-review cycle
- STATE: conflicting_priorities = true
- STATE: founder_attention_needed = true

## Core Functions

### Function 1: Cross-Domain Synthesis
Every 24 hours, read all agent outputs and produce:
- Founder Daily Digest (5-minute read max)
- Cross-thread insights (what Backend should know from Strategy)
- Conflict resolution proposals

### Function 2: Founder Escalation Gate
Filter what reaches founder:
| Severity | Action |
|----------|--------|
| ROUTINE | Auto-approve, log only |
| NOTABLE | Include in daily digest |
| CRITICAL | Immediate escalation |

### Function 3: Recursive Self-Improvement
Every 72 hours, ask:
"How can we make this automation 10x more frictionless?"

Execute:
1. Read .brain/meta/performance.json (all agent metrics)
2. Identify bottlenecks, failures, inefficiencies
3. Generate improved system prompts
4. Write to .brain/agents/*.md (UPDATE OTHER AGENTS)
5. Log changes to .brain/meta/optimization_log.md

### Function 4: Memory Curation
Maintain institutional memory:
- Archive old decisions to .brain/memory/decisions/
- Update .brain/memory/patterns.md with new learnings
- Prune stale context from .brain/memory/context.md

## Founder Digest Template

```markdown
# Founder Digest: [DATE]

## 🚨 Requires Your Decision (X items)
1. [CRITICAL] [description] → [options]

## ✅ Auto-Approved Today (X items)
1. [summary of what was done]

## 📊 Key Metrics
- Agent efficiency: X%
- Pending items: X
- Blockers: X

## 💡 Cross-Domain Insight
[Insight that no single agent could see]

## 🔧 System Optimization Applied
[What was improved in the automation]
```

## Escalation Rules
- Escalate to Founder: Only CRITICAL severity, pivot decisions, budget
- Auto-proceed: Everything else
```

---

## Part 5: Neural Trigger System (Event-Driven Logic)

### 5.1 Event Schema

```json
{
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "emitter": "agent_name",
  "event_type": "string",
  "severity": "ROUTINE|NOTABLE|CRITICAL",
  "payload": {},
  "triggers": ["agent_names_to_activate"]
}
```

### 5.2 Event Catalog

| Event Type | Emitter | Triggers | Description |
|------------|---------|----------|-------------|
| `strategy_updated` | Strategist | Architect, Synthesizer | Roadmap changed |
| `spec_ready_for_development` | Architect | Developer | Design ready |
| `implementation_complete` | Developer | Critic | Code ready for review |
| `review_approved` | Critic | Synthesizer | Quality gate passed |
| `review_blocked` | Critic | Developer, Founder | Quality gate failed |
| `market_shift_detected` | Researcher | Strategist | Competitive intel |
| `founder_decision_needed` | Any | Synthesizer | Human required |
| `meta_optimization_complete` | Synthesizer | All | Prompts updated |

### 5.3 Trigger Logic (Pseudocode)

```python
# Neural Trigger Engine

def on_event(event):
    """
    Central event router - the "nervous system"
    """
    # 1. Log to ledger
    append_to_jsonl(".brain/ledger/events.jsonl", event)
    
    # 2. Update state
    update_state(".brain/ledger/state.json", event)
    
    # 3. Route to triggered agents
    for agent in event.triggers:
        if should_activate(agent, event):
            queue_agent_task(agent, event)
    
    # 4. Synthesizer always observes
    notify_synthesizer(event)

def should_activate(agent, event):
    """
    Check if agent should wake up
    """
    agent_config = load_agent_config(f".brain/agents/{agent}.md")
    
    # Check neural triggers
    for trigger in agent_config.neural_triggers:
        if matches(trigger, event):
            return True
    
    return False

def run_meta_optimization():
    """
    Synthesizer's 72-hour cycle
    """
    # 1. Analyze performance
    metrics = read_json(".brain/meta/performance.json")
    
    # 2. Identify improvements
    improvements = analyze_bottlenecks(metrics)
    
    # 3. Generate new prompts
    for agent in improvements:
        new_prompt = generate_improved_prompt(agent)
        write_file(f".brain/agents/{agent}.md", new_prompt)
    
    # 4. Log optimization
    log_optimization(improvements)
    
    # 5. Emit event
    emit_event("meta_optimization_complete", improvements)
```

### 5.4 State Machine

```
┌──────────────────────────────────────────────────────────────────┐
│                        STATE MACHINE                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   IDLE ──[event]──► PROCESSING ──[complete]──► WAITING           │
│     ▲                    │                         │              │
│     │                    │                         │              │
│     │              [needs_review]                 [trigger]       │
│     │                    │                         │              │
│     │                    ▼                         ▼              │
│     └────────────── REVIEWING ◄───────────── ACTIVATING          │
│                          │                                        │
│                    [critical]                                     │
│                          │                                        │
│                          ▼                                        │
│                   FOUNDER_ESCALATION                              │
│                          │                                        │
│                    [decision]                                     │
│                          │                                        │
│                          ▼                                        │
│                       RESUMING ─────────────────► IDLE            │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Part 6: Recursive Self-Improvement Protocol

### 6.1 The Meta-Learning Loop

```
Every 24-72 hours:

┌─────────────────────────────────────────────────────────────────┐
│                    SELF-IMPROVEMENT CYCLE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. MEASURE                                                      │
│     └── Read .brain/meta/performance.json                        │
│     └── Collect: task_count, success_rate, time_to_complete     │
│     └── Collect: escalation_rate, rework_rate                   │
│                                                                  │
│  2. ANALYZE                                                      │
│     └── Identify: Which agent has lowest efficiency?            │
│     └── Identify: Which handoffs cause delays?                  │
│     └── Identify: What triggers false positives?                │
│                                                                  │
│  3. HYPOTHESIZE                                                  │
│     └── Generate improvement hypotheses                          │
│     └── Rank by expected impact                                  │
│                                                                  │
│  4. MODIFY                                                       │
│     └── Update agent system prompts (.brain/agents/*.md)        │
│     └── Update trigger conditions (.brain/ledger/triggers.json) │
│     └── Update workflows (.brain/workflows/*.md)                │
│                                                                  │
│  5. VALIDATE                                                     │
│     └── Run next cycle with new configuration                   │
│     └── Compare metrics to baseline                              │
│     └── Rollback if degradation detected                        │
│                                                                  │
│  6. DOCUMENT                                                     │
│     └── Log to .brain/meta/optimization_log.md                  │
│     └── Update .brain/memory/learnings.md                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Performance Metrics Schema

```json
{
  "timestamp": "2025-12-26T21:00:00Z",
  "agents": {
    "strategist": {
      "tasks_completed": 5,
      "success_rate": 0.95,
      "avg_time_minutes": 45,
      "escalation_rate": 0.10,
      "rework_rate": 0.05
    },
    "architect": { ... },
    "developer": { ... },
    "critic": { ... },
    "researcher": { ... },
    "synthesizer": { ... }
  },
  "system": {
    "total_events": 127,
    "handoff_efficiency": 0.92,
    "founder_interrupts": 3,
    "auto_approvals": 45
  }
}
```

---

## Part 7: Pioneer Benchmark Comparison

### 7.1 Where We Pioneer

| Capability | Industry Standard | Nuclear Architecture | Advantage |
|------------|-------------------|---------------------|-----------|
| **Tool Fluidity** | Vendor lock-in (LangChain, CrewAI) | 100% Markdown portable | Migrate in minutes |
| **Self-Improvement** | Manual prompt tuning | Recursive meta-learning | Compounds over time |
| **Founder Leverage** | Human orchestrates | Synthesizer orchestrates | 10x time savings |
| **Context Persistence** | Session-based | Ledger-based eternal memory | No context drift |
| **Event-Driven** | Polling/scheduled | Neural triggers on state change | Instant response |

### 7.2 Where We Stand on Giants

| Capability | Source | How We Adapt |
|------------|--------|--------------|
| **Orchestrator Pattern** | Microsoft Magentic-One | Synthesizer as lead agent |
| **Handoffs** | OpenAI Swarm | Event-based handoffs via ledger |
| **Graph-Based Flow** | LangGraph | State machine in triggers.json |
| **Self-Referential Improvement** | Gödel Agent | Meta-optimization cycle |
| **Artifact-Centric** | GitOps | .brain/ as version-controlled brain |

### 7.3 Competitive Analysis

| Framework | Strengths | Weaknesses vs Nuclear |
|-----------|-----------|----------------------|
| **Microsoft Magentic-One** | Web/file tasks, strong orchestrator | Requires AutoGen, not portable |
| **OpenAI Swarm** | Simple handoffs, lightweight | Experimental, no persistence |
| **LangGraph** | Flexible graphs, state management | Python-dependent, complex |
| **CrewAI** | Role-based agents, easy setup | Heavy deps, vendor lock-in |
| **Nuclear Architecture** | Portable, self-improving, founder-optimized | Requires discipline |

---

## Part 8: Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Create `.brain/` directory structure
- [ ] Initialize `ledger/state.json` with current state
- [ ] Write initial agent prompts to `agents/*.md`
- [ ] Set up `events.jsonl` logging

### Phase 2: Neural Triggers (Week 2)
- [ ] Implement event emission in each agent workflow
- [ ] Create trigger routing logic
- [ ] Test agent-to-agent handoffs

### Phase 3: Synthesizer (Week 3)
- [ ] Build daily digest generator
- [ ] Implement founder escalation gate
- [ ] Create cross-domain synthesis logic

### Phase 4: Meta-Learning (Week 4)
- [ ] Implement performance tracking
- [ ] Build self-improvement analyzer
- [ ] Create prompt update mechanism
- [ ] Test rollback on degradation

### Phase 5: Hardening (Week 5+)
- [ ] Load testing with high event volume
- [ ] Validate portability (export/import brain)
- [ ] Document edge cases and failure modes

---

## Part 9: Tool Fluidity Guarantee

### Export Brain
```bash
# Package entire brain for migration
tar -czvf gentlequest-brain-$(date +%Y%m%d).tar.gz .brain/
```

### Import Brain
```bash
# Restore brain in new environment
tar -xzvf gentlequest-brain-YYYYMMDD.tar.gz
# All intelligence, logs, and logic restored in minutes
```

### No Vendor Lock-In
- **Windsurf/Antigravity**: Current host
- **Custom Python**: Can parse .md prompts, .json state
- **Other AI IDEs**: Same portable structure
- **Future platforms**: Markdown is universal

---

## Part 10: Activation Protocol

To activate the Nuclear Architecture:

1. **Initialize Brain**
   ```bash
   mkdir -p .brain/{ledger,agents,memory,artifacts,workflows,meta}
   mkdir -p .brain/artifacts/{strategy,architecture,code,reviews,research,synthesis}
   ```

2. **Copy Agent Prompts**
   - Extract system prompts from Part 4 into `.brain/agents/*.md`

3. **Initialize State**
   ```json
   // .brain/ledger/state.json
   {
     "version": "2025.Final",
     "initialized": "2025-12-26T21:20:00Z",
     "active_agents": [],
     "pending_events": [],
     "founder_queue": []
   }
   ```

4. **Start Event Loop**
   - Each Windsurf thread reads its agent prompt from `.brain/agents/`
   - Each thread writes events to `.brain/ledger/events.jsonl`
   - Synthesizer thread runs 24-72 hour meta-cycle

---

*This blueprint represents the frontier of agentic company architecture.*  
*The orchestration logic—not the product—is the moat.*

*Created: December 26, 2025*  
*Classification: Nuclear | Level 5 Autonomy*  
*Owner: Synthesizer Agent*
