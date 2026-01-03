# ⚛️ Nuclear Agentic Engine: Operations Manual (v1.0)
**Governing Protocols for the Subatomic Flywheel**

## 1. Executive Summary
This document defines the operational heartbeat of the Nuclear Agentic Engine. It is the bridge between Founder intent and Agentic execution. Adherence to these routines ensures 100% portability, zero context rot, and recursive self-improvement.

---

## 2. The Founder’s Daily Rhythm
The engine is designed to reduce cognitive load by 80%. Follow this cycle:

### ☀️ Phase 1: Strategic Injection (10 Mins)
*   **Audit:** Review the latest `digest_*.md` in `.brain/artifacts/synthesis/`.
*   **Ignition:** If the previous sprint is complete, set the new trajectory via CLI:
    ```bash
    python3 agent_manager.py sprint "New Mission Objective"
    python3 agent_manager.py start
    ```
*   **Constraint:** Never prompt worker agents directly. Always command via the **Synthesizer** or **CLI**.

### 🌑 Phase 2: Recursive Review (15 Mins)
*   **Watchdog Check:** Monitor the live pulse:
    ```bash
    tail -f .brain/ledger/events.jsonl
    ```
*   **State Health:** Run `python3 agent_manager.py status` to ensure no agents are "stuck" or in a hallucination loop.
*   **Approval:** If a `CRITICAL` escalation is flagged, review the `decisions.md` and provide a "Yes/No" to the Synthesizer thread.

---

## 3. Maintenance & Evolution Protocols
The "Moat" is maintained through proactive system hygiene.

### A. The 72-Hour "Meta-Sprint"
Every 3 days, trigger a **Recursive Self-Improvement** cycle:
*   **Directive:** *"Agents: Review learnings.md and optimization_log.md. Update your own system prompts in .brain/agents/ to eliminate 10% of operational friction."*

### B. The Golden Image Snapshot
Before any major structural change, protect the "Showroom" version:
*   **Action:** Copy the latest `.brain/agents/` and `event_schema.json` to `BRAIN_PRODUCT_V1/`.
*   **Cleaning:** Ensure no project-specific logs (`events.jsonl`) enter the copiable version.

### C. Garbage Collection (Context Hygiene)
When the ledger exceeds 500 lines:
*   **Command:** *"Synthesizer: Perform Garbage Collection. Condense recent events into patterns.md and archive the raw log stream."*

---

## 4. Fault Tolerance Guardrails
These rules are hard-coded into the 2025 Agentic Hive:

1.  **Max Retries (3):** Agents must attempt a failed task 3 times with exponential backoff before escalating to `CRITICAL`.
2.  **Stuck Task Detection:** The `agent_manager.py` will autonomously restart any thread silent for >10 minutes during an active task.
3.  **Human-in-the-Loop (HITL):** Strategic pivots, financial commits, or core codebase merges require a `FOUNDER_APPROVED` flag in `state.json`.

---

## 5. Tool Fluidity & Portability
This engine is tool-agnostic. To migrate:
1.  Zip the `.brain/` folder.
2.  Unzip in the new environment (Windsurf, Antigravity, or custom IDE).
3.  Run `python3 agent_manager.py start`.
4.  **Result:** The "Company Brain" resumes its current thought process instantly.

---
**Status:** ACTIVE | **Version:** 1.0.0-Nuclear  
**Authored by:** Founder's Desk | **Validated by:** Synthesizer Agent