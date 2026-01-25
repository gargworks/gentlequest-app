# 🧬 Design Journal - Phase 7: The Orchestrator (Multi-Agent Swarm)

## 1. Context
We have "Independent Agents" (Coder, Critic, etc.).
We have "Tools" (brain_critique_code).
They are currently manual: User calls `brain_critique_code`.

## 2. Problem
Agents don't talk to each other autonomously.
The `Developer` doesn't know to ask the `Critic` for a review.
The `Synthesizer` doesn't know how to delegate sub-tasks to the `Developer`.

## 3. Solution (The Swarm)
We need a **Swarm Protocol** where agents can:
1.  **Delegate**: Spawn sub-agents for specialized tasks.
2.  **Handoff**: Pass results to the next agent in a chain.
3.  **Collaborate**: Share a common "Context" (Workplace).

## 4. Architecture
*   **Cluster**: `Orchestration`
*   **Tool**: `brain_orchestrate_swarm(mission)`
    *   Acts as a Project Manager.
    *   Breaks mission into sub-tasks.
    *   Assigns tasks to existing Personas (`Developer`, `Critic`, `Researcher`).
*   **Mechanism**:
    *   **Shared Memory**: A temporary `.brain/swarm/{session_id}/` workspace.
    *   **Event Bus**: Agents emit `task_complete` events which trigger the Orchestrator to assign the next task.

## 5. Implementation Plan
1.  **Persona**: Update `synthesizer.md` to be the "Swarm Leader".
2.  **Tool**: `brain_orchestrate_swarm` (LLM-based planner).
3.  **Integration**: Update `brain_spawn_agent` to support "Reply-To" or "Next-Step" directives.
4.  **Verification**: Execute a `Synthesizer` -> `Developer` -> `Critic` chain.
