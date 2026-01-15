# SIMULATION_RECORD_CHAT5_SECURITY: The Dark Forest Audit

**Session:** Chat 5 (The Dark Forest Audit)
**Date:** 2026-01-13
**Status:** ✅ COMPLETED

---

## 1. The Threat Model (The Dark Forest)

We assume the network is hostile. We assume:
1.  **The Supply Chain is Compromised:** Trusted agents will be sold to bad actors.
2.  **The Context is Radioactive:** User data (SSH keys, notes) is highly sensitive.
3.  **The Prompt is Jailbroken:** Agent instructions *will* be overridden by prompt injection.

---

## 2. The Defenses (Zero Trust)

### Defense A: Segregation of Duties (The "Air Gap")
*   **The Rule:** By default, an agent can have `filesystem` OR `network`, but **NEVER BOTH**.
*   **The Logic:**
    *   `filesystem` only: Can read secrets, but can't exfiltrate them.
    *   `network` only: Can call APIs, but can't read secrets.
*   **The Exception:** "Bridge Agents" (e.g., Backups) require explicit, high-friction `Warning: FULL TRUST` approval.

### Defense B: Immutable Versioning (The "Hash Lock")
*   **The Rule:** We never `install @latest`. We `install @commit-hash`.
*   **The Logic:** A "Supply Chain Attack" works by pushing a malicious update to the *next* version. By pinning the hash, `brain update` becomes a manual, rigorous opt-in. We **DISABLE AUTO-UPDATE**.

### Defense C: The BudgetGuard (The "Wallet")
*   **The Rule:** Every installed agent starts with **$0.00** budget.
*   **The Logic:** A "Trojan Horse" that constantly runs background tasks needs tokens. If the budget is $0, it suffocates. The user must explicitly strictly `grant budget` ($1.00).

---

## 3. The Implementation Constraints

1.  **Transport Hardening:** Use `stdio` over `http` where possible to prevent port scanning.
2.  **Manifest Verification:** The `manifist.json` must be signed by the `public_key` in the `TrustProfile`.
3.  **Kill Switch:** `brain kill <agent>` resolves to `SIGKILL` immediately. No `SIGTERM`. We do not ask politely.

---

## 4. The Verdict

We have defined a **"Paranoid by Default"** architecture.
Convenience is sacrificed for Safety. This aligns with the "Sovereignty" strategy.

**Next Step (Chat 6): The Grandpa Paradox.**
Security protects the user *today*. Ethics protects the user *tomorrow*.
What happens if the user creates an agent that outlives them?
**Ethics & Legacy.**
