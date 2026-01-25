
# Walkthrough: Self-Healing Loop (Phase 4)

> **Date:** 2026-01-11
> **Status:** ✅ Completed
> **Target:** `mcp-server-nucleus`

## 🎯 Goal
Implement a **Self-Healing Loop** (The Fixer) that autonomously repairs code failures.
It uses a "Verify -> Diagnose -> Fix" cycle to iteratively correct issues without human intervention.

## 🛠 Changes Implemented

### 1. The Fixer Loop (`runtime/loops/fixer.py`)
- Implemented `FixerLoop` class.
- **Protocol**:
  1. Run Verification Command (e.g., `pytest`).
  2. If Fail: Analyze output.
  3. Call `brain_fix_code` (The Fixer Agent).
  4. Retry (max 3 times).
  5. If Success: Stop and report.

### 2. The Fixer Persona (`.brain/agents/fixer.md`)
- A conservative agent focused on:
  - Minimal changes.
  - Strict style adherence.
  - Returning ONLY code.

### 3. Tool Exposure (`__init__.py`)
- Added `brain_auto_fix_loop(file_path, verification_command)` tool.
- This allows *any* agent (Coordinator, Developer) to trigger a self-repair session.

## ✅ Verification
- **Test Script**: `tests/test_fixer_loop.py` (Passed).
- **Simulation**:
  - Created a dummy fail file.
  - Fixer "repaired" it (mocked).
  - Loop detected success and stopped.

## 🚀 How to use
```bash
nucleus spawn "Run tests for my_script.py and auto-fix if they fail"
# Agent calls: brain_auto_fix_loop("my_script.py", "pytest my_script.py")
```
