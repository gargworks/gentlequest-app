
# Walkthrough: The Orchestrator (Phase 5.1)

> **Date:** 2026-01-11
> **Status:** ✅ Completed
> **Target:** `mcp-server-nucleus`

## 🎯 Goal
Implement the **Orchestrator** (Mission Control) to enable multi-agent "Team of Teams" architecture.
The Orchestrator spawns specific **Swarms** (e.g., Genesis for Planning) to handle complex missions.

## 🛠 Changes Implemented

### 1. Swarms Orchestrator (`runtime/orchestrator.py`)
- **Class**: `SwarmsOrchestrator`
- **Function**: `start_mission(mission, swarm_type)`
- **Logic**:
  1. Loads Swarm Config (Lead persona, Protocol).
  2. Spawns "Lead Agent" context.
  3. Injects **Protocol Content** from `.brain/swarms/`.
  4. Returns a Mission ID.

### 2. Genesis Swarm Definition (`.brain/swarms/genesis.md`)
- **Mission**: Planning & Architecture.
- **Lead**: Architect / Product Owner.
- **Outputs**: `IMPLEMENTATION_PLAN.md`.

### 3. Tool Exposure (`__init__.py`)
- Exported `brain_orchestrate_swarm` tool.
- Capable of initializing `genesis` or `execution` swarms.

## ✅ Verification
- **Test Script**: `tests/test_orchestrator.py` (Passed).
- **Result**:
  - Orchestrator successfully spawned "Architect" lead.
  - Context correctly included the full "Genesis Swarm Protocol".

## 🚀 How to use
```bash
nucleus spawn "Plan the migration to PostgreSQL"
# Agent calls: brain_orchestrate_swarm("Plan migration", "genesis")
```
