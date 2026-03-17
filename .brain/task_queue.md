# Task Queue for Path 2
> Small brother's work backlog. Ordered by risk (safest first).
> Big brother picks from top. Father can reprioritize.

## ~~Task 1: Write a test for the circuit breaker~~ DONE
- **PR:** #7 (backend-tests green, awaiting father merge)
- **Bonus:** Fixed CI for good — watchdog hang, graceful imports, conftest

## ~~Task 2: Add brain backup to heartbeat schedule~~ REPLACED
- **Decision:** Father chose manual biweekly SSD backup + heartbeat nudge (Signal 7: BACKUP_OVERDUE). No auto-backup.

## Task 3: Add secret pattern detection to archive writes
- **Why:** Pads risk #9 (secret leakage) from risk registry
- **Branch:** `family/archive-secret-filter`
- **Provider:** claude-code
- **Risk:** Medium — edits cli.py (own organ)

## Task 4: Write the delegation log tracker
- **Why:** Enables graduation criteria tracking
- **Branch:** `family/delegation-logger`
- **Provider:** claude-code
- **Risk:** Low — new utility, minor integration

## Task 5: Build weekly trajectory report
- **Why:** Pads risk #7 (strategic drift) from risk registry
- **Branch:** `family/trajectory-report`
- **Provider:** gemini for design, claude-code for implementation
- **Risk:** Low — new feature, reads brain only
