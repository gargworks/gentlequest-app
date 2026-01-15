# Implementation Plan - Phase 66: The Reflexion Loop

**Goal:** Close the loop between Diagnosis (The Auditor) and Improvement (The Kernel). Enable the Oracle to self-heal based on Truth Audit findings.

## User Review Required
> [!WARNING]
> This enables **Automated Code Editing** based on LLM feedback.
> While the protocol enforces isolation (Auditor vs Surgeon), there is a non-zero risk of regression.
> The Surgeon operates on a "Best Effort" basis using the `brain_fix_code` tool logic.

## Proposed Changes

### 1. Diagnosis (The Auditor)
#### [MODIFY] [scripts/gladiator_simulator.py](file:///Users/lokeshgarg/ai-mvp-backend/scripts/gladiator_simulator.py)
*   **Parsing Logic:** Extract the content after `5. Refinement:` from the LLM response.
*   **Queueing:** If Refinement exists, save it to a structured file: `.brain/backlog/pending_fixes.md` (or JSON).
*   **Metadata:** Include Confidence Score. Only queue fixes if Confidence > 90.

### 2. Improvement (The Surgeon)
#### [NEW] [scripts/oracle_reflexion.py](file:///Users/lokeshgarg/ai-mvp-backend/scripts/oracle_reflexion.py)
*   **Role:** The Surgeon.
*   **Input:** Reads `.brain/backlog/pending_fixes.md`.
*   **Action:** Uses `mcp_server_nucleus` capabilities (specifically `brain_fix_code` logic) to apply the requested change.
*   **Safety:** Creates a git commit before applying.

### 3. Orchestration (The Loop)
#### [MODIFY] [scripts/audit_oracle.sh](file:///Users/lokeshgarg/ai-mvp-backend/scripts/audit_oracle.sh)
*   Add `--auto-heal` flag.
*   If set, runs `oracle_reflexion.py` immediately after a FAIL verdict.

## Verification Plan

### Automated Verification
*   **Mock Test:** Run `scripts/gladiator_simulator.py` with specific Mock Output containing a "Refinement" section.
*   **Check Queue:** Verify `.brain/backlog/pending_fixes.md` is created/updated.
*   **Dry Run:** Run `scripts/oracle_reflexion.py --dry-run` to verify it can parse the plan.

### Manual Verification
*   Run `./scripts/audit_oracle.sh --auto-heal` and observe the logs.
