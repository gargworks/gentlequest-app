# Implementation Plan - Phase 5.3: Execution Swarm CLI

## Goal
Implement the CLI entry point (`scripts/execution_swarm.py`) for the Execution Swarm (Tech Lead + Developer). This completes the "Building" phase of the Swarm Architecture, enabling the system to take an `IMPLEMENTATION_PLAN.md` and autonomously execute code changes.

## User Review Required
> [!NOTE]
> This CLI will execute code (edit files, run commands). It acts as the "Hands" of the system.

## Proposed Changes

### Scripts
#### [NEW] [execution_swarm.py](file:///Users/lokeshgarg/ai-mvp-backend/scripts/execution_swarm.py)
- **Role**: Entry point for the Execution Swarm.
- **Inputs**: `--plan` (Path to implementation plan), `--test` (Mock mode).
- **Logic**:
    1. Reads `IMPLEMENTATION_PLAN.md`.
    2. Spawns `Tech Lead` agent to break down tasks in `task.md`.
    3. Spawns `Developer` agent to execute tasks (loop).
    4. (Optional) Spawns `Fixer/Critic` for review.

### Brain Swarms
#### [MODIFY] [execution.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/.brain/swarms/execution.md)
- Ensure the protocol explicitly handles the handoff from Tech Lead to Developer.

## Verification Plan

### Automated Tests
1. **Mock Test**:
    - Run `python scripts/execution_swarm.py --plan IMPLEMENTATION_PLAN_MOCK.md --test`
    - Verify it mocks the "Task Breakdown" and "Code Execution" steps.

2. **Simulation**:
    - Run `tests/test_execution_simulation.py` (Existing) to ensure underlying Orchestrator logic holds up.

### Manual Verification
- Manually check that `task.md` is updated by the Tech Lead (in a live run, or verify via mock logs).
