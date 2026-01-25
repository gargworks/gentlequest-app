# Implementation Plan - Phase 5.2: Genesis Protocol

## Goal
Enable the **Genesis Swarm** (led by the Architect) to automatically generate and save an `IMPLEMENTATION_PLAN.md` file based on a high-level mission intent. This bridges the gap between "Planning" and "Execution".

## Scope
- New Script: `scripts/genesis_swarm.py` (CLI runner for the swarm).
- New Capability: `PlanWriterOps` (Injected locally) with `save_implementation_plan` tool.
- Configuration: Update `.brain/swarms/genesis.md` to instruct existing agents to use the new tool.

## Proposed Changes

### 1. [NEW] `scripts/genesis_swarm.py`
A dedicated CLI tool that:
- Accepts a `--mission` argument (e.g., "Add Dark Mode").
- Initializes the `Architect` persona via `ContextFactory`.
- Injects a local `PlanWriterOps` capability.
- ex: `class PlanWriterOps(Capability): ... def save_implementation_plan(self, content): ...`
- Runs the `EphemeralAgent` in LLM mode.
- Prints the result.

### 2. [MODIFY] `.brain/swarms/genesis.md`
- Add explicit instruction: "You MUST use the `save_implementation_plan` tool to save your work."
- Enhance the output format description to align with the tool usage.

## Verification Plan

### Automated Test (`tests/test_genesis_protocol.py`)
1.  **Mock** the LLM to return a tool call to `save_implementation_plan`.
2.  **Run** `genesis_swarm.py` (imported as module).
3.  **Assert** that `IMPLEMENTATION_PLAN.md` was written to disk (or mocked FS).

### Manual Verification
1.  Run `python scripts/genesis_swarm.py --mission "Implement a Hello World endpoint" --test` (using Mock LLM).
2.  Verify `IMPLEMENTATION_PLAN.md` is created in valid format.
3.  (Optional) Run with real LLM if quota allows.
