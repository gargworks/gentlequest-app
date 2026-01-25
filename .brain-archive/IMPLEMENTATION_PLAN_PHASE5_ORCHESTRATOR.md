
# Implementation Plan: Nucleus Orchestrator (Phase 5)

## Goal
Implement the **Orchestrator** to manage "Team of Teams" execution.
The Orchestrator spawns Swarms (Genesis, Execution) for complex missions.

## User Review Required
> [!IMPORTANT]
> This phase moves from "Single Agent" to "Multi-Agent" architecture.
> Initial release supports the **Genesis Swarm** (Planning).

## Proposed Changes

### `mcp-server-nucleus`

#### [NEW] `src/mcp_server_nucleus/runtime/orchestrator.py`
- Class `SwarmsOrchestrator`
  - `start_mission(mission: str, swarm_type: str)`
  - `_spawn_swarm_lead(swarm_type)`: Loads swarm definition and spawns the Lead Agent.
  - `_load_swarm_config(swarm_type)`: Reads `.brain/swarms/{swarm_type}.md`.

#### [MODIFY] `src/mcp_server_nucleus/__init__.py`
- Export `brain_orchestrate_swarm(mission: str, swarm_type='genesis')`.

#### [NEW] `.brain/swarms/genesis.md`
- **Identity**: Genesis Swarm Lead (Mission Control).
- **Mission**: Plan complex features.
- **Team**: Architect, Product Owner, Strategist.
- **Protocol**: 
  1. Analyze Mission.
  2. Consult Team (simulated via tools or sub-prompts).
  3. Output `IMPLEMENTATION_PLAN.md`.

## Verification Plan

### Automated Verification
- **Test Script**: `tests/test_orchestrator.py`.
- **Scenario**:
  - `brain_orchestrate_swarm("Refactor Auth", "genesis")`.
  - Assert that `Genesis Swarm Lead` is initialized with the correct context.
  - Assert that a "Mission ID" is returned.

### Manual Verification
- **Spawn**: `nucleus spawn "Plan the new Payment Gateway using Genesis Swarm"`
- **Expectation**: The system acknowledges "Deploying Genesis Swarm" and returns a plan ID.
