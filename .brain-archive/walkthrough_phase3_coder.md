# Phase 3: The Coder Agent (Walkthrough)

**Date:** 2026-01-10
**Status:** ✅ Operational (Local)

## 🎯 Objective
Create an autonomous agent capable of writing, modifying, and executing code on the local machine (Mac).

## 🏗️ Architecture

### 1. The "Hands": `CodeOps` Capability
Located in `runtime/capabilities/code_ops.py`.
Provides the agent with physical access to the filesystem:
- `code_read_file(path)`
- `code_write_file(path, content)`
- `code_run_command(command)`
- `code_list_files(path)`

### 2. The "Mind": `Developer` Persona
Registered in `factory.py`.
- **Name:** Developer (Engineer)
- **Role:** Implementation Specialist
- **Capabilities:**
  - `brain_ops` (Memory)
  - `code_ops` (Hands)
  - `proof_system` (Validation)
- **Prompt:** Defined in `.brain/agents/developer.md` (Level 5 Autonomy)

### 3. The "Voice": Explicit Spawning
Updated `brain_spawn_agent` to accept `persona="developer"`.
This allows us to bypass intent classification and force the use of the Coder Agent.

## 🧪 Verification
Verified via `tests/test_coder_agent.py`.
- **Task:** "Create hello_code_ops.py"
- **Result:** Success. File created with correct content.
- **Trace:**
  ```
  >> Tool detected: code_write_file
  [Tool Result]: ✅ Wrote 28 bytes to .../hello_code_ops.py
  ```

## 🚀 How to Use
Ask any agent:
> *"Spawn a developer to create a new file called utils.py with a helper function..."*

Or programmatically:
```python
brain_spawn_agent(
    intent="Create utils.py...",
    persona="developer"
)
```

## ⚠️ Safety
Current implementation has **ROOT** access to the project folder.
It can modify/delete any file. Ensure `monitor_mode` (Watchdog) is active to track changes.
