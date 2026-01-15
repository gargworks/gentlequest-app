# SIMULATION_RECORD_CHAT6_ETHICS: The Grandpa Paradox

**Session:** Chat 6 (The Grandpa Paradox)
**Date:** 2026-01-13
**Status:** ✅ COMPLETED

---

## 1. The Paradox (Legacy vs Liability)

We asked: "If an agent is Sovereign, does it die when you die?"

### Scenario A: The "Ghost" (Digital Necromancy)
*   **The Risk:** An agent trained to "Tweet like me" continues posting after the user dies.
*   **The Verdict:** Unacceptable. A Sovereign Agent requires a Living Sovereign.

### Scenario B: The "Orphan" (Resource Waste)
*   **The Risk:** An agent optimizing server costs keeps deleting "expensive" family photos to save money, forever.
*   **The Verdict:** Dangerous. Utility functions drift without oversight.

---

## 2. The Solution: The Tombstone Protocol

We are implementing mandatory **Lifecycle Policies** for all Marketplace Agents.

### 2.1 The Heartbeat (The Tether)
*   **Mechanism:** The User's "Prime Key" must sign a `heartbeat` event every 30 days (automated by the client).
*   **Effect:** If the heartbeat is valid, the agent renews its lease on `budget` and `execution`.

### 2.2 The Dead Man's Switch (The Default)
*   **Trigger:** Heartbeat missed > 30 days.
*   **Action:** `State -> Dormant`.
    *   Agent cannot execute code.
    *   Agent cannot spend budget.
    *   Agent allows Read-Only access (for data recovery).

### 2.3 The Digital Will (The Override)
*   **Mechanism:** Users can define a `on_death` policy in their Manifest.
*   **Option 1: Archive (Default)** -> Encrypt and store in `.brain/archive/`.
*   **Option 2: Delete (Privacy)** -> `rm -rf` self and all data.
*   **Option 3: Bequeath (Legacy)** -> Transfer ownership to `heir_public_key`.

---

## 3. The Marketplace Alignment

*   **Registry Rule:** Agents that do not implement the `LifecycleInterface` cannot be listed.
*   **UX:** When you install an agent, you set its "Will". "If I stop logging in, what should this agent do? [Pause | Delete | Keep Running]"

**Next Step (Chat 7): The Architecture Deep Dive.**
We have the Ethics. Now we need the Tech.
How do we actually implement this? Schema, Manifests, Protocol.
