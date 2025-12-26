# Neural Bridge: Technical Specification
> **Event ID:** syn-mvp-001  
> **Agent:** Developer | Level 5 Autonomy  
> **Sprint:** Sprint 3: MVP Genesis  
> **Purpose:** Core backend feature connecting agent triggers to execution

---

## Overview

The **Neural Bridge** is the event-driven API layer that connects the `.brain` ledger system to real backend execution. It transforms the conceptual agent architecture into a live, running system.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     NEURAL BRIDGE                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  events.jsonl │───►│   Flywheel   │───►│    Agent     │      │
│  │  (Event Log)  │    │   (Reader)   │    │   Router     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                │                 │
│                                                ▼                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  state.json  │◄───│   State      │◄───│   Agent      │      │
│  │  (State)     │    │   Manager    │    │   Executor   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### 1. Event Emission

**POST /api/brain/events**

Emit a new event to the event stream.

```python
@app.route('/api/brain/events', methods=['POST'])
def emit_event():
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "emitter": request.json.get('emitter', 'api'),
        "event_type": request.json['event_type'],
        "severity": request.json.get('severity', 'NOTABLE'),
        "payload": request.json.get('payload', {}),
        "metadata": request.json.get('metadata', {})
    }
    
    # Append to events.jsonl
    with open('.brain/ledger/events.jsonl', 'a') as f:
        f.write(json.dumps(event) + '\n')
    
    return jsonify({"success": True, "event_id": event["event_id"]})
```

---

### 2. State Management

**GET /api/brain/state**

Get current system state.

```python
@app.route('/api/brain/state', methods=['GET'])
def get_state():
    with open('.brain/ledger/state.json', 'r') as f:
        state = json.load(f)
    return jsonify(state)
```

**PATCH /api/brain/state**

Update specific state fields.

```python
@app.route('/api/brain/state', methods=['PATCH'])
def update_state():
    with open('.brain/ledger/state.json', 'r') as f:
        state = json.load(f)
    
    # Merge updates
    updates = request.json
    state = deep_merge(state, updates)
    state['last_updated'] = datetime.utcnow().isoformat()
    
    with open('.brain/ledger/state.json', 'w') as f:
        json.dump(state, f, indent=4)
    
    return jsonify({"success": True})
```

---

### 3. Sprint Management

**POST /api/brain/sprint/start**

Start a new sprint with goals.

```python
@app.route('/api/brain/sprint/start', methods=['POST'])
def start_sprint():
    sprint_id = f"sprint-{uuid.uuid4().hex[:8]}"
    sprint = {
        "id": sprint_id,
        "name": request.json['name'],
        "started": datetime.utcnow().isoformat(),
        "ends": (datetime.utcnow() + timedelta(hours=72)).isoformat(),
        "focus": request.json['focus'],
        "status": "ACTIVE",
        "objectives": request.json.get('objectives', []),
        "tasks": []
    }
    
    # Update state
    update_state({"current_sprint": sprint})
    
    # Emit event
    emit_event({
        "event_type": "sprint_started",
        "severity": "NOTABLE",
        "payload": {"sprint_id": sprint_id, "goal": sprint["focus"]},
        "emitter": "founder"
    })
    
    return jsonify({"success": True, "sprint_id": sprint_id})
```

---

### 4. Task Assignment

**POST /api/brain/task/assign**

Assign a task to an agent.

```python
@app.route('/api/brain/task/assign', methods=['POST'])
def assign_task():
    task_id = f"task-{uuid.uuid4().hex[:8]}"
    task = {
        "id": task_id,
        "agent": request.json['agent'],
        "task": request.json['description'],
        "status": "assigned",
        "priority": request.json.get('priority', 'MEDIUM'),
        "expected_output": request.json.get('expected_output', ''),
        "deadline_hours": request.json.get('deadline_hours', 24),
        "assigned_at": datetime.utcnow().isoformat()
    }
    
    # Add to current sprint
    state = get_state()
    state['current_sprint']['tasks'].append(task)
    update_state(state)
    
    # Emit assignment event
    emit_event({
        "event_type": "task_assigned",
        "severity": "NOTABLE",
        "payload": {
            "target_agent": task['agent'],
            "task_id": task_id,
            "task_description": task['task']
        },
        "emitter": "synthesizer"
    })
    
    return jsonify({"success": True, "task_id": task_id})
```

---

### 5. Flywheel Control

**POST /api/brain/flywheel/start**

Start the event processing flywheel.

```python
@app.route('/api/brain/flywheel/start', methods=['POST'])
def start_flywheel():
    # Start flywheel in background
    process = subprocess.Popen(
        ['python3', 'agent_manager.py', 'start'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    emit_event({
        "event_type": "flywheel_started",
        "severity": "NOTABLE",
        "payload": {"pid": process.pid},
        "emitter": "system"
    })
    
    return jsonify({"success": True, "pid": process.pid})
```

**GET /api/brain/flywheel/status**

Get flywheel status.

```python
@app.route('/api/brain/flywheel/status', methods=['GET'])
def flywheel_status():
    result = subprocess.run(
        ['python3', 'agent_manager.py', 'status'],
        capture_output=True, text=True
    )
    
    return jsonify({
        "running": "RUNNING" in result.stdout,
        "output": result.stdout
    })
```

---

## Flywheel Integration

The flywheel is the background process that continuously:
1. **Watches** `events.jsonl` for new events
2. **Matches** events against `triggers.json`
3. **Activates** appropriate agents
4. **Updates** `state.json`

### Flywheel Loop (agent_manager.py)

```python
class Flywheel:
    def __init__(self):
        self.last_processed = None
        self.triggers = self.load_triggers()
    
    def run(self):
        while True:
            events = self.read_new_events()
            for event in events:
                self.process_event(event)
            time.sleep(1)  # Poll every second
    
    def process_event(self, event):
        matching_triggers = self.find_triggers(event)
        for trigger in matching_triggers:
            self.activate_agent(trigger['activates'], event)
        
        self.update_state({
            "flywheel": {
                "last_processed_event_id": event['event_id'],
                "last_processed_at": datetime.utcnow().isoformat()
            }
        })
```

---

## Implementation Checklist

- [ ] Create `/api/brain/events` endpoint
- [ ] Create `/api/brain/state` endpoints (GET/PATCH)
- [ ] Create `/api/brain/sprint/start` endpoint
- [ ] Create `/api/brain/task/assign` endpoint
- [ ] Create `/api/brain/flywheel/*` endpoints
- [ ] Integrate with existing Flask app
- [ ] Add authentication (optional - internal only)
- [ ] Test with existing agent_manager.py

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `brain_api.py` | NEW | Neural Bridge API endpoints |
| `main.py` | MODIFY | Register brain blueprint |
| `agent_manager.py` | MODIFY | Add REST client mode |

---

*Agent: Developer*  
*Status: SPECIFICATION COMPLETE*  
*Next: Implementation (requires founder approval for code changes)*  
*Confidence: HIGH*
