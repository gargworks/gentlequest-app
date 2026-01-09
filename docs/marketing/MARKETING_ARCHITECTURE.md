# 🏗️ Marketing Autopilot Architecture 2.0
**Philosophy:** "The Growth Machine" (Automated, Frictionless, Daily)
**Methodology:** Double Diamond (Diverge/Converge) + Critic Governance

---

## 🔌 Technical Sync Protocol ("The Git Pulse")
**The Sync Mechanism:**
The "Brain" and "Body" are decoupled. They communicate via the File System, synced by Git.

### 1. The Pulse (How Data Moves)
*   **Nucleus (Brain):** Defines Strategy -> Commits to Repo.
*   **Comet (Body):** Pulls Repo -> Executes -> Writes Log -> Commits to Repo.
*   **Loop:** `Pull -> Act -> Push`.

### 2. State Files (The Synapse)
*   `docs/marketing/BRAND_STRATEGY.md` (Read-Only for Comet)
*   `docs/marketing/marketing_log.md` (Append-Only for Comet)

### 3. Execution Reality (Browser vs API)
*   **Scenario A (Captive Browser):** If utilizing a "Human-in-the-Loop" browser session:
    *   Comet navigates to X/Reddit.
    *   Comet performs action.
    *   Comet commits the Log.
*   **Scenario B (Headless):** (Not currently active due to Auth risks).

---

## 🧠 The Central Brain (State)
The system relies on **Single Source of Truth (SSOT)** documents. Agents must read these before acting.

1.  **Constituion (Voice & Rules):** `docs/marketing/BRAND_STRATEGY.md`
    *   *Governs:* Tone ("Gentle"), Privacy (No Names), positioning.
2.  ** Reddit Strategy (Manual Safety):** `docs/GENTLEQUEST_REDDIT_GROWTH_STRATEGY.md`
    *   *Governs:* 10:1 Ratio, Crisis Protocols, Subreddit Shortlist.
3.  **Memory (Logs):** `docs/marketing/marketing_log.md`
    *   *Governs:* What we did, what worked, what failed.

---

## ⚙️ The 3 Engines

### 1. The Scout (Diverge) 🔭
**Agent:** Perplexity / Comet
**Goal:** Gather raw intelligence.
*   **Triggers:** Daily scheduled run.
*   **Actions:**
    *   Scan Twitter Trends (#ADHD, #Burnout).
    *   Scan Subreddit mood (What are people complaining about today?).
    *   Scan News (Is there a relevant "Mental Health" story?).
*   **Output:** `Trend Report` (3 potential angles).

### 2. The Maker (Converge) ✍️
**Agent:** Comet
**Goal:** Turn intelligence into content.
*   **Twitter (Low Risk):**
    *   Selects best angle.
    *   Drafts tweet.
    *   **Mode:** *Automated Execution* (after Critic check).
*   **Reddit (High Risk):**
    *   Selects "Safe" subreddit.
    *   Drafts "Smallest Safe Action" (Comment).
    *   **Mode:** *Manual Handoff* (Prepares draft for Human click).

### 3. The Judge (Governance) ⚖️
**Agent:** Critic / Nucleus
**Goal:** Prevent Brand/Safety violations.
*   **Triggers:** Pre-Post (Twitter) or Weekly Audit (Reddit).
*   **Checks:**
    *   "Does this sound like 'Hustle Culture'?" (If yes -> Reject).
    *   "Is this a Crisis thread?" (If yes -> Abort).
    *   "Does this reveal the Founder's identity?" (If yes -> Reject).

---

## 🔄 The Daily Loop (Workflow)
Defined in `.agent/workflows/marketing_autopilot.md`.

1.  **Wake Up:** Comet initializes + **GIT PULL**.
2.  **Ingest:** Reads `BRAND_STRATEGY` + `marketing_log`.
3.  **Scout:** Finds the "Angle of the Day".
4.  **Judge:** Self-critique against Constitution.
5.  **Execute:**
    *   Post Tweet (Immediate).
    *   Log Action.
    *   **GIT COMMIT + PUSH**.
6.  **Sleep:** Until next cycle.

---

## 🔁 The Weekly Sync (Reconciliation)
**Owner:** Nucleus (Antigravity)
**Frequency:** Sunday Evening

1.  **Audit:** Read `marketing_log` vs Actual Platform History.
2.  **Synthesize:** Update `BRAND_STRATEGY` with new learnings.
3.  **Refill:** Update `LAUNCH_CONTENT_PACK` with new evergreen basics.

---
**Status:** Live
**Maintainer:** Lead Systems Architect
