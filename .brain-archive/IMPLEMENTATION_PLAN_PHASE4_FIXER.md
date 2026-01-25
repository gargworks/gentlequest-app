
# Implementation Plan: Self-Healing Loop (The Fixer)

## Goal
Implement a **Closed-Loop Repair System** (`FixerLoop`) that can iteratively run a verification command, analyze failure, and apply fixes until success or timeout.
This enables `brain_auto_fix_loop`.

## User Review Required
> [!NOTE]
> This introduces a new runtime module `loops/fixer.py`.
> It requires `brain_fix_code` to be available (already verified).

## Proposed Changes

### `mcp-server-nucleus`

#### [NEW] `src/mcp_server_nucleus/runtime/loops/fixer.py`
- Class `FixerLoop`
  - `__init__(target_file, test_cmd, max_retries=3)`
  - `run()`: Main loop logic.
  - `_run_verification()`: Executes shell command.
  - `_invoke_fixer(output)`: Calls `brain_fix_code`.

#### [MODIFY] `src/mcp_server_nucleus/__init__.py`
- Export `brain_auto_fix_loop(target_file, verification_command)` tool.
- Delegate to `FixerLoop`.

#### [NEW] `.brain/agents/fixer.md`
- **Identity**: The Fixer.
- **Goal**: Repair code based on error logs.
- **Constraint**: Minimal changes, preserve style.

## Verification Plan

### Automated Verification
- **Test Script**: `tests/test_fixer_loop.py`.
- **Scenario 1 (Simulation)**:
  - Create a temporary file.
  - Mock `brain_fix_code` to "fix" the file (e.g., replace "FAIL" with "PASS").
  - Run `FixerLoop` with a command that checks for "PASS".
  - Assert that it retries once and then succeeds.

### Manual Verification
- **Spawn**: `nucleus spawn "Fix tests/broken_file.py using 'pytest tests/broken_file.py'"`
- **Expectation**: Agent sees failure, calls fixer, runs test again, sees success.
