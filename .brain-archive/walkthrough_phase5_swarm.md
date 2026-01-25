# Walkthrough: Nucleus Team of Teams (Phase 5)

> [!NOTE]
> This phase implemented the **"Team of Teams"** architecture, transforming Nucleus from a single-agent system into a multi-swarm orchestrator.

## 🎯 Objective
Enable true autonomy by splitting the workflow into two specialized swarms:
1.  **Genesis Swarm**: Planning & Strategy (Architect, Product Owner, Strategist).
2.  **Execution Swarm**: Building & Engineering (Tech Lead, Developer, Fixer).
3.  **The Relay**: Autonomous handoff between swarms.

## 🏗️ Architecture Implemented

### 1. Swarm Protocols (`.brain/swarms/`)
We defined "Constitutions" for each swarm that dictate their mission and roles.
- **[genesis.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/.brain/swarms/genesis.md)**: "Plan before you build." Output: `IMPLEMENTATION_PLAN.md`.
- **[execution.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/.brain/swarms/execution.md)**: "Build the plan." Input: `IMPLEMENTATION_PLAN.md`.

### 2. Specialized Personas (`.brain/agents/`)
We defined the members of each squad. The Lead Agent "simulates" the squad by having their perspectives injected into the context.
- **Planning Squad**: `Architect` (Lead), `Product Owner`, `Strategist`.
- **Building Squad**: `Tech Lead` (Lead), `Developer`, `Fixer`.

### 3. The Orchestrator (`orchestrator.py`)
The logic that binds it all together.
- **Dynamic Injection**: Loads protocol and persona files at runtime.
- **Simulated Squads**: Injects squad contexts into the Lead Agent's prompt.
- **The Relay**: Enables agents to spawn new swarms via `brain_orchestrate_swarm`.

### 4. Tooling Upgrade (`brain_ops.py`)
- Added `brain_orchestrate_swarm` to `BrainOps` capability.
- Registered `Tech Lead` and `Product Owner` in `ContextFactory`.

## 🧪 Verification

### Automated Tests
We created a suite of simulation tests to verify the architecture:

1.  **Genesis Simulation**: `python3 tests/test_genesis_simulation.py`
    - Verifies correct injection of Architect, PO, and Strategist contexts.
2.  **Execution Simulation**: `python3 tests/test_execution_simulation.py`
    - Verifies Tech Lead and Developer contexts.
3.  **Swarm Relay**: `python3 tests/test_swarm_relay.py`
    - Verifies that an agent can call `brain_orchestrate_swarm` to trigger a handoff.

### Manual Verification
1.  **Start a Genesis Mission**:
    ```python
    orchestrator.start_mission("Create a new login page", "genesis")
    ```
2.  **Observe Handoff**:
    - The Genesis Swarm produces a plan.
    - The Genesis Swarm calls `brain_orchestrate_swarm(mission="Execute...", swarm_type="execution")`.
    - The Execution Swarm starts with `Tech Lead` persona.

## 📜 Key Artifacts
- [factory.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/factory.py) (Updated Registry)
- [orchestrator.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/orchestrator.py) (The Brain)
- [brain_ops.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/capabilities/brain_ops.py) (The Tool)

## 🚀 Next Steps
With the "Brain" fully operational, we can now proceed to **Phase 6: Integration & Polish** (if planned) or start using the system to build itself.
