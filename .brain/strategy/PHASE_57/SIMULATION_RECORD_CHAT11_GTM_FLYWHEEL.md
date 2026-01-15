# SIMULATION_RECORD_CHAT11_GTM_FLYWHEEL: The Flywheel

**Session:** Chat 11 (GTM Loop 4: The Flywheel)
**Date:** 2026-01-13
**Status:** ✅ COMPLETED

---

## 1. The Framework (Reforge Growth Loops)

Funnels (Acquisition -> Retention) are linear and expensive.
Flywheels (Usage -> Acquisition) are circular and compounding.

### The "Utility Loop" (Collaborative Automation)
We designed the core loop that drives internal team growth.

1.  **Trigger (Pain):** "I need to run the complex DB migration script" (Fear of breaking prod).
2.  **Action (Usage):** Run `brain run @team/db-migrate`.
3.  **Reward (Value):** It works safely. The "TrustProfile" verified the permissions.
4.  **Investment (Re-Contribution):**
    *   The user notices a missing flag.
    *   They edit the agent: `brain edit @team/db-migrate`.
    *   They push the improvement: `brain publish`.
5.  **Output (Compounding):** The tool is now 2x better for the *next* engineer, increasing the likelihood they use it.

---

## 2. The "Network Loop" (Cross-Team Infection)

How does it jump from "DevOps Team" to "Backend Team"?

1.  **Trigger:** Backend Dev asks: "How do I reset my staging DB?"
2.  **Action:** DevOps Dev says: "Just install our agent: `brain install @devops/staging-reset`."
3.  **Investment:** Backend Dev installs Nucleus to get the tool.
4.  **Loop:** Backend Dev realizes they can build `@backend/api-test` for themselves.

---

## 3. The Implementation Requirement

To make these flywheels spin, we need **Zero Friction Contribution**.
*   **"Edit in Place":** `brain edit <agent>` must open VS Code, allow a fix, and `brain publish` must update the hash in the Registry.
*   **Speed:** The loop from "Finding a Bug" to "Fixing the Agent" must be < 30 seconds.

**Next Step (Chat 12): GTM Consolidation.**
We have the Beachhead (Chasm), the Supply (Atomic), and the Growth (Flywheel).
We will now synthesize these 5 loops into a **Unified Launch Vector**.
