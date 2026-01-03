# Hardening Technical Specifications (FA-001 to FA-005)
> **Event ID:** syn-h003  
> **Agent:** Architect | Level 5 Autonomy  
> **Sprint:** Hardening Sprint  
> **Purpose:** Technical specs for implementing audit recommendations

---

## Overview

This document provides implementation-ready specifications for the 5 findings from the Brain Audit Report.

---

## FA-001: Max Retries for Developer↔Critic Loop

### Problem
Developer and Critic can loop infinitely if code keeps failing review.

### Specification

#### Schema Addition to state.json

```json
{
  "tasks": [
    {
      "id": "task-xxx",
      "agent": "developer",
      "retry_count": 0,
      "max_retries": 3,
      "retry_history": [
        {
          "attempt": 1,
          "timestamp": "2025-12-26T12:00:00Z",
          "reason": "review_blocked: missing tests"
        }
      ],
      "escalated": false
    }
  ]
}
```

#### Trigger Modification (triggers.json)

Add condition to `review_fail` trigger:

```json
{
  "id": "review_fail",
  "event": "review_blocked",
  "emitter": "critic",
  "activates": ["developer"],
  "condition": "severity >= HIGH AND task.retry_count < task.max_retries"
}
```

Add new escalation trigger:

```json
{
  "id": "retry_exhausted",
  "event": "review_blocked",
  "emitter": "critic",
  "activates": ["synthesizer"],
  "condition": "task.retry_count >= task.max_retries",
  "action": "escalate_to_founder"
}
```

#### Event Schema for Retry

```json
{
  "event_type": "task_retry",
  "severity": "NOTABLE",
  "payload": {
    "task_id": "task-xxx",
    "agent": "developer",
    "attempt": 2,
    "reason": "Previous attempt blocked by critic",
    "max_retries": 3
  }
}
```

---

## FA-002: Citation Validation Rules

### Problem
Researcher can fabricate sources without detection.

### Specification

#### Updates to researcher.md Prompt

Add validation section:

```markdown
## Citation Requirements

**MANDATORY for all research outputs:**

1. **Source Format:**
   ```
   [N] Author/Org - "Title" (Date) - URL
   Status: VERIFIED | UNVERIFIED | INACCESSIBLE
   ```

2. **Verification Levels:**
   - VERIFIED: Directly accessed and confirmed
   - UNVERIFIED: Cited from secondary source
   - INACCESSIBLE: Unable to access, marked accordingly

3. **Prohibited Behaviors:**
   - NEVER fabricate a source
   - NEVER cite a URL without attempting access
   - ALWAYS mark uncertainty explicitly

4. **Confidence Mapping:**
   - All VERIFIED sources → HIGH confidence
   - Any UNVERIFIED sources → MEDIUM confidence max
   - Any INACCESSIBLE sources → LOW confidence max
```

#### Critic Review Checklist Addition

Add to critic.md:

```markdown
## Research Review Checklist

- [ ] All sources have verification status
- [ ] No UNVERIFIED sources for critical claims
- [ ] Confidence level matches source verification
- [ ] No hallucinated URLs (spot-check 2-3)
```

---

## FA-003: Stuck Task Detection

### Problem
Silent agent failures go undetected.

### Specification

#### Schema Addition to state.json Tasks

```json
{
  "tasks": [
    {
      "id": "task-xxx",
      "assigned_at": "2025-12-26T12:00:00Z",
      "last_progress_at": "2025-12-26T14:00:00Z",
      "expected_completion_hours": 24,
      "status": "in_progress"
    }
  ]
}
```

#### Synthesizer Daily Digest Addition

Add to synthesizer.md Function 3:

```python
def check_stuck_tasks():
    threshold_hours = 24
    warning_hours = 12
    
    stuck = []
    warning = []
    
    for task in state['current_sprint']['tasks']:
        if task['status'] == 'in_progress':
            last_activity = task.get('last_progress_at', task['assigned_at'])
            hours_since = (now - parse(last_activity)).total_seconds() / 3600
            
            if hours_since >= threshold_hours:
                stuck.append(task)
            elif hours_since >= warning_hours:
                warning.append(task)
    
    return {'stuck': stuck, 'warning': warning}
```

#### Progress Event Type

```json
{
  "event_type": "task_progress",
  "severity": "ROUTINE",
  "payload": {
    "task_id": "task-xxx",
    "agent": "developer",
    "checkpoint": "tests_passing",
    "progress_note": "Unit tests complete, starting integration"
  }
}
```

---

## FA-004: Automated State Backup

### Problem
state.json is a single point of failure.

### Specification

#### Backup Directory Structure

```
.brain/
├── backup/
│   ├── state/
│   │   ├── state_20251226.json
│   │   ├── state_20251227.json
│   │   └── ...
│   └── events/
│       ├── events_20251226.jsonl
│       └── ...
```

#### Synthesizer 72h Cycle Addition

```python
def backup_state():
    date_str = datetime.now().strftime('%Y%m%d')
    
    # Backup state.json
    shutil.copy(
        '.brain/ledger/state.json',
        f'.brain/backup/state/state_{date_str}.json'
    )
    
    # Archive events older than 7 days
    # (keep in main file, but also backup)
    shutil.copy(
        '.brain/ledger/events.jsonl',
        f'.brain/backup/events/events_{date_str}.jsonl'
    )
    
    # Cleanup: Keep only last 30 backups
    cleanup_old_backups('.brain/backup/', max_files=30)
```

#### Recovery Procedure

```markdown
## State Recovery

1. Identify last known good backup
2. Copy to active: `cp .brain/backup/state/state_YYYYMMDD.json .brain/ledger/state.json`
3. Reconcile with events since backup
4. Emit `state_recovered` event
```

---

## FA-005: Stale Pending Events Cleanup

### Problem
pending_events can accumulate without being processed.

### Specification

#### Cleanup Protocol

Add to Synthesizer 72h cycle:

```python
def cleanup_pending_events():
    processed = []
    
    for event in state['pending_events']:
        # Check if corresponding agent has completed or acknowledged
        if event_was_processed(event['event_id']):
            processed.append(event['event_id'])
    
    # Remove processed events
    state['pending_events'] = [
        e for e in state['pending_events'] 
        if e['event_id'] not in processed
    ]
    
    # Archive very old pending events (> 7 days)
    old_events = [
        e for e in state['pending_events']
        if age_hours(e) > 168
    ]
    
    if old_events:
        emit_event({
            'event_type': 'stale_events_detected',
            'severity': 'NOTABLE',
            'payload': {'count': len(old_events), 'event_ids': [e['event_id'] for e in old_events]}
        })
```

#### Event Acknowledgment Pattern

Agents should emit acknowledgment when receiving task:

```json
{
  "event_type": "task_acknowledged",
  "severity": "ROUTINE",
  "payload": {
    "task_id": "task-xxx",
    "agent": "developer",
    "original_event_id": "syn-task-xxx"
  }
}
```

---

## Implementation Priority

| Finding | Severity | Effort | Priority |
|---------|----------|--------|----------|
| FA-001 | MEDIUM | LOW | 1 (Quick win) |
| FA-003 | MEDIUM | MEDIUM | 2 (Critical for monitoring) |
| FA-002 | MEDIUM | LOW | 3 (Prompt update) |
| FA-004 | LOW | LOW | 4 (Simple script) |
| FA-005 | LOW | LOW | 5 (Cleanup routine) |

---

## Implementation Checklist

- [ ] Update state.json schema with retry and timing fields
- [ ] Update triggers.json with retry exhaustion trigger
- [ ] Update synthesizer.md with stuck detection and cleanup
- [ ] Update researcher.md with citation rules
- [ ] Update critic.md with research review checklist
- [ ] Create .brain/backup/ directory structure
- [ ] Add backup commands to 72h cycle

---

*Agent: Architect*  
*Status: COMPLETE*  
*Confidence: HIGH*
