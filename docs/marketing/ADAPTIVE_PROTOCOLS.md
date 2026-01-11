# Adaptive Protocols: The "Try-Catch-Log" Standard

## **Philosophy**
Autonomous agents (like Comet) operate in a brittle environment (the live web). Elements move, auth expires, and sites go down.
**A robust agent does not crash; it logs the failure and tries a different path.**

---

## **The Protocol Loop**

1.  **TRY (Primary Path):** Attempt the optimal action (e.g., scrape specific div).
2.  **CATCH (Constraint):** Identify failure constraints (e.g., "Element not found", "Login required").
3.  **LOG (Feedback):** Report the failure to the "Feedback Loop" (`marketing_log.md` via Server).
4.  **FALLBACK (Secondary Path):** Execute the safety net (e.g., global search).

---

## **Standard Failure Codes**

When logging a failure, use these standard tags so the Nucleus can parse them later.

| Tag | Meaning | Example Scenario |
| :--- | :--- | :--- |
| `[AUTH_LOCKED]` | Agent cannot access data due to login wall. | "Redirected to /login" |
| `[SELECTOR_MISSING]` | The target UI element was not found. | "Did not find .inbox-badge" |
| `[TIMEOUT]` | The page took too long or hung. | "Spinner stuck for 30s" |
| `[BLOCKED]` | Bot detection or 403 Forbidden. | "Cloudflare verify screen" |

---

## **Logging Instruction (For Agents)**

If a step fails, **DO NOT STOP**.
Navigate to `http://localhost:9999` and ingest a Log Entry:

**Type:** `System Failure`
**Content:**
```
[FAILURE] [SELECTOR_MISSING]
Target: Reddit Inbox
Action: Skipped harvest.
Timestamp: <NOW>
```

---

## **Recovery Triggers (Nucleus)**

*   **IF** `[AUTH_LOCKED]` **THEN** -> Alert User "Please login to Reddit".
*   **IF** `[SELECTOR_MISSING]` **THEN** -> Alert Dev "Update CSS Selectors".
