# Nucleus Multi-Agent Orchestration Protocol
> **Version:** 1.0 (Draft)
> **Status:** Definition Phase
> **Objective:** Define a First Principle solution for seamless multi-agent collaboration.

## 1. The Core Philosophy (First Principles)
Traditional multi-agent systems fail because they rely on complex, brittle direct communication (Agent A talks to Agent B).
Nucleus solves this by uncoupling **Compute** (Agents) from **State** (Ledger).

**The Architecture:**
1.  **Registry (DNS):** "Who is available?" (`thread_registry.md`)
2.  **Ledger (Queue):** "What needs doing?" (`state.json`)
3.  **Synthesizer (Router):** "Who should do what?" (The Intelligence Layer)

---

## 2. Critique of Current State (v0.2.6)
**The Verdict:** Structurally sound, but Operationally manual.

| Dimension | Current Implementation | Production Grade (Target) |
| :--- | :--- | :--- |
| **Discovery** | Manual File Read | Semantic Similarity Search |
| **Dispatch** | Human/Agent edits JSON | **Automated Synthesizer Loop** |
| **Lock-in** | "Honor System" | Cryptographic Task Signing |
| **Latency** | Polling `state.json` | WebSocket/SSE Push Events |

### The Friction Points
1.  **JSON Editing:** Asking users/agents to manually edit `state.json` is error-prone.
2.  **Latency:** Agents might work on stale data if they don't poll frequently.
3.  **Orphaned Tasks:** If an agent dies, the task sits in `TODO` forever.

---

## 3. The Path to "Seamless" (v1.0)
To make this "invisible magic" for the user, we need to implement **The Nucleus Autopilot**.

### A. The Synthesizer Loop (The Brain)
Instead of a passive role, the **Synthesizer** becomes a daemon agent that:
1.  **Ingests** rough user intent ("We need better docs").
2.  **Decomposes** it into atomic tasks.
3.  **Matches** tasks to Registry roles.
4.  **Dispatches** via `brain_delegate_task(task_desc, role)`.

### B. New Tooling Required
We need to move from "Raw File Edits" to "Atomic Transactions":

- `brain_claim_task(task_id)`: Atomically locks a task.
- `brain_delegate_task(description, target_role)`: Creates task & notifies role.
- `brain_heartbeat(thread_id)`: Proves agent is alive.

## 4. Production Workflow (The Vision)
1.  **User:** "We need a new landing page."
2.  **Synthesizer (Auto):**
    - Creates Task 1: "Design Mockup" (Role: Designer)
    - Creates Task 2: "Implement React Component" (Role: Developer)
3.  **Designer Agent:** Wakes up (Event Trigger), sees Task 1, executes, marks Complete.
4.  **Developer Agent:** Sees Task 1 Complete, picks up Task 2.
5.  **User:** Sees progress bars moving in real-time.

## 5. Conclusion
Your intuition is correct. The **Registry + Ledger** is the correct *Storage* layer.
To make it seamless, we simply need to automate the *Control Plane* (The Synthesizer).
