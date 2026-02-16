# 🧠 The Nucleus Hypervisor: System Architecture (v0.8.0)

**Concept**: Agent Operating System (AOS).
**Function**: Virtualization of Identity & State for Polyglot Agents.
**Status**: Forward-Looking Specification ("Beyond SOTA").

---

## 🏗️ The Problem: "Context Splintering"
Current SOTA tools (Claude Code, CrewAI, LangGraph) behave like Operating Systems. They demand total control of the environment. When you run two of them, they collide.
*   **Claude Code** overwrites files.
*   **OpenClaw** processes outdated state.
*   **LangGraph** hallucinates on stale checkpoints.

## 🛡️ The Solution: The Hypervisor
Nucleus retreats from being "Another Agent" to being the **Hypervisor** that sits *underneath* them.

### Layer 1: The Ledger Kernel (VFS)
The Virtual File System (VFS) intercepts all writes.
*   **Standard OS**: `write(file, content)`
*   **Nucleus OS**: `write(file, content, identity_signature)`

**Mechanism**:
1.  **Identity Injection**: When Claude Code runs, we inject `LD_PRELOAD` or similar tags to its process.
2.  **Atomic Writes**: Every write to the `brain/` is a Transaction.
3.  **Conflict Resolution**:
    *   If `Red Team` locks `src/auth.py`, `Blue Team` (Claude) writes **Fail** or **Fork**.
    *   *Implementation*: `sync_ops.py` checks Identity before allowing writes.

### Layer 2: The Context Switcher (Polyglot Injection)
Nucleus dynamically generates the "Context" that each agent sees.
*   **SOTA**: Context is siloed in `.cursorrules` or `.crewai`.
*   **BEYOND**: Nucleus creates a **Universal Context Kernel**.
*   We generate `.cursorrules` *dynamically* based on the `current_phase` of the project.
*   We inject `os.environ` into CrewAI based on the `ledger` state.

### Layer 3: The Identity Firewall
Nucleus enforces "Sovereign Identity".
*   **The Check**: Before `execute_tool()` is allowed, Nucleus verifies `_current_identity`.
*   **The Block**: If `unknown_agent` tries to delete `production_db`, the tool call is rejected at the *Kernel Level*.
*   **The Log**: Every rejection is signed and stored in the Ledger.

### Layer 4: The Threading Hypervisor (Surpassing SOTA)
To dominate the "Threading War", Nucleus implements specific countermeasures:

*   **Atomic Composer Locking (vs Cursor)**:
    *   *Problem*: Cursor Composer has race conditions.
    *   *Nucleus*: Implements a **File-Level Mutex** in the Ledger. If Agent A has a "Write Intent", Agent B (Composer) receives a "423 Locked" signal until the customized MCP tool releases it.
*   **Cascade Firewalls (vs Windsurf)**:
    *   *Problem*: Windsurf Cascade bleeds context between projects.
    *   *Nucleus*: Monitors `file_access_log`. If a Cascade touches `Project B` files while in `Project A` mode, Nucleus **Force-Terminates** the context stream or alerts the user to "Fork the Cascade".
*   **Mode-Switched Context Wiping (vs Kilo)**:
    *   *Problem*: Kilo "Coder" inherits "Architect" exploits.
    *   *Nucleus*: Enforces a **Context Flush Protocol** (CFP) when `NUCLEUS_AGENT_ID` changes.

---

## 🔬 The Infinite Simulation: Stress Test
We simulated the "Tsar Bomba" scenario:
1.  **Claude Code** refactors the entire codebase.
2.  **OpenClaw** simultaneously patches a security hole.
3.  **Replit Agent** deploys the app.

**Without Hypervisor**: The deployment fails, the patch is lost, the code is corrupted.
**With Hypervisor**:
1.  Nucleus detects Claude's heavy write volume. **Locks** the file system for "Maintenance".
2.  OpenClaw's patch is queued as a **Pending Merge**.
3.  Replit Agent receives a **"Deployment Blocked"** signal until the merge resolves.
4.  *Result*: Order.

## 🚀 Implementation Path
We are currently at **Layer 0 (The MCP Server)**.
To reach Hypervisor status, we must building:
1.  **The Sentinel**: A Daemon that watches file IO (Watchdog on steroids).
2.  **The Wrapper**: A unified CLI (`nuc run claude`) that sets up the environment.
3.  **The Visualizer**: A "God View" dashboard showing which agent is touching which file in real-time.
