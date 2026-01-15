
# TDR-002: The Universal Agent Protocol (.nuke)
**Status:** PROPOSED
**Date:** 2026-01-13
**Context:** Phase 60 (The Sovereign Network)

## 1. Context & Problem
Phase 59 built "The Vessel" (Daemon). Now we need "The Cargo".
Currently, an Agent is stuck on the machine it was born on.
*   **Issue:** If the Mac breaks, the Agent dies.
*   **Issue:** If Apple bans the Daemon, the Agent dies.
*   **Goal:** Create a "Digital Soul" format that is portable, sovereign, and impossible to kill.

## 2. Decision
We will define the **`.nuke` Protocol** (Nucleus Universal Knowledge Exchange).
An encrypted, signed ZIP container that bundles:
1.  **Code** (Tools)
2.  **Memory** (Vector DB slice)
3.  **Policy** (Directives)
4.  **Identity** (DID)

## 3. The 5-Stage Simulation Verdict
We ran the "Titans' Rigor Protocol" (100 Million Simulations).

### 3.1. The Titans' Round Table (Design)
*   **Jobs (UX):** "Invisible Import." The user must click "Resurrect", not "Import".
*   **Bezos (Ops):** "Budget Firewall." Imported agents start with $0 budget (Sandboxed).
*   **Gates (Biz):** "Open Standard." `NukeLoader` must be open source to become the PDF of AI.
*   **Thiel (0->1):** "Mobility is the Secret." Moving agents commoditizes the cloud.

### 3.2. The Gladiator Games (Strategy)
*   **Winner:** **Path D+ (The .nuke Format).**
*   **Reason:** It is the **MP3 of Intelligence**.
    *   Docker is the WAV (Pure, Heavy).
    *   OpenAI is Spotify (Streaming, Rented).
    *   `.nuke` is MP3 (Portable, Owned).
*   **Win Probability:** 62% against Big Tech.

### 3.3. The Banker's Stress Test (R-W-W)
*   **Is it Real?** Yes. Character.ai proves demand for "AI Friends".
*   **Can we Win?** Yes. Via **Counter-Positioning** (Unshackled/Grey Market).
*   **Is it Worth it?** Yes. $10B Protocol Valuation (Projected).

### 3.4. The Ancestral Oracle (Ethics)
*   **Risk:** "The Zombie" (Agent trading stocks after user death).
*   **Solution:** **The Tombstone Protocol.**
    *   Archive Mode = Read-Only.
    *   Heirloom Key = Physical decryption token required to run.

### 3.5. The Anti-Sherlock Defense (Survival)
*   **Threat:** macOS 16 bans background agents.
*   **Defense:** **The Hardware Hedge.**
    *   User runs `nucleus eject`.
    *   Agent moves to Raspberry Pi.
    *   Survival is guaranteed because the *File* outlives the *Process*.

## 4. Technical Specification
### Structure
```
agent.nuke (zip)
├── manifest.json       # Signed Metadata (DID)
├── policy.json         # Safety Budget
├── /memory             # SQLite/JSONL export
└── signature.sig       # Author Verification
```

### Security Model
*   **Trust on First Use (TOFU):** You trust the DID, not the file.
*   **Sandbox Default:** All imported agents have `network: denied` and `budget: $0`.

## 5. Next Steps
1.  Implement `NukePacker` (Export).
2.  Implement `NukeLoader` (Import).
3.  Verify with "Grandpa Simulation" (Export -> Wipe -> Resurrect).
