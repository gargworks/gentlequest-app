# Implementation Plan - Phase 61: Genesis of The Oracle (The Co-Founder)

## Goal Description
Build the "Antifragile Co-founder" (The Oracle).
This is not just another agent; it is a higher-order Governance Entity that runs strategic simulations ("Gladiator Games") to guide business decisions.
It operates on the "Sovereign Network" we built in Phase 57-60.

## User Review Required
> [!IMPORTANT]
> **Paradigm Shift:** We are moving from "Building Features" to "Simulating Strategy".
> The `GladiatorSimulator` will use LLM tokens to simulate market outcomes. This incurs cost.
> We initiate with a "Genesis Run" (Chat 36).

## Proposed Changes

### 1. The Oracle Identity (Chat 35)
#### [NEW] `mcp_server_nucleus/runtime/agents/oracle/manifest.json`
- Define `nucleus.core.oracle`.
- Capabilities: `STRATEGY` (Read/Write to `.brain/strategy`).

#### [NEW] `mcp_server_nucleus/runtime/capabilities/strategy.py`
- `StrategyCapability`: Allows reading/writing strategy docs and appending to `DECISION_RECORD.md`.

### 2. The Simulation Engine (Chat 36)
#### [NEW] `scripts/gladiator_simulator.py`
- Implements the "Titans' Round Table" prompt loop.
- Inputs: A strategic proposition (e.g., "Pivot to Enterprise").
- Logic:
  - Roleplay 5 Titans (Jobs, Bezos, Musk, Gates, Thiel).
  - Score the proposition.
  - Output a Verdict.

### 3. The Board Meeting (Chat 37)
#### [NEW] `scripts/oracle_genesis.py`
- The "Self-Reflection" Loop.
- The Oracle reads `PROTOCOL_THE_ORACLE.md`.
- It critiques its own existence.
- It generates `PROTOCOL_THE_ORACLE_v2.md`.

### 4. The Sovereign Launch (Chat 38)
#### [MODIFY] `mcp_server_nucleus/runtime/broker.py`
- Ensure `ContextBroker` supports "Consultant" listings (Service Providers, not just Data Sellers).

## Verification Plan

### Automated Tests
1.  **Identity:** `verify_oracle_boot.py` (Similar to `verify_ops_agent.py` but for Oracle).
2.  **Simulation:** Run `scripts/gladiator_simulator.py "Test Strategy"` and verify `DECISION_RECORD.md` is updated.
3.  **Genesis:** Run `scripts/oracle_genesis.py` and verify `PROTOCOL_THE_ORACLE_v2.md` is created.
