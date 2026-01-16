# Render Pipeline Rescue Protocol (The "Ninja Move") 🥷

**Version:** 1.0.0
**Last Updated:** 2026-01-15
**Status:** ACTIVE

## 🚨 The Emergency Scenario
You have exhausted your **Render Free Tier Pipeline Minutes** (500/500 mins used).
- **Symptom:** Any attempt to deploy code or update Environment Variables results in a `Build Blocked` error.
- **Consequence:** You are locked out of deploying critical configuration fixes (e.g., rotating a database password).

## 🛡️ The Solution: "The Ninja Move"
We bypass the build pipeline by forcing Render to strictly re-deploy a **cached Docker image** (which costs 0 build minutes) while applying the **latest Environment Variables**.

### ⚠️ Constraints (The "Code Freeze")
*   **Restoration Only:** You cannot deploy *new* code, typos fixes, or static pages.
*   **Old Code, New Config:** You will be running the *previous* version of your application, connected to the *new* infrastructure/config.
*   **Duration:** This state persists until billing resets (1st of the month) or you purchase minutes.

---

## 🛠️ Execution Steps

### Phase 1: Stop the Bleeding
1.  Go to **Render Dashboard** -> **Settings**.
2.  Find **Auto Deploy**.
3.  Set to **No** (Toggle Off).
    *   *Reason: Prevents accidental git pushes from triggering more "Build Blocked" emails/alerts.*

### Phase 2: The Setup (Staging the Config)
1.  Go to **Environment**.
2.  Update your target variable (e.g., `DATABASE_URL`).
3.  Click **Save Changes**.
    *   *Result: Render will try to deploy and FAIL (Build Blocked). This is EXPECTED. Your config is now saved in the database, just not active.*

### Phase 3: The Ninja Strike (Time Travel)
1.  Go to the **Deploys** tab.
2.  Scroll down to find the **last Successful (Green) Deploy**.
3.  Click the **... (Menu)** or the **Deploy** button on that row.
4.  Select **Rollback to this deploy**.
    *   *Mechanism: Render sees "Rollback" -> Skips Build -> Pulls Cached Image -> Injects CURRENT (Saved) Env Vars -> Boots Container.*

### Phase 4: Verification
1.  Watch the logs. You should see `Deploying...` followed by `Live`.
2.  Verify functionality (e.g., `/api/health`).

---

## 📝 Example: Database Rotation (Jan 15, 2026)
*   **Issue:** `gentlequest-db` expired. New DB `gentlequest-db-jan` created.
*   **Blocker:** 504/500 pipeline minutes.
*   **Action:**
    1.  Updated `DATABASE_URL` to `gentlequest-db-jan` internal URL.
    2.  Rolled back to commit `f75898e` (Last green build).
*   **Result:** Service `GentleQuest` came online with new DB, bypassing the paywall.
