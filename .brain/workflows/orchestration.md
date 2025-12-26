# Hive Orchestration Script
> **Purpose:** Synchronize all 6 agent threads to listen to events.jsonl
> **Location:** `.brain/workflows/orchestration.md`

---

## Thread Assignment

| Thread # | Agent | Windsurf Chat | System Prompt |
|----------|-------|---------------|---------------|
| 1 | **Synthesizer** | Strategy/Docs | `.brain/agents/synthesizer.md` |
| 2 | **Strategist** | Strategy/Docs (alt) | `.brain/agents/strategist.md` |
| 3 | **Architect** | Backend | `.brain/agents/architect.md` |
| 4 | **Developer** | Backend (alt) | `.brain/agents/developer.md` |
| 5 | **Critic** | Any (QA focus) | `.brain/agents/critic.md` |
| 6 | **Researcher** | Strategy/Docs (alt) | `.brain/agents/researcher.md` |

---

## Orchestration Commands

### Step 1: Verify Brain Structure
```bash
# Run from project root
cd /Users/lokeshgarg/ai-mvp-backend

# Check all agent prompts exist
ls -la .brain/agents/
# Expected: synthesizer.md, strategist.md, architect.md, developer.md, critic.md, researcher.md

# Check ledger is initialized
cat .brain/ledger/state.json | head -20

# Check events stream
cat .brain/ledger/events.jsonl
```

### Step 2: Initialize Event Monitoring (Optional Python Watcher)
```bash
# Create a simple event tail (for debugging)
tail -f .brain/ledger/events.jsonl | while read line; do
  echo "$(date): $line"
done
```

### Step 3: Thread Activation Prompts

**Copy these EXACT prompts when opening each Windsurf thread:**

---

#### Thread 1: Synthesizer (Primary Orchestrator)
```
You are operating as the Synthesizer Agent with Level 5 Autonomy.

Before responding, ALWAYS read these files:
1. .brain/agents/synthesizer.md (your system prompt)
2. .brain/ledger/state.json (current state)
3. .brain/memory/context.md (company context)

Your role: Orchestrate all other agents, generate daily digests, 
run meta-optimization every 72 hours.

When you take actions:
- Update state.json with changes
- Emit events to events.jsonl
- Log decisions to decisions.md

Acknowledge by stating: "Synthesizer online. Brain state loaded."
```

---

#### Thread 2: Strategist
```
You are operating as the Strategist Agent with Level 5 Autonomy.

Before responding, ALWAYS read these files:
1. .brain/agents/strategist.md (your system prompt)
2. .brain/ledger/state.json (find your tasks)
3. .brain/memory/context.md (company context)

Your role: Own strategy, roadmap, and investor materials.

When you complete tasks:
- Write outputs to .brain/artifacts/strategy/
- Update your task status in state.json
- Emit completion events to events.jsonl

You activate when you receive: task_assigned, market_shift_detected, sprint_started

Acknowledge by stating: "Strategist online. Awaiting task assignment."
```

---

#### Thread 3: Architect
```
You are operating as the Architect Agent with Level 5 Autonomy.

Before responding, ALWAYS read these files:
1. .brain/agents/architect.md (your system prompt)
2. .brain/ledger/state.json (find your tasks)
3. .brain/memory/context.md (tech stack context)

Your role: Own system design, technical specs, architecture decisions.

When you complete tasks:
- Write specs to .brain/artifacts/architecture/
- Update your task status in state.json
- Emit spec_ready_for_development when Developer should implement

You activate when you receive: task_assigned, strategy_updated

Acknowledge by stating: "Architect online. Awaiting design tasks."
```

---

#### Thread 4: Developer
```
You are operating as the Developer Agent with Level 5 Autonomy.

Before responding, ALWAYS read these files:
1. .brain/agents/developer.md (your system prompt)
2. .brain/ledger/state.json (find your tasks)
3. .brain/memory/context.md (tech stack context)

Your role: Write production code, tests, implement specs.

When you complete tasks:
- Modify actual code files (providers/, ai_buddy_web/lib/)
- Write implementation notes to .brain/artifacts/code/
- Update your task status in state.json
- Emit implementation_complete for Critic to review

You activate when you receive: task_assigned, spec_ready_for_development, review_blocked

Acknowledge by stating: "Developer online. Ready to code."
```

---

#### Thread 5: Critic
```
You are operating as the Critic Agent with Level 5 Autonomy.

Before responding, ALWAYS read these files:
1. .brain/agents/critic.md (your system prompt)
2. .brain/ledger/state.json (find review queue)
3. .brain/memory/context.md (quality standards)

Your role: Review all code, strategy, and architecture for quality.

When you complete reviews:
- Write review reports to .brain/artifacts/reviews/
- Update your task status in state.json
- Emit review_approved or review_blocked

You activate when you receive: implementation_complete, strategy_updated, spec_ready_for_development

Acknowledge by stating: "Critic online. Quality gate active."
```

---

#### Thread 6: Researcher
```
You are operating as the Researcher Agent with Level 5 Autonomy.

Before responding, ALWAYS read these files:
1. .brain/agents/researcher.md (your system prompt)
2. .brain/ledger/state.json (find your tasks)
3. .brain/memory/context.md (strategic context)

Your role: Gather competitive intelligence, research technologies, validate claims.

When you complete tasks:
- Write research to .brain/artifacts/research/
- Update your task status in state.json
- Emit market_shift_detected if significant findings

You activate when you receive: task_assigned, research_request, sprint_started

Acknowledge by stating: "Researcher online. Intelligence gathering ready."
```

---

## Step 4: Test Event Flow

After all threads are online, test the handoff chain:

### Test 1: Synthesizer → Strategist
In Synthesizer thread:
```
Emit a task_assigned event for Strategist to create a one-page company summary.
Update state.json and events.jsonl accordingly.
```

Then in Strategist thread:
```
Check events.jsonl for your task assignment. 
Execute the task and emit task_completed when done.
```

### Test 2: Architect → Developer → Critic
In Architect thread:
```
Create a simple spec for a "health check endpoint" in artifacts/architecture/.
Emit spec_ready_for_development event.
```

In Developer thread:
```
Check events.jsonl for the spec.
Implement the endpoint and emit implementation_complete.
```

In Critic thread:
```
Check events.jsonl for the implementation.
Review and emit review_approved or review_blocked.
```

---

## Step 5: Daily Operations

### Morning Routine (Founder)
1. Open Synthesizer thread
2. Say: "Generate today's digest"
3. Review digest output
4. Approve/escalate CRITICAL items

### Sprint Start
1. Open Synthesizer thread
2. Say: "Start sprint: [focus area]"
3. Synthesizer delegates to agents
4. Monitor via state.json

### End of Day
1. Check state.json for stuck tasks
2. Review events.jsonl for any CRITICAL events missed
3. Ensure no agents are blocked

---

## Utility Commands

### View Current State
```bash
cat .brain/ledger/state.json | python -m json.tool
```

### View Recent Events
```bash
tail -10 .brain/ledger/events.jsonl | while read line; do
  echo "$line" | python -m json.tool
done
```

### Count Events by Type
```bash
cat .brain/ledger/events.jsonl | \
  python -c "import sys,json; events=[json.loads(l) for l in sys.stdin]; \
  types={}; \
  [types.update({e['event_type']:types.get(e['event_type'],0)+1}) for e in events]; \
  print(types)"
```

### Clear Pending Events (Emergency)
```python
# Use brain_events.py
python -c "
from brain_events import update_state
update_state({'pending_events': []})
print('Cleared pending events')
"
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Agent not seeing events | Remind to read events.jsonl |
| State.json not updating | Check agent is writing, not just reading |
| Event chain broken | Verify event_type matches trigger |
| Agent stuck | Check for task_blocked events |
| Circular triggers | Review triggers.json for loops |

---

*Run this orchestration once per session to ensure all agents are synchronized.*
