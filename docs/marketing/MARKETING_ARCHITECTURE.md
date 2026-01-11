# 🏗️ Marketing Autopilot Architecture 2.0 (The Sensor Network)

**Philosophy:** "The Growth Machine" (Automated, Frictionless, Daily)
**Status:** Live (v2.1 - Hybrid Agentic Model)
**Maintainer:** Lead Systems Architect

---

## 🗺️ The System Flow (How it Works)

```mermaid
graph TD
    subgraph "Input: Automated Intelligence"
        A[Comet Browser] -->|Trend Protocol| B(Perplexity.ai)
        A -->|Inbox Protocol| C(Social Notifications)
        B -->|Auto-Post Data| E[Ingest Server (Port 9999)]
        C -->|Auto-Post Data| E
        E -->|Write to Disk| D[Marketing Log]
    end

    subgraph "The Hub"
        D -->|Parsed Live| F[Interactive Dashboard]
    end

    subgraph "Output: Rapid Execution"
        F -->|Click 'Post'| G(TwitterIntent/RedditSubmit)
        G -->|Action| H(The World)
    end
```

---

## ⚙️ The 3 Engines

### 1. The Trend Scout (Outbound) 🔭
*   **Agent:** Comet (The Browser)
*   **Tool:** Perplexity Web Interface (`comet_trend_protocol.md`)
*   **Goal:** Find *new* things to talk about.
*   **Mechanism:** Comet visits `perplexity.ai` (Free/Pro) and types the Prompt.
*   **Output:** "Trend Alert" -> Marketing Log.

### 2. The Inbox Listener (Inbound) 👂
*   **Agent:** Comet (The Browser)
*   **Tool:** Direct Browser Navigation (`comet_inbox_protocol.md`)
*   **Goal:** Hear who is talking to *us* (Engagement).
*   **Mechanism:** Comet logs in (using your session) and checks notifications.
*   **Output:** "Reply Needed" -> Marketing Log.

### 3. The Dashboard (Command Center) 🕹️
*   **Tool:** Local HTML App (`marketing-dashboard/index.html`)
*   **Goal:** Eliminate friction.
*   **Mechanism:** Reads the Log -> Auto-generates "Click-to-Post" buttons.
*   **Output:** Pre-filled Twitter/Reddit tabs.

---

## 🧪 The "Dev -> UAT -> Prod" Pipeline

To ensure reliability, we follow this testing lifecycle:

1.  **Dev (Simulation):** We inject mock data into the log to verify the Dashboard renders correctly.
2.  **UAT (User Acceptance):** You run the Protocols with Comet (Real Data) and verify the dashboard updates.
3.  **Prod (Daily Habit):** You perform the loop daily as part of your morning routine.

---

## ⚠️ Known Limitations (The "Honest" Section)

### 1. The Data Bridge Gap (Browser -> Disk)
*   **Issue:** Comet (Browser Agent) sees the data but may not have permission to write directly to `marketing_log.md` on your local disk.
*   **Workaround:** The Protocol asks Comet to *generate* the Markdown row. The User (You) may need to "Copy Code Block" and paste it into the file manually.
*   **Fix (Future):** Give Comet filesystem access or use the Python API script (Cost tradeoff).

### 2. The Echo Chamber Risk
*   **Issue:** Perplexity scans the same sources (Reddit/Twitter) daily. It may repetitively surface "Burnout" or "AI Anxiety" every single day.
*   **Risk:** Editorial fatigue.
*   **Fix (Future):** Implement "Topic Rotation" logic in the Brain (e.g., "Ignore 'Burnout' for 3 days").

### 3. Analytics Blindness
*   **Issue:** We track *Outputs* (Posts) but not *Outcomes* (Clicks/Traffic).
*   **Risk:** We don't know which posts actually drive users to the app.
*   **Fix (Future):** Implement UTM tags (`?utm_source=reddit`) in the Dashboard's link generator.
