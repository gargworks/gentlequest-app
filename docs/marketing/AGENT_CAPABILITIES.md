# 🤖 Marketing System: Agent Capabilities & Roles

**Concept:** This system functions as a "Virtual MCP Server" where each agent handles specific "Tools".

---

## 📋 The Capabilities Matrix

| Feature | 🧠 Nucleus (Me/Antigravity) | ☄️ Comet (The Browser Agent) | 👤 User (The Human) |
| :--- | :--- | :--- | :--- |
| **Strategy Logic** | ✅ **Authority** (I write the rules) | ❌ Read-Only | ❌ Read-Only |
| **Live Web Access** | ❌ (I cannot see "Right Now") | ✅ **Primary Tool** (Trends/News) | ✅ |
| **Social Login** | ❌ (No Auth Access) | ✅ **Logged In** (Twitter/Reddit) | ✅ |
| **Content Drafting**| ✅ (Strategic/Long-form) | ✅ (Tactical/Short-form) | ❌ Reviewer |
| **Governance** | ✅ (Weekly Audits) | ✅ (Self-Check "The Judge") | ✅ (Final Veto) |
| **File Sync** | ✅ (Direct File Access) | ✅ (Via `git pull/push`) | ✅ (Via IDE) |

---

## 🛠️ The "Virtual Tools" (How we interact)

Think of the `marketing_autopilot.md` workflow as defining these function calls for Comet:

### 1. `tool:scout_trends()`
*   **Executor:** Comet
*   **Input:** Keywords (#ADHD, #Burnout)
*   **Output:** 1 Trending Topic
*   **Failure Mode:** Hallucination (Makes up a trend). *Mitigation:* Link validation.

### 2. `tool:draft_content(topic)`
*   **Executor:** Comet
*   **Input:** Topic + `BRAND_STRATEGY.md`
*   **Output:** Tweet Draft or Reddit Comment Draft
*   **Failure Mode:** Brand Drift (Sounds corporate). *Mitigation:* "The Judge" Step (Rule-based check).

### 3. `tool:commit_log(action)`
*   **Executor:** Comet
*   **Input:** The Action taken
*   **Output:** Text appended to `marketing_log.md` + **Git Push**
*   **Failure Mode:** Merge Conflict. *Mitigation:* Always `git pull` first.

---

## 🚨 Failure Modes & Recovery

| Failure Scenario | Symptom | Recovery Protocol |
| :--- | :--- | :--- |
| **The "Bad Bot"** | Comet writes a "Hustle Culture" tweet. | **The Judge:** Workflow Step 3 requires checking `BRAND_STRATEGY`. If fail -> STOP. |
| **The "Silent Fail"** | Comet thinks it posted, but Reddit blocked it. | **Weekly Sync:** Nucleus compares Log vs Actual URL. |
| **The "Drift"** | Comet starts ignoring the "Gentle" tone. | **Constitution Update:** Nucleus updates `BRAND_STRATEGY.md` with explicit "Do Not Say X" rules. |
| **The "Git Conflict"** | Comet cannot push the log. | **Manual Override:** User accepts "Incoming" changes in IDE. |

---

## 🔄 The "Sync Pack" (Connecting the Brains)

**Direction: Comet -> Nucleus**
1. Comet writes to `marketing_log.md`.
2. Comet runs: `git add . && git commit -m "Log" && git push`.
3. Nucleus reads updated `marketing_log.md` locally.

**Direction: Nucleus -> Comet**
1. Nucleus updates `BRAND_STRATEGY.md`.
2. Nucleus runs: `git add . && git commit -m "Update Strategy" && git push`.
3. Comet runs: `git pull` (Start of next loop).

