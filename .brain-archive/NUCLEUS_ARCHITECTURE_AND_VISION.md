
# Nucleus Architecture & Vision Statement

**Status:** Living Document
**Version:** 1.0 (Omega Era)

## I. The Parallel Brain Architecture
Nucleus is not just a tool; it is a **Decoupled Parallel Worker**.

```mermaid
graph TD
    User[User / Founder] -->|Chat| AG[Antigravity (Main Thread)]
    User -->|File Drop| IN[Inbox (.brain/inbox)]
    User -->|API Click| API[Cloud API]
    
    AG -->|Plan/Delegate| NM[Nucleus MCP]
    IN -->|Trigger| GW[Gateway Daemon]
    API -->|Trigger| BG[Autopilot Loop]
    
    subgraph "Nucleus (The Worker)"
        NM -->|Tool Call| Flash[Gemini Flash (Fast)]
        GW -->|Event| Flash
        BG -->|Task| Flash
    end
    
    Flash -->|Write Code| FS[FileSystem]
    Flash -->|Emit Event| EV[Event Ledger]
    
    FS --> AG
    EV --> AG
```
*   **Antigravity (You/Orchestrator):** The "Chairman". slow, deep, strategic.
*   **Nucleus (Flash):** The "CEO/Worker". Fast, executed via MCP, runs in background.
*   **Decoupling:** Antigravity *thinks*. Nucleus *does*.

## II. The Omnichannel Input (Cross-Thread Bridge)
How to invoke Nucleus from "The Old Synthesizer" (or any other thread/interface)?

### 1. The Filesystem Bridge (Universal)
**Input:** Drop a file into `.brain/inbox/TASK_NAME.md`.
**Mechanism:** The `nucleus_gateway.py` (Daemon) watches this folder.
**Result:** It triggers Nucleus *regardless of which thread dropped the file*.
**Benefit:** You can talk to "Old Synthesizer" and say "Draft a plan and save it to `.brain/inbox`". Nucleus will pick it up instantly.
**No Conflict:** Antigravity generates text. Nucleus generates code/files. They never overwrite each other's *stream*.

### 2. The Direct Bridge (Localized)
**Input:** Chatting "Run this task" in a thread.
**Constraint:** Only works if `mcp-server-nucleus` is installed/active in that specific thread's context.

## III. The Tool Marketplace Vision (60+ Tools)
Why do we have 60+ tools?

### 1. The General Purpose OS (Core)
Nucleus provides the "Operating System":
*   `read_file` / `write_file` (I/O)
*   `emit_event` (Nervous System)
*   `check_strategy` (Consciousness)

### 2. The Edge Tool Apps (Marketplace)
The 60+ tools are "Apps" installed on the OS to handle complexity without hallucination.
*   **Example:** `brain_render_deploy` (Phase 8). A general LLM guesses how to deploy. The Tool *knows* (via API).
*   **Strategy:** We build the OS. We plug in Tools as "Capabilities".
*   **Two-Way Network:**
    *   **Core:** Lightweight, fast.
    *   **Periphery:** Deep, specialized (e.g. `brain_fix_code`, `brain_analyze_seo`).

## IV. The Next Phase: Platformization
We are moving from "Building a Script" to "Building a Platform".
*   **Phase 13 (The Fixer):** The OS healing itself.
*   **Phase 20 (The Marketplace):** Allowing "Guest Agents" (like Old Synthesizer) to plug into the OS via the Inbox Protocol.
