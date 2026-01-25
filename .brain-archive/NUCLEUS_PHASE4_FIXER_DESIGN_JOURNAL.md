
# Design Journal: Nucleus Self-Healing Loop (The Fixer)

> **Date:** 2026-01-11
> **Phase:** 4 (Self-Evolution)

## 🎯 Problem Statement
Currently, `brain_fix_code` is a "fire-and-forget" tool. It attempts to fix a file but has no feedback loop.
If the fix fails (syntax error, regression), the user must manually intervene.
We need a **Closed Loop System** that can iterate until success or exhaustion.

## 🏗 Architecture: The Fixer Loop

### 1. The Loop Protocol (`FixerLoop`)
A python class that manages the repair cycle.
```python
class FixerLoop:
    def __init__(self, target_file, test_command, max_retries=3):
        ...
    
    def run(self):
        while retries < max_retries:
            # 1. Verification (Run Test)
            success, output = self._run_test()
            if success:
                return "Fixed!"
            
            # 2. Diagnosis (Analyze Output)
            issues = self._analyze_failure(output)
            
            # 3. Repair (Call Fixer)
            brain_fix_code(self.target_file, issues)
            
            retries += 1
```

### 2. The Agent Persona (`fixer.md`)
We need a specialized persona that understands it is part of a loop.
It should be conservative and focused on minimal changes to pass the test.

### 3. Tool Exposure
New tool: `brain_auto_fix_loop(file_path: str, verification_command: str)`.
This delegates to `FixerLoop`.

## 🧠 Cognitive Architecture
- **Critic**: Identifies the break (already exists).
- **Fixer**: Patches the code.
- **Verifier**: Runs the test (The Loop).

## ⚠️ Risks & Mitigations
- **Infinite Loops**: Hard limit on retries (3-5).
- **Destructive Fixes**: `brain_fix_code` already creates `.bak` files.
- **Flaky Tests**: The loop might "fix" a flaky test by just rerunning it. (Acceptable for now).

## 📝 Implementation Steps
1. Create `mcp_server_nucleus/runtime/loops/fixer.py`.
2. Implement `FixerLoop` class.
3. Expose `brain_auto_fix_loop` in `__init__.py`.
4. Create `tests/test_fixer_loop.py` (Integration test).
