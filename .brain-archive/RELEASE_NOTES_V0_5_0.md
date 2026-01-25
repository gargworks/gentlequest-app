# Nucleus v0.5.0 Release Notes
**Codename:** The Swarm Engine

## Overview
This release marks a major architectural shift from single-agent workflows to the "Team of Teams" architecture. Nucleus now features a native Swarm Orchestrator capable of managing specialized agent swarms (Genesis for planning, Execution for building) with autonomous handoffs.

## Key Features

### 1. Swarm Orchestration (Team of Teams)
- **New `SwarmsOrchestrator`**: A centralized engine to manage multi-agent missions.
- **Swarm Relay**: Autonomous handoff between Planning (Genesis) and Building (Execution) phases.
- **Persistence**: Active swarms are now persisted to `.brain/swarms/state.json`, surviving server restarts.

### 2. Specialized Personas
- **Tech Lead**: The execution lead, responsible for code quality and implementation.
- **Product Owner**: The product lead, converting intent to backlog.
- **Architect**: The system designer.
- **Genesis Swarm**: A coordinated group (Architect + PM) that turns raw ideas into `implementation_plan.md`.

### 3. Nucleus HUD (Observability)
- **SwarmMonitor**: real-time visualization of active swarms via the Dashboard.
- **API**: New `/api/swarms` endpoint for external monitoring.
- **Outcome Dashboard**: Real-time GAD-7/PHQ-9 visualization for clinical pilot tracking.


### 4. Memory & Commitments
- **RAG + Graph Memory**: Enhanced long-term context retention.
- **Integrated Ledger**: Tasks and Commitments are unified in the Brain.

## Breaking Changes
- `agent_manager.py` (Legacy Flywheel) has been archived. Use `nucleas-init` or the MCP `brain_orchestrate_swarm` tool instead.

## Getting Started
To trigger a new mission:
```bash
# Via MCP
brain_orchestrate_swarm(mission="Your Mission Here", swarm_type="genesis")
```

## Known Issues
- HUD autorefresh polling is currently set to 5s.
- Manual agent approval step is currently bypassed in `auto` mode.

---
*Built with <3 by the Nucleus Team.*
