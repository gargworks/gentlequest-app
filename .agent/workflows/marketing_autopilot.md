---
description: Daily Marketing Autopilot & Weekly Strategy Sync
---
# Marketing Autopilot & Strategy Sync 🔄

## ⏰ Daily Routine (The Loop)
**Goal:** Keep the "Consultant" (Browser Agent) running and the Dashboard fresh.
**Tools:** `scripts/launch_marketing_agent.py`

### 1. Morning: The Listener 👂
*   **Run:** `python3 scripts/launch_marketing_agent.py listener`
*   **Action:** Script copies the prompt & opens Perplexity. You just Paste.
*   **Result:** Agent finds replies/notifications. You paste findings to Dashboard.

### 2. Noon: The Publisher ✍️
*   **Run:** `python3 scripts/launch_marketing_agent.py publisher`
*   **Action:** Script copies Drafts & opens Perplexity. You just Paste.
*   **Result:** Agent posts the content. You click "Mark Posted" in Dashboard.

---

## 📅 Weekly Ritual (The Strategy Sync)
**Goal:** Use the agent's "Consultant Reports" to refine `strategy.md`.
**When:** Sunday Night / Monday Morning.

### 1. Execute the Sync Code 🧠
*   **Run:** `python3 scripts/auto_strategy_sync.py`
*   **Action:** The Brain analyzes `marketing_log.md` and *rewrites* `strategy.md`.
*   **Result:** You get a new Strategy file with "Recent Insights" and "Drafting Angles".

### 2. Verify & Commit 💾
*   `git diff docs/marketing/strategy.md` to see what changed.
*   If good, commit it.


### 4. Workflow Evolution (Meta-Optimization) 🧬
*   Did the Agent suggest a better prompt? (Check "META-FEEDBACK" in logs).
*   **Action:** Update `marketing_autopilot_cheatsheet.md` with the new prompts.
*   **Action:** If Agent reported a UI failure, create a task to fix `index.html`.

