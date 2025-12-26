# Learnings Archive

> Institutional memory of what worked, what didn't, and why.
> Updated by all agents; curated by Synthesizer.

---

## December 2025

### 2025-12-26: Sprint 1 Agent Execution
**Learning:** Event-driven handoffs work; all 3 agents completed tasks in one session
**What Worked:** State handshake before execution, event emission after completion
**What Didn't:** Nothing blocked (first run)
**Action Taken:** Archived as proof of concept

### 2025-12-26: SOTA Benchmark Discovery
**Learning:** We pioneer tool-fluidity and self-improvement; industry lacks both
**What Worked:** Structured comparison against 5 frameworks
**What Didn't:** N/A
**Action Taken:** Adopt orchestrator pattern from Magentic-One, handoffs from Swarm

### 2025-12-26: Brain Audit Findings
**Learning:** Developer↔Critic loop needs max_retries; silent failures undetected
**What Worked:** Systematic audit of all trigger paths
**What Didn't:** Gap in stuck task detection
**Action Taken:** Recommendations logged for Phase 2 implementation

### 2025-12-26: Architecture Evolution
**Learning:** Document-centric architecture works but has scaling limits
**What Worked:** Artifacts as coordination layer, no agent-to-agent chatter
**What Didn't:** Manual weekly syncs, founder as bottleneck
**Action Taken:** Upgraded to Nuclear Architecture with event-driven triggers

### 2025-12-25: Function Calling Implementation
**Learning:** Gemini's native function calling is simpler than LangChain
**What Worked:** Direct tool declarations in gemini.py
**What Didn't:** Complex framework dependencies
**Action Taken:** Avoided LangChain, used native API

---

## Template for New Entries

```markdown
### YYYY-MM-DD: [Title]
**Learning:** [One-sentence insight]
**What Worked:** [Successful approach]
**What Didn't:** [Failed approach]
**Action Taken:** [How we adapted]
```

---

*This file is append-only. Archive old entries monthly.*
