# 🛡️ Safety Audit: Agentic Actions Review
> **Date:** 2026-01-06  
> **Purpose:** Verify all agentic systems for irreversible/destructive operations  
> **Status:** ✅ PASS (with notes)

---

## Executive Summary

All current agentic systems are **safe** with respect to destructive file operations. No automatic deletions occur in production-critical paths. Manual confirmation or explicit mode triggers are required for any destructive action.

---

## Audit Findings

### 1. `nightly_agent.py` (Primary Autonomous Daemon)

| Metric | Status |
|:-------|:-------|
| `os.remove()` calls | ❌ None |
| `shutil.rmtree()` calls | ❌ None |
| File writes | ✅ Append-only (events.jsonl, digest.md) |

**Verdict:** ✅ **SAFE.** This script only reads and appends. No destructive operations.

---

### 2. `switch_brain.py` (Brain Switching Utility)

| Metric | Status |
|:-------|:-------|
| `shutil.rmtree()` calls | ⚠️ Yes (line 69) |
| Trigger Condition | Only when `mode == "cold"` |
| Target | `/Users/lokeshgarg/dogfood-brain/.brain` |

**Code:**
```python
if mode == "cold":
    shutil.rmtree(brain_path)  # Deletes dogfood brain
```

**Verdict:** 🟡 **INTENTIONAL.** This is for dogfood/testing. Does NOT affect production brain. However, recommend adding backup before delete.

---

### 3. `nucleus-init` (CLI Initialization)

| Metric | Status |
|:-------|:-------|
| `shutil.rmtree()` calls | ⚠️ Yes (line 324) |
| Trigger Condition | Only when user confirms overwrite |
| Safety Mechanism | Creates timestamped backup FIRST |

**Code:**
```python
backup_path = Path(f"{path}.backup.{timestamp}")
shutil.copytree(brain_path, backup_path)  # Backup first
shutil.rmtree(brain_path)  # Then delete
```

**Verdict:** ✅ **SAFE.** Backups exist. User must explicitly confirm.

---

### 4. Test Files (Various)

| File | Purpose |
|:-----|:--------|
| `test_depth_tracker.py` | Cleans up temp test directory |
| `test_brain_v2_logic.py` | Cleans up temp test directory |

**Verdict:** ✅ **SAFE.** These only delete `/tmp/` or `test_*` directories created during test runs. No production data at risk.

---

## Recommendations

### ✅ Already Safe
- `nightly_agent.py` is append-only.
- `nucleus-init` backs up before clearing.
- All tests clean up only their own temp data.

### 🟡 Consider Improving
1. **`switch_brain.py`:** Add a backup before deleting cold brain.
2. **Future Consolidation Features:** MUST use `shutil.move()` not `os.remove()`.

---

## Guiding Principle

> **Reversibility First:** Any Brain Consolidation feature MUST be implemented as MOVE operations, not DELETE. Archiving to `.brain/archive/` is the only approved approach.

---

## Linked Principles

- **NORTH_STAR_VISION.md** Principle XIII: Forgiveness Architecture
- **BRAIN_CONSOLIDATION_PRINCIPLE.md** Phase 2: CEO-Assisted (not auto-delete)
- **DECISION_LOG.md** [004]: Nuclear Hazard Switch (Conservative approach)
