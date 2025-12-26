# First Activation: Subatomic Sprint Kickoff

> **Purpose:** This document tells the founder exactly what to say to activate the Synthesizer
> **Location:** `.brain/workflows/first_activation.md`

---

## The First Command

Copy and paste this exact prompt to the **Synthesizer Agent (Strategy/Docs thread)**:

```
Synthesizer: Activate Level 5 Autonomy. 

Your first mission: Digest my strategic documents and produce the first Subatomic Sprint.

Documents to digest:
1. docs/AGENTIC_COMPANY_ARCHITECTURE.md (the document-centric foundation)
2. docs/AGENTIC_SOLO_FOUNDER_PLAYBOOK.md (the playbook for operations)
3. docs/NUCLEAR_AGENTIC_BLUEPRINT.md (the nuclear upgrade)

Actions required:
1. Read all three documents
2. Read .brain/memory/context.md for current company context
3. Read .brain/ledger/state.json for current system state
4. Identify the TOP 3 highest-leverage actions for next 72 hours
5. Create Sprint Plan in .brain/ledger/state.json
6. Emit 'sprint_started' event to .brain/ledger/events.jsonl
7. Delegate tasks to appropriate agents
8. Report back with the Sprint Summary

Output format:
- Sprint definition written to state.json
- Digest summary written to .brain/artifacts/synthesis/doc_digest.md
- Event emitted to events.jsonl
- Plain text summary for me to review

Begin.
```

---

## What Happens Next

When you issue this command, the Synthesizer will:

### Step 1: Context Loading
```
READ: .brain/ledger/state.json → Get current state
READ: .brain/memory/context.md → Understand company
READ: .brain/memory/patterns.md → Know decision patterns
```

### Step 2: Document Digestion
```
READ: docs/AGENTIC_COMPANY_ARCHITECTURE.md
READ: docs/AGENTIC_SOLO_FOUNDER_PLAYBOOK.md  
READ: docs/NUCLEAR_AGENTIC_BLUEPRINT.md

EXTRACT:
- Key architecture decisions
- Obsolete patterns to replace
- Priority actions identified
- Success metrics defined
```

### Step 3: Sprint Creation
```
WRITE: .brain/ledger/state.json
{
  "current_sprint": {
    "id": "sprint-001",
    "name": "Subatomic Sprint 1: Architecture Activation",
    "started": "ISO8601",
    "focus": "Activate Nuclear Brain and establish baseline",
    "tasks": [
      {"agent": "researcher", "task": "...", "status": "pending"},
      {"agent": "strategist", "task": "...", "status": "pending"},
      {"agent": "architect", "task": "...", "status": "pending"}
    ]
  }
}
```

### Step 4: Event Emission
```
APPEND: .brain/ledger/events.jsonl
{
  "event_id": "syn-001",
  "timestamp": "ISO8601",
  "emitter": "synthesizer",
  "event_type": "sprint_started",
  "severity": "NOTABLE",
  "payload": {
    "sprint_name": "Subatomic Sprint 1",
    "focus": "Architecture Activation",
    "assigned_agents": ["researcher", "strategist", "architect"]
  }
}
```

### Step 5: Report
```
Synthesizer presents:
- Sprint summary
- Tasks assigned per agent
- Expected outputs
- Timeline (72h)
- What founder needs to do next
```

---

## Expected Output Format

The Synthesizer should return something like:

```markdown
# 🔥 Subatomic Sprint 1: Activated

## Sprint Focus
Activate Nuclear Brain and establish operational baseline.

## Tasks Assigned

| Agent | Task | Output | Deadline |
|-------|------|--------|----------|
| Researcher | Benchmark against elite AI labs | artifacts/research/benchmark.md | 24h |
| Strategist | Create investor pitch deck outline | artifacts/strategy/pitch_outline.md | 48h |
| Architect | Design agent communication protocol | artifacts/architecture/agent_protocol.md | 48h |

## Events Emitted
- ✅ sprint_started (syn-001)
- ✅ task_assigned × 3

## State Updated
- current_sprint populated in state.json
- active_agents: ["researcher", "strategist", "architect"]

## Founder Action Required
None immediately. Sprint runs for 72h.
Next check-in: Daily Digest tomorrow at 06:00 UTC.
```

---

## Verification Steps

After the Synthesizer responds, verify:

1. **Check state.json:**
   ```bash
   cat .brain/ledger/state.json | jq '.current_sprint'
   ```

2. **Check events.jsonl:**
   ```bash
   tail -5 .brain/ledger/events.jsonl
   ```

3. **Check artifact created:**
   ```bash
   ls -la .brain/artifacts/synthesis/
   ```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Synthesizer doesn't read files | Explicitly list file paths |
| No event emitted | Remind to "emit sprint_started event" |
| State not updated | Remind to "update state.json with sprint" |
| Output too verbose | Ask for "concise sprint summary" |

---

*This workflow is version 1.0. Update based on first activation learnings.*
