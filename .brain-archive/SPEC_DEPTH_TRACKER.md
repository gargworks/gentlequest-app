# Depth Tracker: Comprehensive Tiered Specification

> **Priority:** #0 (before all v0.4.0 features)  
> **Target User:** ADHD builders, founders, creative thinkers  
> **Value Proposition:** Channel ADHD hyperfocus into productivity, not rabbit holes  
> **Status:** FROZEN - Ready for implementation

---

## User's Raw Inputs (2026-01-05, ~2am)

**Captured verbatim from voice/chat to preserve original intent:**

> "I really need to see a map on where we are in this rabbit hole depth. I think this is level 0, 1, 2, 3. Reach down is something which I need to be reminded all the time as the ADHD person after we do everything itself."

> "The real pain here is also that the context from when we are at a particular node in this depth, and I don't really believe it. What was going on in my brain at that point in time and where to pick it up from. Ultimately once we explain that, when to consolidate, how to consolidate and get back and shape and make it valuable rather than just keep exploring that is something that we have to see. Also what learnings are there consolidated junk it back into the system that is something which is very powerful."

> "I think this is the ultimate feature for the ADHD brains and ADHD builders and founders. Isn't it? What do you suggest? This will actually empower the creative ADHD brain and helps in all of its energy into one direction so that the ADHD brain can outperform the normal brain."

> "This alone is worth a million dollars right now isn't it?"

**Key Requirements Extracted:**
1. **Real-time depth map** - Always visible "you are here"
2. **Brain state at each node** - "What was going on in my brain at that point"
3. **Context preservation** - "Where to pick it up from"
4. **Consolidation triggers** - "When to consolidate, how to consolidate"
5. **Learning extraction** - "What learnings are there" → feed back into system
6. **ADHD-specific design** - "Reminded all the time as the ADHD person"
7. **Performance enhancement** - "ADHD brain can outperform the normal brain"

---

## The Million Dollar Problem

### What ADHD Builders Experience

**The Hyperfocus Trap:**
```
Start: "Let me fix this bug"
├─ Level 1: "Actually, let me refactor this first"
│   ├─ Level 2: "I need a better architecture"
│   │   ├─ Level 3: "Let me design a framework"
│   │   │   ├─ Level 4: "I should write a spec"
│   │   │   │   └─ Level 5: "I need to research best practices"
│   │   │   │       └─ 6 hours later: Bug still exists
```

**What Gets Lost:**
1. **Original intent** - Why did we start this?
2. **Current depth** - How deep are we?
3. **Path home** - How do we get back?
4. **When to stop** - Should we still be going deeper?
5. **What we learned** - Were these rabbit holes valuable?

### Why Current Tools Fail

**IDEs:** Track files, not conversation depth  
**Task managers:** Track tasks, not thought pathways  
**AI assistants:** Go as deep as you go (no guardrails)  
**Note apps:** Where you dump things, not navigate them

**What's Missing:** Real-time "you are here" indicator for thought depth.

---

## The Solution: Depth Tracker

**One-line summary:**  
> A real-time GPS for your conversation. Always know how deep you are, why you're there, and how to get back.

---

## Tier Overview

| Tier | Name | What It Does | Effort | When to Build |
|:-----|:-----|:-------------|:-------|:--------------|
| **1** | **MVP** | Simple depth counter + breadcrumbs | 2-3h | NOW |
| **2** | **Context-Aware** | Captures why you went deeper, consolidation triggers | +2h | After MVP used 10+ times |
| **3** | **Proactive** | Warns before going too deep, suggests resurfacing | +2h | After Tier 2 proves value |
| **4** | **Learning** | Tracks patterns, predicts when you'll get stuck | +4h | After 50+ sessions |
| **5** | **Team/Enterprise** | Shared pathways, async collaboration | +8h | When team uses Nucleus |

---

## TIER 1: MVP (2-3 hours)

### What It Does

**Simple, always-visible depth indicator:**
```
╔═══════════════════════════════════════╗
║ DEPTH: ●●●○○ (3 of 5)                ║
║                                       ║
║ 0: Fix shipping loop                  ║
║ └─ 1: Design thinking                 ║
║    └─ 2: v0.4.0 specs                ║
║       └─ 3: Intent snapshots ← YOU   ║
╚═══════════════════════════════════════╝
```

**Core Features:**
1. **Depth Counter** - Visual indicator (1-5 dots, traffic light colors)
2. **Breadcrumb Trail** - How you got here (topic at each level)
3. **Go Up Command** - Resurface one level: `nucleus depth up`
4. **Max Depth Warning** - Red alert at level 4+

### Data Model

```json
// .brain/session/depth.json
{
  "session_id": "2025-01-05_design_session",
  "current_depth": 3,
  "max_safe_depth": 5,
  "levels": [
    {
      "depth": 0,
      "topic": "Fix shipping loop",
      "started_at": "2025-01-05T10:00:00Z",
      "status": "active"
    },
    {
      "depth": 1,
      "topic": "Design thinking",
      "started_at": "2025-01-05T12:00:00Z",
      "status": "active"
    },
    {
      "depth": 2,
      "topic": "v0.4.0 specs",
      "started_at": "2025-01-05T18:00:00Z",
      "status": "active"
    },
    {
      "depth": 3,
      "topic": "Intent snapshots",
      "started_at": "2025-01-05T01:00:00Z",
      "status": "current"
    }
  ]
}
```

### Brain Tools

```python
# Go deeper (called when branching into subtopic)
brain_depth_push(topic: str) -> dict
# Returns: {"current_depth": 4, "warning": "Approaching max depth"}

# Come back up
brain_depth_pop() -> dict
# Returns: {"current_depth": 3, "returned_to": "v0.4.0 specs"}

# View current state
brain_depth_show() -> dict
# Returns: Full depth.json content

# Reset to level 0
brain_depth_reset() -> dict
# Returns: {"message": "Session cleared. Back to root."}
```

### CLI Commands

```bash
# Show current depth
nucleus depth show

# Go up one level
nucleus depth up

# Go up to specific level
nucleus depth up --to=1

# Reset session
nucleus depth reset

# Set max safe depth
nucleus depth max 4
```

### Visual Indicators

**Depth Colors:**
- 🟢 Level 0-2: Green (safe zone)
- 🟡 Level 3: Yellow (caution)
- 🔴 Level 4+: Red (danger zone)

**Shown After Every Response:**
```
─────────────────────────────────────
📍 DEPTH: ●●●○○ (3/5) ← You are here
   Path: Fix shipping → Design thinking → v0.4.0 specs → Intent snapshots
   [Go up: `nucleus depth up`]
─────────────────────────────────────
```

### Implementation Checklist (Tier 1)

- [ ] Create `.brain/session/depth.json` structure
- [ ] Implement `brain_depth_push(topic)`
- [ ] Implement `brain_depth_pop()`
- [ ] Implement `brain_depth_show()`
- [ ] Implement `brain_depth_reset()`
- [ ] Add CLI commands (`nucleus depth show/up/reset/max`)
- [ ] Add visual indicator to response footer
- [ ] Color-code by depth level

**Effort:** 2-3 hours

---

## TIER 2: Context-Aware (After MVP proves value)

### What It Adds

**Capture WHY you went deeper + consolidation triggers:**

```json
{
  "depth": 3,
  "topic": "Intent snapshots",
  "started_at": "2025-01-05T01:00:00Z",
  "why_deeper": "Would lose context if we don't capture now",
  "brain_state": "Peak context, worried about momentum loss",
  "consolidation": {
    "should_consolidate": true,
    "trigger": "user_flagged_rabbit_hole",
    "suggested_action": "Return to level 2, extract key learnings"
  }
}
```

### Added Features

1. **Why Deeper** - Captures reason for going deeper (auto or manual)
2. **Brain State** - What you were thinking at that node
3. **Consolidation Triggers:**
   - Time-based (>1 hour at same level)
   - Depth-based (hit max depth)
   - User-flagged ("we're in a rabbit hole")
   - Energy-based (it's 2am)
4. **Learning Extraction** - When popping up, prompts: "What did you learn?"

### New Commands

```bash
# Mark why you're going deeper
nucleus depth push "Need to capture v0.5 vision" --why="Prevent context loss"

# Flag rabbit hole
nucleus depth rabbit-hole

# Pop with learning
nucleus depth up --learned="Tiered specs prevent over-engineering"
```

### Visual Enhancement

```
─────────────────────────────────────
📍 DEPTH: ●●●●○ (4/5) ⚠️ DEEP!
   Path: Fix shipping → Design → Specs → Intent → Depth tracker spec
   Why here: "Capture ADHD feature before sleeping"
   
   💡 Consolidation suggested: You've been at level 4 for 45 min
   [Pop up: `nucleus depth up --learned="..."`]
─────────────────────────────────────
```

### Implementation Checklist (Tier 2)

- [ ] Add `why_deeper` field capture
- [ ] Add `brain_state` field (auto-inferred from conversation)
- [ ] Implement consolidation triggers (time, depth, flag)
- [ ] Add `nucleus depth rabbit-hole` command
- [ ] Add `--learned` parameter to `depth up`
- [ ] Store learnings in `.brain/session/learnings.jsonl`
- [ ] Show consolidation suggestions

**Effort:** +2 hours (total: 4-5 hours)

---

## TIER 3: Proactive (After Tier 2 proves value)

### What It Adds

**AI-assisted guardrails:**

1. **Pre-Dive Warning** - Before going to level 4+:
   ```
   ⚠️ You're about to go to level 4.
   Current path: Fix shipping → Design → Specs → Intent
   
   Do you want to:
   a) Continue deeper (set time limit?)
   b) Stay at current level
   c) Go back up to level 2
   ```

2. **Suggested Resurfacing** - Based on patterns:
   ```
   💡 Pattern detected: You often get stuck at level 4.
   
   Last 3 times at level 4:
   - Session 1: Spent 2 hours, extracted 1 learning
   - Session 2: Spent 3 hours, had to abandon
   - Session 3: Current session (45 min so far)
   
   Suggestion: Resurface now, consolidate learnings.
   ```

3. **Time Limits** - Optional time bounds:
   ```bash
   nucleus depth push "Research best practices" --max-time=30m
   ```
   After 30 min: "Time limit reached. Resurface with learnings?"

### New Commands

```bash
# Set time limit for current level
nucleus depth limit 30m

# Check remaining time
nucleus depth time

# Force resurface (ignore resistance)
nucleus depth force-up
```

### Implementation Checklist (Tier 3)

- [ ] Add pre-dive confirmation at level 4+
- [ ] Track time spent at each level
- [ ] Implement `--max-time` parameter
- [ ] Add pattern detection (history analysis)
- [ ] Show suggestions based on past sessions
- [ ] Implement `nucleus depth limit` command
- [ ] Add `force-up` for when user is stuck

**Effort:** +2 hours (total: 6-7 hours)

---

## TIER 4: Learning (After 50+ sessions)

### What It Adds

**Pattern recognition + prediction:**

1. **Personal Patterns Dashboard:**
   ```
   📊 Your Depth Patterns (Last 30 days):
   
   Productive Depths:
   - Level 2: 85% of work completed
   - Level 3: 60% completed, 40% abandoned
   
   Risky Depths:
   - Level 4+: Only 20% of sessions produced results
   
   Average session: 2.3 levels deep
   Most productive time: 10am-2pm (rarely go past level 3)
   Risky time: After 10pm (average depth 4.2)
   
   Recommendation: Stop at level 3 after 10pm.
   ```

2. **Predictive Warnings:**
   ```
   🔮 Based on your patterns:
   - It's 1am
   - You're at level 3
   - You usually go to level 5+ at this hour
   
   Prediction: 70% chance of rabbit hole
   Suggestion: Wrap up now, resume fresh tomorrow
   ```

3. **Learning Aggregation:**
   ```
   📚 Learnings from rabbit holes:
   - "Tiered specs prevent over-engineering" (level 4, worth it)
   - "Don't design at 2am" (level 5, not worth it)
   - "Capture intent while context hot" (level 3, critical)
   
   Patterns: Deep dives after midnight rarely produce value.
   ```

### New Commands

```bash
# View patterns
nucleus depth patterns

# View learnings
nucleus depth learnings

# Export for reflection
nucleus depth report --days=30
```

### Implementation Checklist (Tier 4)

- [ ] Track all sessions in `.brain/session/history.jsonl`
- [ ] Build pattern analysis (time, depth, outcomes)
- [ ] Implement predictive model (simple heuristics first)
- [ ] Aggregate learnings by topic/depth
- [ ] Generate recommendations based on history
- [ ] Add `nucleus depth patterns` command
- [ ] Add `nucleus depth report` command

**Effort:** +4 hours (total: 10-11 hours)

---

## TIER 5: Team/Enterprise (When team uses Nucleus)

### What It Adds

**Shared pathways + async collaboration:**

1. **Pathway Sharing:**
   ```
   📤 Lokesh shared a pathway:
   "Design Thinking Session (2025-01-05)"
   
   Depth reached: 4
   Artifacts: 42
   Key learnings: 5
   
   [View pathway] [Continue from here]
   ```

2. **Async Handoff:**
   ```
   🤝 Team Handoff:
   
   Lokesh (1am): Reached level 4, need to sleep.
   Current state: Intent snapshots captured, depth tracker speced.
   
   For next person:
   - Resume at level 2 (v0.4.0 specs)
   - Key context: Depth tracker is priority #0
   - Don't go deeper than level 3
   ```

3. **Collective Patterns:**
   ```
   📊 Team Patterns:
   - Average productive depth: 2.5
   - Deepest productive session: Level 4 (rare)
   - Most rabbit holes: After 8pm (all members)
   
   Team recommendation: Cap daily deep work at level 3.
   ```

### Implementation Checklist (Tier 5)

- [ ] Pathway export/import (JSON + markdown)
- [ ] Shareable links (file:// or cloud)
- [ ] Handoff protocol (who's working, where they stopped)
- [ ] Team analytics aggregation
- [ ] Slack/Discord notifications (optional)
- [ ] Permission system (who can view/continue pathways)

**Effort:** +8 hours (total: 18-19 hours)

---

## Effort Summary

| Tier | Cumulative Effort | Value |
|:-----|:------------------|:------|
| 1 (MVP) | 2-3 hours | Immediate relief from rabbit holes |
| 2 (Context) | 4-5 hours | Understand why and extract learnings |
| 3 (Proactive) | 6-7 hours | Prevent rabbit holes before they happen |
| 4 (Learning) | 10-11 hours | Personal productivity patterns |
| 5 (Team) | 18-19 hours | Scalable for teams |

**Recommendation:** Build Tier 1 MVP tomorrow (2-3h). Evaluate before Tier 2.

---

## Success Criteria

### Tier 1 (MVP)
- [ ] Always see current depth after every response
- [ ] Can go up with single command
- [ ] Red warning at level 4+
- [ ] Never lose track of where you are

### Full System
- [ ] ADHD builder reports: "I stay focused now"
- [ ] Average session depth reduced from 4+ to 2-3
- [ ] Rabbit hole time reduced by 50%
- [ ] Learnings captured and reusable
- [ ] Team handoffs are seamless

---

## Foundational References

### Prof. Venkat Venkatraman: Agentic Orchestration

**Source:** [Agentic Orchestration: The Next Frontier of Competitive Advantage](https://www.linkedin.com/pulse/agentic-orchestration-next-frontier-competitive-venkat-venkatraman-9r0pf/)

**Why This Matters to Nucleus:**

Prof. Venkatraman's research on **Agentgraphs** directly informs how we think about coordinating biological (human) and digital (AI) agents. The Depth Tracker is a personal-scale implementation of his enterprise coordination principles.

---

### Key Concepts from the Article

**Three Agent Types:**
1. **Biological agents (humans):** Judgment, creativity, ethical reasoning
2. **Digital agents (AI):** Speed, scale, pattern recognition  
3. **Physical agents (robots):** Precision, endurance, physical presence

**The Agentgraph:**
> "An agentgraph is the dynamic architecture of coordination among autonomous actors."

Captures:
- **Task allocation:** Which agent types handle which decisions
- **Handoff protocols:** How work flows between agents
- **Escalation paths:** When to route exceptions to higher authority
- **Learning loops:** How the system continuously improves
- **Boundary interfaces:** Where your agents connect with external agents

**Agent Network Effects (Scale, Scope, Speed):**

| Dimension | What It Means | Application to Nucleus |
|:----------|:--------------|:-----------------------|
| **Scale** | Adding agents reduces coordination costs | More threads = better routing patterns |
| **Scope** | Coordination patterns transfer across domains | GentleQuest learnings apply to Nucleus |
| **Speed** | Machine-timescale learning (thousands of experiments/day) | Depth Tracker learns user patterns rapidly |

**Dynamic Decision Rights:**
> "The system learns which agent type best handles each decision given current context, continuously adapting."

This directly maps to our **CEO/Chairman model**: AI handles groundwork, escalates to human for judgment calls.

---

### Five Design Principles (Applied to Nucleus)

**1. Start with coordination patterns, not tools**
- Don't ask "what AI should we use?"
- Ask "what work requires coordination, what patterns create value?"
- **Nucleus Application:** Depth Tracker coordinates your attention, not just your tasks

**2. Architect for learning velocity, not current efficiency**
- How fast can the system discover better patterns?
- **Nucleus Application:** Tier 4 tracks personal patterns, predicts when you'll get stuck

**3. Develop coordination-focused metrics**
- Track coordination efficiency, capability utilization, learning velocity
- **Nucleus Application:** Time-at-depth, consolidation triggers, outcome tracking

**4. Map boundary conditions explicitly**
- Where do your agents interface with external agents?
- **Nucleus Application:** Cross-thread handoffs, session boundaries, context sharing

**5. Build modular capability layers**
- Specialized functions that combine into sophisticated workflows
- **Nucleus Application:** Tiered implementation (MVP → Enterprise)

---

### The Strategic Insight

> "Companies obsessed with technical infrastructure might build impressive AI systems yet suffer chaotic, inefficient coordination—like hiring brilliant people but failing to build effective organizational networks. Companies mastering agentgraphs—even with modest technical infrastructure—achieve superior operational performance because they've solved the orchestration problem, not just the information problem."

**For ADHD Builders:**
The Depth Tracker solves the **orchestration problem** (managing attention across rabbit holes) rather than the information problem (having more tools/context).

---

### Connection to Nucleus Design

| Prof. Venkatraman's Concept | Nucleus Implementation |
|:----------------------------|:-----------------------|
| Agentgraph | Nucleus brain architecture (Registry + Ledger + Synthesizer) |
| Task allocation | CEO/Chairman model (AI handles groundwork, human decides) |
| Handoff protocols | Session management, pathway preservation |
| Escalation paths | Depth limits, consolidation triggers |
| Learning loops | Pattern tracking (Tier 4), outcome analysis |
| Dynamic decision rights | Proactive warnings (Tier 3), capability-based routing |

---

### User's Personal Note

> "I am deeply inspired by his research and his lectures and classes molded my way of thinking such systems."

This research forms the theoretical foundation for Nucleus's approach to agent coordination at personal scale.

---

### Design Influences

- Satellite View metaphor (Part 2 monologue)
- Brain Consolidation Principle (Principle XVI)
- CEO/Chairman Model (Principle III)
- Session Management (v0.5.0 intent)

---

## Build Order

1. **Tomorrow:** Tier 1 MVP (2-3 hours)
2. **After 10+ uses:** Tier 2 Context-Aware (+2 hours)
3. **After proves value:** Tier 3 Proactive (+2 hours)
4. **After 50+ sessions:** Tier 4 Learning (+4 hours)
5. **When team:** Tier 5 Enterprise (+8 hours)

---

**FROZEN. Priority #0 for implementation.**
