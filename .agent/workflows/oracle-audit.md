---
description: Run the Recursive Anti-Hallucination Audit (Self-Healing)
---

This workflow executes the "Skeptical Auditor" and the "Surgeon" to detect and fix hallucinations.

1. Execute the Audit Loop (Auto-Heal Enabled)
   - If the user provided a specific topic/proposition, pass it as the first argument.
   - If no topic was provided, run without arguments (defaults to System Audit).

2. ./scripts/audit_oracle.sh "<PROPOSITION>" --auto-heal

3. The results will be saved to `.brain/memory/ORACLE_LEDGER.md` and `.brain/backlog/fixes.json`.
