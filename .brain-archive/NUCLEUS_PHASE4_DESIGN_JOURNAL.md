# Nucleus Phase 4: The Orchestrator (Design Journal)

> **Date:** January 10, 2026  
> **Topic:** Evolution of the Multi-Agent "Team of Teams" Architecture  
> **Status:** Implemented & Verified  
> **Authors:** Antigravity (Agent) & User

---

## 1. Executive Summary

Phase 4 marked the transition of **Nucleus** from a single-agent coding assistant to a **Multi-Agent Orchestration System** (The "Team of Teams"). 

**The Core Problem:**
A single agent (Developer) is excellent at writing code but lacks the broader context for product management, architectural foresight, and system-wide synthesis.

**The Solution:**
We decomposed the system into specialized **Personas** (Product Manager, Researcher, Architect, Developer) and connected them via an **Event-Driven Architecture (EDA)** managed by a central **Orchestrator**.

---

## 2. Architectural Evolution

### 2.1 From Monolith to Micro-Agents (Phase 4.1)

**Concept:**
Instead of one "God Mode" prompt, we created specialized system prompts for each role.

**Key Decisions:**
*   **Static Personas vs. Dynamic Generation:** We chose **Static Personas** (`.brain/agents/*.md`) for the core team.
    *   *Why?* Stability and predictability. A "Product Manager" should always behave like a PM, enforcing backlog discipline.
    *   *Trade-off:* Less flexibility than generating agents on the fly, but far more reliable for core workflows.
*   **Capability Segregation:**
    *   **WebOps** (Search/Read) was assigned *only* to the `Researcher`.
    *   **CodeOps** (Write File) was assigned *only* to the `Developer`.
    *   *Principle:* **Least Privilege**. The PM cannot accidentally delete production code; they can only write specs.

### 2.2 The Neural Pathways (Phase 4.2)

**Concept:**
How do agents talk to each other?

**Design Choice 1: Event-Driven Routing (`triggers.json`)**
*   We rejected direct agent-to-agent calls (e.g., PM calling `architect.run()`).
*   Instead, we implemented a **Pub/Sub model**.
*   **Flow:** PM emits `spec_ready` event → Orchestrator sees event → Matches trigger → Spawns Architect.
*   *Benefit:* Decoupling. Behavior can be evolved by changing `triggers.json` without modifying agent code.

**Design Choice 2: Synchronous Delegation (`brain_delegate_task`)**
*   *Problem:* Sometimes an agent needs an answer *now* (e.g., Synthesizer needs Research *during* a thought process). EDA is async/fire-and-forget.
*   *Solution:* We implemented `brain_delegate_task`.
*   *Implementation Detail:* This allows an agent to spawn a sub-agent, wait for the result, and include it in their own response.

### 2.3 The Technical Conundrum: `asyncio` Re-entrancy

**The Critical Hurdle:**
The Nucleus runtime is asynchronous. When the Synthesizer (running in an async loop) calls `brain_delegate_task`, that tool tries to run another async agent.
Python's `asyncio` does not allow `asyncio.run()` to be called from within an existing event loop.

**The "Hack" that Saved the System:**
*   **We utilized `nest_asyncio`.**
*   *Code:*
    ```python
    import nest_asyncio
    nest_asyncio.apply()
    # Now we can call loop.run_until_complete() recursively
    ```
*   *Why:* It allowed us to keep the `BrainOps` tool signature simple (synchronous return) while performing complex async operations (Agent -> LLM -> Tool) under the hood.
*   *Future Consideration:* For high-scale production, this should eventually move to a **Job Queue** (Celery/BullMQ), but for a local Agentic OS, this recursive loop provides the most "fluid" experience.

---

## 3. Component Deep Dives

### 3.1 The Orchestrator (`scripts/orchestrator.py`)
*   **Role:** The "Heartbeat". It pulses (runs via cron or loop), reads the `events.jsonl` stream, and compares it against `triggers.json`.
*   **Upgrade:** Originally a logger, we upgraded it in Phase 4.2 to actually **instantiate and execute** `EphemeralAgent`s using the `DualEngineLLM`.
*   **Verification:** Validated via `tests/test_team_execution.py`, proving that a `spec_needed` event autonomously wakes up the `Product Manager`.

### 3.2 The Triggers Ledger (`triggers.json`)
*   **Role:** The routing table.
*   **Evolution:**
    *   *v1:* Simple `id` mapping.
    *   *v2.1:* Added `user_intent` → `synthesizer`.
    *   *v2.2:* Condition logic (`always`, `severity==CRITICAL`).
*   **Key Learning:** Ensure consistency between "Artifact" versions (for documentation) and "Live" versions (in `.brain/ledger`). We had a mismatch in Phase 4.2 that caused a debugging loop. **Always Source Truth from the Live System.**

### 3.3 Fluid Sync (Phase 4.3)
*   **Concept:** Cloud-to-Local Handoff.
*   **Verification:** `tests/test_fluid_sync.py`.
    *   *Insight:* We had to **Mock the LLM** for the rigid test case because real LLMs are non-deterministic (Synthesizer might chat instead of delegate).
    *   *Principle:* **Test the Plumbing, Trust the Model.** The test verified that *if* the Model decides to delegate, the System *can* execute it.

---

## 4. Operational Principles for Future Refactoring

1.  **Events First:** If you want to add a new behavior, defining it as an **Event** (`triggers.json`) is better than hardcoding it.
2.  **Persona Purity:** Do not give `Developer` tools to the `Architect`. Keep the roles distinct to force the "Spec -> Code" handover. This ensures documentation (`spec.md`) is always generated.
3.  **Recursion is Powerful but Dangerous:** `brain_delegate_task` allows infinite depth (Agent A -> B -> C).
    *   *Guardrail:* Ensure we don't create circular loops (A triggers B triggers A).
    *   *Monitor:* `events.jsonl` provides the trace.

## 5. Conclusion

The standard is now set. Nucleus is no longer just a script; it is a **Society of Agents**. 
Any future upgrades should respect the **Event-Driven-Architecture** and the **Specialized Persona** boundaries established here.

---
*End of Design Journal - Phase 4*
