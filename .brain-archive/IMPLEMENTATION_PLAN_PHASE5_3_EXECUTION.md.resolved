
# Implementation Plan: Execution Swarm (Phase 5.3)

## Goal
Define the **Execution Swarm** ("The Builders") to handle code generation and repair.
This complements the Genesis Swarm ("The Planners").

## User Review Required
> [!NOTE]
> This creates the "Tech Lead" and "Developer" personas.
> The "Fixer" persona (Phase 4) is also part of this swarm.

## Proposed Changes

### `.brain/agents/`

#### [NEW] `tech_lead.md`
- **Role**: Operational Leader.
- **Focus**: Task breakdown, standard adherence, code review.
- **Style**: Pragmatic, detail-oriented.

#### [NEW] `developer.md`
- **Role**: Coder.
- **Focus**: Writing clean, working code.
- **Style**: Efficient, code-first.

### `.brain/swarms/`

#### [NEW] `execution.md`
- **Mission**: Implement the `IMPLEMENTATION_PLAN.md`.
- **Protocol**:
  1. Read Plan.
  2. Tech Lead breaks down tasks.
  3. Developer executes tasks.
  4. Fixer repairs failures.

## Verification Plan

### Automated Verification
- **Test Script**: `tests/test_execution_simulation.py`.
- **Logic**:
  - Instantiate `SwarmsOrchestrator`.
  - Start an "execution" mission.
  - Verify `Tech Lead`, `Developer`, and `Fixer` contexts are injected.

### Manual Verification
- **Spawn**: `nucleus spawn "Build the login page using Execution Swarm"`
- **Expectation**: Orchestrator acknowledges and sets up the context.
