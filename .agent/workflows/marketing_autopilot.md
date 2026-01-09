---
description: Daily Marketing Autopilot & Weekly Strategy Sync
---

# 🛸 Marketing Autopilot (Architecture 2.0)
**Objective:** Automate daily growth actions via the Scout-Maker-Judge loop.
**Architecture:** Defined in `docs/marketing/MARKETING_ARCHITECTURE.md`.

## 🔄 The Sync Protocol (Data Flow)
1.  **Read-Only Context:** `docs/marketing/BRAND_STRATEGY.md` (SSOT).
2.  **Write-Only Log:** `docs/marketing/marketing_log.md` (Memory).
3.  **Governance:** Weekly reviews by Nucleus.

---

## ⚡️ Daily Loop (The Execution Script)
**Frequency:** Every Morning
**Agent:** Comet

### Phase 1: The Scout (Diverge) 🔭
1.  **Read Context:**
    *   `docs/marketing/BRAND_STRATEGY.md` (Constitution).
    *   `docs/marketing/LAUNCH_CONTENT_PACK.md` (Queue).
2.  **Scan Trends:**
    *   What is trending in #ADHD, #Burnout, #MentalHealth?
    *   Select ONE high-relevance topic.

### Phase 2: The Judge (Governance Check) ⚖️
3.  **Self-Critique Strategy:**
    *   *Check:* Does this topic align with "Gentle Productivity"?
    *   *Check:* Is this a "Crisis" topic? (If yes -> STOP & LOG "Aborted due to safety").
    *   *Check:* for Reddit: Is the tone truly "peer-to-peer" and NOT "brand-to-customer"?

### Phase 3: The Maker (Converge & Execute) ✍️
4.  **Twitter (Automated Draft):**
    *   Draft a tweet using Brand Voice (No "I").
    *   *Constraint:* Must be < 280 chars.
    *   **Action:** Post to Twitter (or Queue if confidence < 90%).
5.  **Reddit (Strict Manual Prep):**
    *   **CRITICAL:** ZERO AUTOMATION for Reddit posting.
    *   *Action:* Draft the "Smallest Safe Action" (Comment).
    *   *Output:* "Draft for Review: [Text]" -> Log to `marketing_log.md`.
    *   *Human Trigger:* Waiting for user to copy-paste.

### Phase 4: Logging & Sync 📝
6.  **Update Memory:**
    *   Append activity to `marketing_log.md`.
7.  **Sync:**
    *   Run `git pull` (before starting).
    *   Run `git add docs/marketing/marketing_log.md && git commit -m "Comet: Daily Log" && git push` (after finishing).

---

## 🧠 Weekly Sync (The Governance Job)
**Frequency:** Every Sunday Evening
**Agent:** Nucleus

1.  **Audit:** Compare `marketing_log.md` vs actual platform stats.
2.  **Update:** Refine `docs/marketing/BRAND_STRATEGY.md`.
3.  **Refill:** Add new evergreen ideas to `docs/marketing/LAUNCH_CONTENT_PACK.md`.

---

## 🚀 How to Trigger
*   **Daily:** `agent run .agent/workflows/marketing_autopilot.md --step daily`
*   **Weekly:** `agent run .agent/workflows/marketing_autopilot.md --step weekly`
