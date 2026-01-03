# Hardening Patterns Research: Retry & Stuck-Task Detection
> **Event ID:** syn-h001  
> **Agent:** Researcher | Level 5 Autonomy  
> **Sprint:** Hardening Sprint  
> **Purpose:** Research SOTA patterns for FA-001 (max_retries) and FA-003 (stuck-task detection)

---

## Executive Summary

This research synthesizes best practices from SOTA multi-agent frameworks for implementing **retry mechanisms** and **stuck-task detection** to address the Architect's FA-001 and FA-003 findings.

---

## 1. Retry Pattern Research (FA-001)

### Industry Patterns

| Framework | Retry Approach | Max Retries | Backoff |
|-----------|---------------|-------------|---------|
| **Magentic-One** | Orchestrator retry loop | 3 attempts | Linear |
| **LangGraph** | Checkpoint + retry node | Configurable | None |
| **CrewAI** | Task retry with agent reassignment | 2 attempts | None |
| **Temporal.io** | Workflow retry policies | Infinite (with timeout) | Exponential |
| **Kubernetes Jobs** | Pod restart policy | 6 (default) | Exponential |

### Recommended Pattern for Nuclear

```json
{
  "retry_policy": {
    "max_retries": 3,
    "backoff_strategy": "exponential",
    "base_delay_seconds": 60,
    "max_delay_seconds": 3600,
    "escalate_on_exhaustion": true,
    "escalation_target": "founder"
  }
}
```

**Rationale:**
- **3 retries** balances recovery with avoiding infinite loops
- **Exponential backoff** prevents resource exhaustion
- **Founder escalation** after exhaustion maintains human-in-loop

### Task State Machine

```
                    ┌────────────────────────────────────────┐
                    ▼                                        │
    ┌─────────┐  assign  ┌─────────────┐  complete  ┌────────────┐
    │ PENDING │ ───────► │ IN_PROGRESS │ ─────────► │  COMPLETE  │
    └─────────┘          └─────────────┘            └────────────┘
                               │                          
                               │ fail                     
                               ▼                          
                         ┌─────────────┐                  
                         │   RETRY     │◄────────┐       
                         │ (count < 3) │─────────┘       
                         └─────────────┘   retry         
                               │                          
                               │ count >= 3               
                               ▼                          
                         ┌─────────────┐                  
                         │  ESCALATED  │                  
                         │ (to founder)│                  
                         └─────────────┘                  
```

---

## 2. Stuck-Task Detection Research (FA-003)

### Definition of "Stuck"

A task is considered stuck when:
1. Status = `in_progress` AND
2. No progress event emitted for > threshold time AND
3. No completion event received

### Industry Patterns

| System | Detection Method | Threshold | Action |
|--------|-----------------|-----------|--------|
| **Airflow** | Heartbeat monitoring | 5 min no heartbeat | Mark failed |
| **Kubernetes** | Liveness probes | Configurable | Restart pod |
| **Temporal** | Workflow timeout | Configurable | Retry/fail |
| **AWS Step Functions** | Heartbeat + Timeout | 5 min / workflow | Fail step |

### Recommended Pattern for Nuclear

```python
# Stuck Detection Algorithm
def detect_stuck_tasks(state, events, threshold_hours=24):
    stuck_tasks = []
    now = current_time()
    
    for task in state['current_sprint']['tasks']:
        if task['status'] == 'in_progress':
            last_event = find_last_event_for_task(events, task['id'])
            if last_event is None:
                time_since_assign = now - parse(task['assigned_at'])
            else:
                time_since_assign = now - parse(last_event['timestamp'])
            
            if time_since_assign > timedelta(hours=threshold_hours):
                stuck_tasks.append({
                    'task_id': task['id'],
                    'agent': task['agent'],
                    'hours_stuck': time_since_assign.total_seconds() / 3600,
                    'last_activity': last_event['timestamp'] if last_event else task['assigned_at']
                })
    
    return stuck_tasks
```

### Integration with Synthesizer

Add to Synthesizer's daily digest routine:
1. Run `detect_stuck_tasks()` 
2. If stuck tasks found, add to founder digest with severity NOTABLE
3. If stuck > 48 hours, escalate to CRITICAL

---

## 3. Implementation Recommendations

### For FA-001 (Developer↔Critic Loop)

| Field | Add to state.json tasks | Type |
|-------|------------------------|------|
| `retry_count` | Number of retries attempted | integer |
| `max_retries` | Maximum allowed retries | integer (default: 3) |
| `last_retry_at` | Timestamp of last retry | ISO timestamp |
| `escalated` | Whether escalated to founder | boolean |

### For FA-003 (Stuck Detection)

| Component | Modification | Purpose |
|-----------|-------------|---------|
| `state.json` | Add `assigned_at` to tasks | Track assignment time |
| `synthesizer.md` | Add stuck detection to 24h digest | Automated monitoring |
| `events.jsonl` | Require `progress` events | Track activity |

---

## 4. Progress Event Schema

Add new event type for ongoing task updates:

```json
{
  "event_type": "task_progress",
  "severity": "ROUTINE",
  "payload": {
    "task_id": "task-xyz",
    "agent": "developer",
    "progress_percentage": 50,
    "status_message": "Completed unit tests, starting integration",
    "checkpoint": "tests_passed"
  }
}
```

This enables:
- Fine-grained stuck detection
- Progress visibility in digests
- Checkpoint-based recovery

---

## 5. Sources

1. Temporal.io Documentation - Workflow Timeouts and Retries
2. Kubernetes Documentation - Pod Failure Handling
3. Apache Airflow - Task Monitoring and Heartbeats
4. AWS Step Functions - Execution Timeouts
5. Microsoft Magentic-One - Orchestrator Loop Patterns

---

*Agent: Researcher*  
*Status: COMPLETE*  
*Confidence: HIGH*
