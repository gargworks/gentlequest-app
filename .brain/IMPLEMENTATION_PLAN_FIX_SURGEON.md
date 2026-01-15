# Implementation Plan: Fix Surgeon & Credentials

## Problem
1.  `audit_oracle.sh` forces `FORCE_VERTEX=1`, causing "Default Credentials not found" on non-GCP envs.
2.  `oracle_reflexion.py` crashes with `ModuleNotFoundError` because `BrainFixCode` doesn't exist.

## Proposed Changes

### 1. `scripts/audit_oracle.sh`
-   Remove `FORCE_VERTEX=1`. Let `llm_client.py` fallback to `GEMINI_API_KEY` naturally.

### 2. `scripts/oracle_reflexion.py`
-   **Add System Path**: Ensure `mcp-server-nucleus/src` is in `sys.path`.
-   **Correct Import**: Import `DualEngineLLM` from `mcp_server_nucleus.runtime.llm_client`.
-   **Implement `BrainFixCode`**: Create a local class `BrainFixCode` that:
    -   Takes `DualEngineLLM` instance.
    -   Uses it to generate a `replace_file_content` JSON blob based on the diagnosis.
    -   Executes the file write using `pathlib` (or `CodeOps` logic).

## Verification Plan
1.  **Run Audit (Mock/Real)**: `@[/oracle-audit]`
    -   Verify it runs without credential error.
    -   Verify if it triggers Surgeon (it might pass if system is good).
    -   If it passes, I will forcibly break a file to test the Surgeon.
