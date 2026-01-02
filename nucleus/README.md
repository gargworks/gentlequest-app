# 🧠 Nucleus Brain

> **One Brain, Many Interfaces.**

Nucleus is the central state management system for AI agents. It provides:

- **State Management**: Persistent brain state with JSON fallback
- **Event Ledger**: Append-only event log for agent activity
- **MCP Integration**: Model Context Protocol server (planned)

## Quick Start

```bash
# From project root
PYTHONPATH=. python3 nucleus/clients/cli/nucleus_cli.py status
```

Output:
```
🧠 NUCLEUS STATUS
========================================
Sprint: Integration & Polish Sprint
Status: ACTIVE
Events: 35
Tasks: 15
========================================
```

## Package Structure

```
nucleus/
├── __init__.py         # Package entry (get_state, set_state, emit_event)
├── state.py            # State management with JSON fallback
├── events.py           # Event ledger (JSONL format)
├── setup.py            # pip installable package
├── mcp_server/         # Future MCP server implementation
└── clients/
    ├── cli/            # nucleus CLI tool
    └── telegram/       # Telegram bot client (planned)
```

## API

### State Management

```python
from nucleus import get_state, set_state

# Get full state
state = get_state()

# Get nested path
sprint_name = get_state("current_sprint.name")

# Update state (shallow merge)
set_state({"current_sprint": {"name": "New Sprint", "status": "ACTIVE"}})
```

### Event Emission

```python
from nucleus import emit_event, get_events

# Emit an event
event_id = emit_event(
    emitter="my_agent",
    event_type="task_completed",
    payload={"task": "example", "duration_ms": 150}
)

# Get recent events
events = get_events(limit=10)
```

## CLI Commands

```bash
nucleus status              # Show brain status
nucleus sprint "Sprint 1"   # Start a new sprint
nucleus event task_done     # Emit an event
```

## Integration

### With MCP Server

The Nucleus MCP server exposes these tools:
- `brain_get_state` - Read brain state
- `brain_update_state` - Update brain state
- `brain_emit_event` - Emit events to ledger
- `brain_read_events` - Read recent events

### With Telegram Bot

(Planned) Commands like `/status` and `/sprint` will connect directly to Nucleus.

---

## File Locations

- **State**: `.brain/ledger/state.json`
- **Events**: `.brain/ledger/events.jsonl`
- **Artifacts**: `.brain/artifacts/`

---

*Part of the GentleQuest AI Assistant project.*
