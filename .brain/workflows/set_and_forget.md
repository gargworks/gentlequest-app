# Set-and-Forget Flywheel Protocol
> **Purpose:** Run the Nuclear Brain with minimal human intervention
> **Location:** `.brain/workflows/set_and_forget.md`

---

## The Protocol

```
┌──────────────────────────────────────────────────────────────┐
│                   SET-AND-FORGET FLYWHEEL                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   FOUNDER INPUT (Only Required Action):                      │
│   ┌──────────────────────────────────────┐                  │
│   │ python agent_manager.py sprint "Goal"│                  │
│   │ python agent_manager.py start        │                  │
│   └──────────────────────────────────────┘                  │
│                         │                                    │
│                         ▼                                    │
│   ┌──────────────────────────────────────────────────────┐  │
│   │              FLYWHEEL RUNS AUTONOMOUSLY               │  │
│   │                                                       │  │
│   │  events.jsonl ──► Event Loop ──► Agent Router         │  │
│   │        ▲                              │                │  │
│   │        └────────── Output Events ◄────┘                │  │
│   │                                                       │  │
│   └──────────────────────────────────────────────────────┘  │
│                         │                                    │
│                         ▼                                    │
│   FOUNDER OUTPUT (Daily Review):                            │
│   ┌──────────────────────────────────────┐                  │
│   │ .brain/artifacts/synthesis/digest_*  │                  │
│   └──────────────────────────────────────┘                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Step 1: Set Your Goal (30 seconds)
```bash
cd /Users/lokeshgarg/ai-mvp-backend
python agent_manager.py sprint "Implement RAG memory layer with pgvector"
```

### Step 2: Start the Flywheel (5 seconds)
```bash
python agent_manager.py start
```

### Step 3: Walk Away
The flywheel will:
- Read events from `events.jsonl`
- Match events to triggers in `triggers.json`
- Activate appropriate agents
- Create activation files in `.brain/activations/`
- Monitor for CRITICAL events
- Generate daily digests

### Step 4: Review Daily (5 minutes)
```bash
# Check digests
ls .brain/artifacts/synthesis/

# Check status
python agent_manager.py status

# Stop if needed
python agent_manager.py stop
```

---

## What Happens Under the Hood

### Event Processing Cycle (Every 5 seconds)

```python
while running:
    # 1. Check for new events
    events = get_unprocessed_events()
    
    # 2. For each event, find matching triggers
    for event in events:
        agents = get_agents_to_activate(event, triggers)
        
        # 3. Create activation file for each agent
        for agent in agents:
            create_activation_file(agent, event)
        
        # 4. If CRITICAL, pause and notify founder
        if event.severity == 'CRITICAL':
            escalate_to_founder(event)
    
    # 5. Mark events as processed
    update_last_processed_id()
    
    # 6. Wait and repeat
    time.sleep(5)
```

### Activation Files

When an agent is triggered, a file is created:
```
.brain/activations/researcher_20251226_231930.md
```

This file contains:
- The trigger event
- Current state snapshot
- Context from memory
- The agent's system prompt
- Task instructions

---

## Agent Execution Modes

### Mode 1: Manual (Current)
Activation files are created. Human copies to Windsurf.

### Mode 2: Semi-Automated (Coming)
Activation files trigger Windsurf API calls.

### Mode 3: Full Automation (Future)
Direct LLM API integration with output parsing.

---

## CRITICAL Event Handling

When a CRITICAL event is detected:

1. **Flywheel Pauses** (continues monitoring but doesn't process)
2. **Notification Created** at `.brain/artifacts/synthesis/CRITICAL_*.md`
3. **Founder Reviews** the event
4. **Founder Resumes** with:
   ```bash
   python agent_manager.py resume
   ```

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `sprint "goal"` | Initialize a new sprint with the given goal |
| `start` | Start the flywheel (runs until stopped or CRITICAL) |
| `stop` | Stop the flywheel gracefully |
| `status` | Show current flywheel and sprint status |
| `resume` | Resume after CRITICAL event review |

---

## Monitoring

### Real-Time Event Stream
```bash
tail -f .brain/ledger/events.jsonl | jq .
```

### Flywheel Logs
```bash
tail -f .brain/flywheel.log
```

### Current State
```bash
cat .brain/ledger/state.json | jq .current_sprint
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Flywheel not starting | Check for existing PID in `.brain/.flywheel.pid` |
| Agents not activating | Verify trigger definitions in `triggers.json` |
| Event not processed | Check `last_processed_event_id` in state |
| CRITICAL not notifying | Review escalation logic in agent_manager.py |

---

## Daily Founder Ritual

1. **Morning (5 min):**
   ```bash
   python agent_manager.py status
   cat .brain/artifacts/synthesis/digest_*.md | tail -100
   ```

2. **Review any CRITICAL events**

3. **Adjust sprint if needed:**
   ```bash
   python agent_manager.py sprint "New goal"
   ```

4. **Resume if paused:**
   ```bash
   python agent_manager.py resume
   ```

---

*This is the path to Level 5 Autonomy.*
*The system runs. You review. You decide only when CRITICAL.*
