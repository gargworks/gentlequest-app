# Implementation Plan: System Polish (Phase 7)

## Goal
Clean up legacy artifacts, synchronize documentation, and ensure the repo is ready for release/operations.

## Proposed Changes

### 1. Repository Hygiene
- **Archive Legacy Flywheel**: Move `agent_manager.py` to `archive/legacy_agent_manager.py`. It has been superseded by the `mcp-server-nucleus` Runtime.
- **Archive Old Scripts**: Check `scripts/` for deprecated files.

### 2. Documentation Synchronization
- **Update `backlog.md`**:
  - Mark "Memory System" as DONE.
  - Mark "Swarm Persistence" as DONE.
  - Add "Swarm HUD" as DONE.
- **Update `task.md`**:
  - Ensure all accomplished phases are checked.

### 3. Frontend Check
- Verify `tools/nucleus-hud` builds (or just visually check import paths).

## Verification
- Run `ls archive/` to confirm move.
- Run `cat backlog.md` to confirm updates.
