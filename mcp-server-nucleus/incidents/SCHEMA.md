# Nucleus Incident Schema — Phase F

This document defines the canonical schema for machine-readable incident
records written by the incident controller.

## Incident JSON Schema

Each incident produces a file at `incidents/YYYY-MM/INCIDENT-<id>.json`.

```json
{
  "schema_version": "1.0.0",
  "id": "INC-20260314T050336-DEAD_PIP",
  "type": "dead_pipeline",
  "severity": "warning",
  "detected_at": "2026-03-14T05:03:36.123456Z",
  "resolved_at": null,
  "resolution_status": "pending",
  "summary": "No commands recorded in the last 6 hours",
  "metrics_snapshot": {
    "total_commands_6h": 0.0
  },
  "actions": [
    {
      "name": "restart_collector",
      "target": "nucleus-otel-collector",
      "result": "success",
      "timestamp": "2026-03-14T05:03:37.000000Z"
    }
  ],
  "playbook": "dead_pipeline",
  "evaluation": {
    "evaluated_at": null,
    "delay_seconds": 120,
    "metrics_after": {},
    "success_criteria_met": null,
    "resolution_status": "pending"
  },
  "policy_snapshot": {
    "cooldown_minutes": 30,
    "action_flags": {
      "restart_collector": true
    },
    "success_rate": null
  }
}
```

## Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Schema version, currently `"1.0.0"` |
| `id` | string | Unique incident ID: `INC-<timestamp>-<type_prefix>` |
| `type` | string | Incident type key matching a playbook name |
| `severity` | string | `"info"`, `"warning"`, or `"critical"` |
| `detected_at` | string | ISO 8601 UTC timestamp of detection |
| `resolved_at` | string\|null | ISO 8601 UTC timestamp when resolved, or null |
| `resolution_status` | string | One of: `"pending"`, `"success"`, `"partial"`, `"failed"`, `"unknown"` |
| `summary` | string | Human-readable one-line summary |
| `metrics_snapshot` | object | Key metrics at time of detection |
| `actions` | array | Ordered list of actions taken (see below) |
| `playbook` | string | Name of the playbook that handled this incident |
| `evaluation` | object | Outcome evaluation data (see below) |
| `policy_snapshot` | object | Policy state at time of incident |

### Action Entry

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Action primitive name (e.g. `restart_collector`) |
| `target` | string | Target of the action (container name, command, etc.) |
| `result` | string | `"success"`, `"failed: <reason>"`, `"skipped"` |
| `timestamp` | string | ISO 8601 UTC timestamp |

### Evaluation Entry

| Field | Type | Description |
|-------|------|-------------|
| `evaluated_at` | string\|null | When the follow-up evaluation ran |
| `delay_seconds` | int | Configured delay before evaluation |
| `metrics_after` | object | Metrics re-queried after the delay |
| `success_criteria_met` | bool\|null | Whether the playbook's success criteria passed |
| `resolution_status` | string | Final status after evaluation |

### Resolution Status Values

| Status | Meaning |
|--------|---------|
| `pending` | Actions taken, awaiting evaluation |
| `success` | Follow-up evaluation confirms metrics recovered |
| `partial` | Some metrics improved but not all criteria met |
| `failed` | Metrics did not improve after actions |
| `unknown` | Evaluation could not determine outcome (e.g. Prometheus unreachable) |

## Actions Log Schema

Each line in `incidents/actions.log` is a JSON object:

```json
{
  "timestamp": "2026-03-14T05:03:37.000000Z",
  "incident_id": "INC-20260314T050336-DEAD_PIP",
  "action": "restart_collector",
  "target": "nucleus-otel-collector",
  "result": "success",
  "details": "",
  "playbook": "dead_pipeline"
}
```

The `playbook` field (added in Phase F) links every action entry back to the
playbook that triggered it.

## Policy State Schema

See `incidents/policy_state.json` — managed exclusively by the controller.

```json
{
  "schema_version": "1.0.0",
  "updated_at": "2026-03-14T05:10:00Z",
  "incident_types": {
    "dead_pipeline": {
      "recent_outcomes": ["success", "success", "failed"],
      "success_rate": 0.67,
      "total_incidents": 3,
      "last_incident_at": "2026-03-14T05:03:36Z",
      "action_overrides": {},
      "cooldown_multiplier": 1.0
    }
  }
}
```
