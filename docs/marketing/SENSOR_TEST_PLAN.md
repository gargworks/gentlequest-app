# 🧪 Sensor Network Test Plan

**Objective:** Verify the "Comet -> Log -> Dashboard" flow works in all 3 environments.

## Phase 1: Dev Environment (Simulation) 🤖
*Executed by Antigravity (Me)*

### 1. Trend Simulation
*   **Action:** Inject simulated "Perplexity Response" into `marketing_log.md`.
*   **Verification:**
    *   [ ] Open Dashboard.
    *   [ ] Check for "Trend 📡" row.
    *   [ ] Verify "Draft Response" button works.

### 2. Inbox Simulation
*   **Action:** Inject simulated "IndieHackers Reply" into `marketing_log.md`.
*   **Verification:**
    *   [ ] Open Dashboard.
    *   [ ] Check for "Inbox 📬" row (Green Card).
    *   [ ] Verify "Open Thread" button links deeply.

---

## Phase 2: UAT Environment (User + Comet) 👤
*Executed by You (with Comet Browser)*

### 1. Execute Trend Protocol
1.  Open **Comet**.
2.  Paste the **Trend Prompt** from `comet_trend_protocol.md`.
3.  Go to `perplexity.ai`.
4.  **Instructions for Comet:** "Go to `http://localhost:9999`, paste finding, and click Save."
5.  **Check:** Does the Dashboard card appear automatically?

### 2. Execute Inbox Protocol
1.  Open **Comet**.
2.  Paste the **Inbox Instruction** from `comet_inbox_protocol.md`.
3.  **Instructions for Comet:** "Go to `http://localhost:9999`, paste findings, and click Save."
4.  **Check:** Does the Dashboard turn it into a "Reply Station"?

---

## Phase 3: Prod Environment (The Habit) 🚀
*Daily Routine*

1.  **Morning Coffee:**
    *   Open Comet.
    *   Run Trend Protocol (2 mins).
    *   Run Inbox Protocol (1 min).
2.  **Action:**
    *   Open Dashboard (`./Marketing_Dashboard.command`).
    *   Click "Draft" on the best trend.
    *   Click "Reply" on urgent messages.
3.  **Sync:**
    *   `git commit -am "marketing: daily pulse"`
