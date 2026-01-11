# Marketing Dashboard (Front-End) Roadmap

## **Current Status: v1.0 (The "Portal")**
*   **Core Feature:** Ingests raw text, formats to Markdown, appends to Log.
*   **UI:** Static HTML/JS.
*   **Server:** Python `http.server`.

## **Planned Upgrade: v2.0 (The "Controller")**

### 1. Error Visualization (Self-Healing)
*   **Feature:** "System Health" Status Bar.
*   **Logic:**
    *   If `marketing_log.md` contains `[FAILURE]` tags in the last 24h -> Show "⚠️ Degradation".
    *   If `[FAILURE]` count > 5 -> Show "🔴 Critical".
*   **Action:** Click status to see "Error Log" (filtered view of failures).

### 2. Action Buttons (Enhanced)
*   **Feature:** "One-Click Retry".
*   **Logic:** If a log entry is a `[FAILURE]`, show a "Retry" button that re-launches the specific Protocol (requires Nucleus).

### 3. Smart Sorting
*   **Feature:** "High Priority" View.
*   **Logic:** Float entries with words like "Urgent", "Crisis", or "Viral" to the top.

## **Validation Strategy**
*   **Mock Errors:** Inject fake failure logs to test the UI's "Error Mode".
*   **User Test:** Verify that "Error Mode" is clear and actionable (not just scary).
