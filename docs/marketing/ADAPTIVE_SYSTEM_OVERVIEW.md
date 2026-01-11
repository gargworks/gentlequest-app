# Marketing Autopilot: System Overview & Forward Plan

## 1. How It Works (The "Three-Engine" Architecture)

The system is designed as a **Self-Correction Loop** rather than a linear script. It consists of three parts:

### A. The Front-End (The "Cockpit")
*   **What it is:** The local Marketing Dashboard (`http://localhost:9999`).
*   **Role:** The interface for Human-Agent collaboration.
*   **Function:**
    *   Receives raw intelligence from Agents (Perplexity/Comet).
    *   Formats data into "Action Cards" (Twitter Drafts, Reddit Replies).
    *   **New:** Acts as the "Feedback Monitor" where Failures are logged.

### B. The Protocols (The "Agents")
*   **What they are:** Markdown workflows (`comet_trend_protocol.md`, `comet_inbox_protocol.md`).
*   **Role:** The instructions for the Browser Agent (Comet).
*   **Adaptive Logic:**
    *   **Try:** Attempt the standard path (e.g., "Check Reddit Inbox").
    *   **Catch:** If blocked (Auth, Selector fail), do NOT crash.
    *   **Log:** Report the failure to the Dashboard (`[FAILURE] Context: X`).
    *   **Fall Back:** Execute alternative path (e.g., "Check Email Notification" instead).

### C. The Nucleus (The "Brain")
*   **What it is:** The backend Python system (`nucleus/`, `server.py`).
*   **Role:** The enforcer and orchestrator.
*   **Future Function (Phase 12):**
    *   **Daemon:** Runs silently in the background (`launchd`).
    *   **Watcher:** Monitors `marketing_log.md`.
    *   **Healer:** If it sees a `[FAILURE]` log, it can trigger a specific recovery script or alert the user.

---

## 2. The Plan Forward (Roadmap)

### Step 1: Document & Harden (Current Phase)
*   **Goal:** Ensure the "Front-End" (Dashboard) and "Protocols" are robust enough to handle errors without stopping.
*   **Action:**
    *   Create `docs/marketing/ADAPTIVE_PROTOCOLS.md` (The "Rulebook").
    *   Update protocols with "If/Then" fallback logic.
    *   Define the "Failure Dictionary" (Standard error codes for agents).

### Step 2: Nucleus Integration (Next Phase)
*   **Goal:** Move from "Manual Trigger" (`Marketing_Morning_Routine.command`) to "Nucleus Management".
*   **Action:**
    *   Update `server.py` to parse `[FAILURE]` tags actively.
    *   Create simple "Healer" triggers (e.g., "If `Auth Fail`, send System Notification to User").

### Step 3: Full Autonomy (Future)
*   **Goal:** Zero-Click "Ghost Mode".
*   **Action:** Headless browser scripts running via `cron`, feeding the Dashboard while you sleep.

---

## 3. Data Flow Diagram

```mermaid
graph TD
    User((User)) -->|Launches| Dashboard[Marketing Dashboard]
    
    subgraph "External World"
        Web[Perplexity / Reddit / X]
    end
    
    subgraph "The Agents"
        Comet[Comet (Browser Agent)]
        Comet -->|Scans| Web
        Comet -- Success -->|POST Data| Server[Ingest Server :9999]
        Comet -- Failure -->|POST Error| Server
    end
    
    subgraph "The Brain"
        Server -->|Appends| Log[marketing_log.md]
        Log -->|Reads| Dashboard
        Nucleus[Nucleus Core] -.->|Watches| Log
    end
    
    Dashboard -->|Displays Actions| User
```
