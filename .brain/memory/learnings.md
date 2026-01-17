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

## January 2026

### 2026-01-17: Overnight Planning Session
**Learning:** PLANNING MODE requires deep reading before any action; assumptions must be validated before GTM execution
**What Worked:** Creating structured planning documents (synthesis, audit, competitive, briefing); verifying product capabilities in code
**What Didn't:** Jumping to maintenance fixes before absorbing strategic context
**Action Taken:** Created 4 planning documents; verified /api/assessment/history, admin_dashboard, crisis detection exist; identified gap (counselor notifications missing)

### 2026-01-17: Product Readiness Discovery
**Learning:** GentleQuest has more capabilities than assumed - assessment history API, admin dashboard, 11-country crisis resources all exist
**What Worked:** Systematic grep search of app.py to verify features
**What Didn't:** Assuming gaps without checking code
**Action Taken:** Updated planning documents with verified findings; identified true gap (crisis alerts to counselors missing)

### 2026-01-17: Strategic Constraint Enforcement
**Learning:** "NO PRODUCT CODE UNTIL FEB 1" means absorb→plan→validate, not just pause coding
**What Worked:** Deep reading of 291 checkpoints, all GTM artifacts, NORTH_STAR_VISION
**What Didn't:** Treating constraint as "no work" vs "different work"
**Action Taken:** Shifted to planning-only mode with verification of existing capabilities

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
