---
description: Rescue an overloaded/broken thread by migrating all state to the current thread.
---

# Protocol: Rescue Thread
**Usage:** `/rescue_thread <OLD_THREAD_ID>`
**Pre-requisites:** You must be in a **NEW, EMPTY** thread.
**Version:** 2.0.0 (Hardened)

---

## 0. Pre-Flight (MANDATORY)
1. Confirm `OLD_THREAD_ID` is provided. If not, ask the user.
2. Set variables:
   ```bash
   OLD_BRAIN=~/.gemini/antigravity/brain/<OLD_THREAD_ID>
   NEW_BRAIN=$(pwd)  # Current brain directory
   ```
3. Verify old brain exists:
   ```bash
   ls "$OLD_BRAIN/task.md" || echo "ERROR: Old brain not found. Abort."
   ```

---

## 1. Artifact Migration
// turbo
1. Copy core markdown files EXPLICITLY (no wildcards):
   ```bash
   cp "$OLD_BRAIN/task.md" "$NEW_BRAIN/"
   cp "$OLD_BRAIN/BOOK_OF_WORK.md" "$NEW_BRAIN/" 2>/dev/null || true
   cp "$OLD_BRAIN/DECISION_LOG.md" "$NEW_BRAIN/" 2>/dev/null || true
   cp "$OLD_BRAIN/SYSTEM_STATUS.md" "$NEW_BRAIN/" 2>/dev/null || true
   cp "$OLD_BRAIN/LAUNCH_CONTROL.md" "$NEW_BRAIN/" 2>/dev/null || true
   cp "$OLD_BRAIN/NORTH_STAR_VISION.md" "$NEW_BRAIN/" 2>/dev/null || true
   cp "$OLD_BRAIN/secrets_protocol.md" "$NEW_BRAIN/" 2>/dev/null || true
   cp "$OLD_BRAIN/implementation_plan.md" "$NEW_BRAIN/" 2>/dev/null || true
   cp "$OLD_BRAIN/walkthrough.md" "$NEW_BRAIN/" 2>/dev/null || true
   ```

2. **VERIFICATION GATE A:** Count migrated files:
   ```bash
   ls -la "$NEW_BRAIN/"*.md | wc -l
   # MUST be >= 1. If 0, STOP.
   ```

---

## 2. Native State Migration (CRITICAL)
> **WARNING:** First rescue attempt failed here. Agent declared "done" without copying these.

// turbo
1. Create directories FIRST:
   ```bash
   mkdir -p "$NEW_BRAIN"/{ledger,session,features,swarms,commitments}
   ```

2. Copy EACH directory EXPLICITLY:
   ```bash
   cp -r "$OLD_BRAIN/ledger/"* "$NEW_BRAIN/ledger/" 2>/dev/null || echo "⚠️ ledger/ empty"
   cp -r "$OLD_BRAIN/session/"* "$NEW_BRAIN/session/" 2>/dev/null || echo "⚠️ session/ empty"
   cp -r "$OLD_BRAIN/features/"* "$NEW_BRAIN/features/" 2>/dev/null || echo "⚠️ features/ empty"
   cp -r "$OLD_BRAIN/swarms/"* "$NEW_BRAIN/swarms/" 2>/dev/null || echo "⚠️ swarms/ empty"
   cp -r "$OLD_BRAIN/commitments/"* "$NEW_BRAIN/commitments/" 2>/dev/null || echo "⚠️ commitments/ empty"
   ```

3. **VERIFICATION GATE B:** Check richest state file:
   ```bash
   wc -l "$NEW_BRAIN/ledger/events.jsonl"
   # MUST be > 0 if old thread had activity.
   ```

---

## 3. Continuity Bridge
1. Append the Bridge Phase to `task.md`:
   ```markdown
   
   ### Phase Rescue: Handover Recovery ({{ DATE }}) 🔄 COMPLETE
   **Goal:** Resume operations from Thread `<OLD_THREAD_ID>`.
   
   - [x] **Artifact Migration:** task.md, BOOK_OF_WORK, etc.
   - [x] **Native State Migration:** ledger/, session/, features/, swarms/, commitments/
   - [x] **Verification:** File integrity confirmed.
   ```

---

## 4. Engineer Audit (MANDATORY)
1. Ask these questions about the handover:
   - Does it have explicit CLI commands for verification?
   - Does it have rollback instructions?
   - Does it list unanswered questions?
2. If any answer is "No", add the missing section.

---

## 5. Final Verification Checklist
> **DO NOT DECLARE DONE UNTIL ALL PASS.**

- [ ] `ls -la "$NEW_BRAIN/"` shows `.md` files AND subdirectories.
- [ ] `wc -l "$NEW_BRAIN/ledger/events.jsonl"` returns > 0.
- [ ] `tail -20 "$NEW_BRAIN/task.md"` shows the Handover Phase.
- [ ] `du -sh "$NEW_BRAIN/"` is within 10% of `du -sh "$OLD_BRAIN/"`.
- [ ] Engineer Audit completed (Step 4).

---

## 6. Completion
1. List migrated files for user to confirm.
2. **Notify User:** "Rescue complete. Context bridged. All verification gates passed."
