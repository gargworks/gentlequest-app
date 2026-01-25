
# Walkthrough: Phase 21 - Critical Maintenance Sprint

> **Objective:** Fix critical bugs identified by Windsurf Audit (2026-01-10).
> **Status:** ✅ COMPLETE
> **Date:** 2026-01-10

## 🐛 Bug Fixes

### 1. Pending Tasks Visibility (Critical)
- **Issue:** `brain_list_tasks(status="PENDING")` returned empty list because it only read the legacy `tasks.json` (which was empty) and ignored `task.md`.
- **Root Cause:** 
    1. Data Ingestion: `brain_scan_commitments` was scanning `artifacts/` subfolder instead of root, and `rg` command was malformed.
    2. Data Retrieval: `brain_list_tasks` did not query the `commitment_ledger`.
- **Fix:**
    - Updated `scan_for_commitments` to scan `brain_path` (root) and strictly parse `rg` output (ignoring `.resolved` files).
    - Updated `_list_tasks` to load `commitment_ledger` and merge items into the response.
- **Verification:**
    - `brain_scan_commitments` found **455** items.
    - `brain_list_tasks(PENDING)` returned **455** tasks.

### 2. Proof Generation Args
- **Issue:** Windsurf reported "Argument count mismatch" for `brain_generate_proof`.
- **Analysis:** Code inspection confirmed `ProofSystem._generate_proof` accepts `args: Dict`, and the wrapper passes a dictionary.
- **Result:** Verified as False Positive/Caller Error.

### 3. Trigger Evaluation
- **Issue:** Windsurf reported `brain_evaluate_triggers` returns `None`.
- **Analysis:** Code ensures `List[str]` return in all paths (success or exception).
- **Result:** Verified as False Positive.

## 🛠 Files Modified
- `mcp_server_nucleus/commitment_ledger.py` (Scanner logic)
- `mcp_server_nucleus/__init__.py` (Task list logic)

## 📊 Impact
The agent is no longer "blind" to the backlog. It can now effectively query pending work from `task.md`.
