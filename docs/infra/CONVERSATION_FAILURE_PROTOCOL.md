# Protocol: Conversation Failure Rescue (Zero-Drop Handover)
> **Version:** 2.0.0 (Hardened)  
> **Trigger:** Thread size > 30MB, extreme latency, or hallucinations due to context overload.  
> **Goal:** Migrate 100% of state to a fresh thread with zero packet loss.  
> **Lesson Learned:** This protocol was born from a failed rescue where the agent declared "done" after copying only markdown files, missing all native state. DO NOT TRUST THE AGENT'S FIRST "DONE" SIGNAL.

---

## 1. Early Warning Signs ⚠️

> [!CAUTION]
> If you see **2+** of these, STOP. Do not push through. Initiate rescue immediately.

| # | Warning Sign | How to Detect |
|:-:|:-------------|:--------------|
| 1 | **Latency** | Tool calls take >15 seconds to start. |
| 2 | **Amnesia** | Agent forgets files it viewed 3 turns ago. |
| 3 | **Payload Bloat** | `task.md` alone is >50KB (check with `wc -c task.md`). |
| 4 | **Looping** | Agent repeats "Checking status..." without progress. |
| 5 | **UI Freeze** | Browser/IDE becomes unresponsive when opening the thread. |
| 6 | **Truncation Notices** | "Conversation truncated" messages appear. |

---

## 2. Pre-Flight Checklist (Before Starting Rescue)

> [!IMPORTANT]
> Complete ALL of these BEFORE proceeding. Do NOT skip.

- [ ] **2.1** Confirm the old thread's conversation ID (e.g., `7c654df4-b83e-43f9-8620-f15868ec39d1`).
- [ ] **2.2** Run: `ls ~/.gemini/antigravity/brain/<OLD_ID>/` — Verify directory exists.
- [ ] **2.3** Run: `du -sh ~/.gemini/antigravity/brain/<OLD_ID>/` — Note size for comparison.
- [ ] **2.4** Confirm you are in a **NEW, EMPTY** thread.
- [ ] **2.5** Note the new thread's ID: `b95f3ae4-...` (from URL or brain path).

---

## 3. The Rescue Procedure ⛑️

### Phase A: Artifact Migration (Human-Readable State)

**MANDATORY FILES** — Copy ALL of these. Do NOT use wildcards. Be explicit.

```bash
OLD_BRAIN=~/.gemini/antigravity/brain/<OLD_THREAD_ID>
NEW_BRAIN=~/.gemini/antigravity/brain/<NEW_THREAD_ID>

# Core State (REQUIRED)
cp "$OLD_BRAIN/task.md" "$NEW_BRAIN/"
cp "$OLD_BRAIN/BOOK_OF_WORK.md" "$NEW_BRAIN/" 2>/dev/null || echo "BOOK_OF_WORK.md not found"
cp "$OLD_BRAIN/DECISION_LOG.md" "$NEW_BRAIN/" 2>/dev/null || echo "DECISION_LOG.md not found"
cp "$OLD_BRAIN/SYSTEM_STATUS.md" "$NEW_BRAIN/" 2>/dev/null || echo "SYSTEM_STATUS.md not found"
cp "$OLD_BRAIN/LAUNCH_CONTROL.md" "$NEW_BRAIN/" 2>/dev/null || echo "LAUNCH_CONTROL.md not found"
cp "$OLD_BRAIN/NORTH_STAR_VISION.md" "$NEW_BRAIN/" 2>/dev/null || echo "NORTH_STAR_VISION.md not found"
cp "$OLD_BRAIN/secrets_protocol.md" "$NEW_BRAIN/" 2>/dev/null || echo "secrets_protocol.md not found"
cp "$OLD_BRAIN/implementation_plan.md" "$NEW_BRAIN/" 2>/dev/null || echo "implementation_plan.md not found"
cp "$OLD_BRAIN/walkthrough.md" "$NEW_BRAIN/" 2>/dev/null || echo "walkthrough.md not found"
```

**VERIFICATION GATE A:**
```bash
ls -la "$NEW_BRAIN/"*.md | wc -l
# MUST be >= 1. If 0, STOP and debug.
```

---

### Phase B: Native State Migration (CRITICAL — This is where the first rescue FAILED)

> [!CAUTION]
> **FAILURE MODE:** The first rescue attempt in thread `b95f3ae4` copied only markdown files and declared "done". The user had to explicitly ask for reassessment. The agent then discovered 5 missing directories totaling 750KB of state.

**MANDATORY DIRECTORIES** — These are Antigravity-native. Failure to copy = agent amnesia.

| # | Directory | Contents | Size (Typical) |
|:-:|:----------|:---------|:---------------|
| 1 | `ledger/` | `events.jsonl`, `triggers.json`, `state.json`, `tasks.json` | 150KB+ |
| 2 | `session/` | `depth.json` | <1KB |
| 3 | `features/` | `gentlequest.json`, `nucleus.json`, `proofs/` | 1-5KB |
| 4 | `swarms/` | `state.json` | <1KB |
| 5 | `commitments/` | `ledger.json` (PEFS open loops) | 500KB+ |

**EXPLICIT COMMANDS:**
```bash
# Create directories FIRST
mkdir -p "$NEW_BRAIN"/{ledger,session,features,swarms,commitments}

# Copy EACH directory explicitly. Do NOT use a single wildcard.
cp -r "$OLD_BRAIN/ledger/"* "$NEW_BRAIN/ledger/" 2>/dev/null || echo "⚠️ ledger/ empty or missing"
cp -r "$OLD_BRAIN/session/"* "$NEW_BRAIN/session/" 2>/dev/null || echo "⚠️ session/ empty or missing"
cp -r "$OLD_BRAIN/features/"* "$NEW_BRAIN/features/" 2>/dev/null || echo "⚠️ features/ empty or missing"
cp -r "$OLD_BRAIN/swarms/"* "$NEW_BRAIN/swarms/" 2>/dev/null || echo "⚠️ swarms/ empty or missing"
cp -r "$OLD_BRAIN/commitments/"* "$NEW_BRAIN/commitments/" 2>/dev/null || echo "⚠️ commitments/ empty or missing"
```

**VERIFICATION GATE B:**
```bash
# Check ledger events exist (this is the richest state file)
wc -l "$NEW_BRAIN/ledger/events.jsonl"
# MUST be > 0 if old thread had any activity.

# Check commitments ledger (PEFS)
ls -la "$NEW_BRAIN/commitments/ledger.json"
# Should exist if PEFS was active.
```

---

### Phase C: The Continuity Bridge (Audit Trail in `task.md`)

> [!IMPORTANT]
> This step creates a permanent record that explains the context shift. Without it, future sessions won't understand why phases jump.

**APPEND TO `task.md`:**
```markdown

---

### Phase X: Handover Recovery (YYYY-MM-DD) 🔄 COMPLETE
**Goal:** Resume operations from Thread `<OLD_THREAD_ID>`.
**Source:** Conversation that exceeded safe operating size.

- [x] **Artifact Migration:**
    - [x] `task.md` (XXX KB)
    - [x] `BOOK_OF_WORK.md`
    - [x] `DECISION_LOG.md`
    - [x] `SYSTEM_STATUS.md`
    - [x] `NORTH_STAR_VISION.md`
    - [x] `secrets_protocol.md`
- [x] **Native State Migration:**
    - [x] `ledger/` (XXX events)
    - [x] `session/` (depth.json)
    - [x] `features/` (X features)
    - [x] `swarms/` (state.json)
    - [x] `commitments/` (XXX KB)
- [x] **Audit:** Verified file integrity.
```

---

### Phase D: The Engineer Audit (MANDATORY — DO NOT SKIP)

> [!CAUTION]
> **FAILURE MODE:** The first handover document was "good enough" but lacked operational details (rollback commands, smoke tests). Only after the user asked "read this as a new engineer" did the agent discover 6 missing sections.

**REQUIRED SELF-CRITIQUE QUESTIONS:**

| # | Question | Action if "No" |
|:-:|:---------|:---------------|
| 1 | Does the handover doc contain **explicit CLI commands** for verification? | Add smoke test commands. |
| 2 | Does the handover doc contain **rollback instructions**? | Add `gcloud run services update-traffic --to-revisions=<OLD>` commands. |
| 3 | Are **all secrets documented** (even if redacted)? | Add secrets section with `****` placeholders. |
| 4 | Is there an **"Unanswered Questions"** section? | List what you don't know. |
| 5 | Is there a **"Next Steps"** section with numbered tasks? | Add prioritized task list. |

---

## 4. Final Verification Checklist

> [!WARNING]
> DO NOT declare "done" until ALL of these pass.

- [ ] **4.1** `ls -la "$NEW_BRAIN/"` shows both `.md` files AND subdirectories (`ledger/`, `session/`, etc.).
- [ ] **4.2** `wc -l "$NEW_BRAIN/ledger/events.jsonl"` returns > 0.
- [ ] **4.3** `tail -20 "$NEW_BRAIN/task.md"` shows the new Handover Phase.
- [ ] **4.4** `du -sh "$NEW_BRAIN/"` is within 10% of `du -sh "$OLD_BRAIN/"` (allows for smaller due to no images).
- [ ] **4.5** The Engineer Audit (Phase D) has been completed.

---

## 5. Automation: `/rescue_thread`

See `.agent/workflows/rescue_thread.md` for the executable definition.

**Usage:**
```
/rescue_thread <OLD_THREAD_ID>
```

---

## 6. Prevention: How to Avoid This Next Time 🛡️

| # | Rule | Why |
|:-:|:-----|:----|
| 1 | **One Feature = One Thread** | Prevents monolithic 30MB conversations. |
| 2 | **Archive Completed Phases** | Move closed milestones to `docs/history/`. |
| 3 | **Externalize Large State** | Keep 100KB+ documents in repo, not brain. |
| 4 | **Use `task_boundary` Mode** | Creates checkpoints every phase. |
| 5 | **Watch for Truncation** | If you see "context truncated", rescue immediately. |

---

## 7. Reference: Actual Failure Timeline (Thread b95f3ae4)

| Step | What Happened | Lesson |
|:-----|:--------------|:-------|
| 1 | Agent copied 9 `.md` files. | Insufficient. |
| 2 | Agent declared "✅ Zero-Drop Handover Complete". | **FALSE**. |
| 3 | User asked: "Reassess if this is truly done." | User caught the error. |
| 4 | Agent discovered 5 missing native directories (750KB). | Critical state was missing. |
| 5 | Agent migrated native state. | Should have been Step 1. |
| 6 | User asked for "Engineer Audit". | Handover doc was incomplete. |
| 7 | Agent added 6 missing sections to handover. | Should have been automatic. |

**Takeaway:** Never trust the agent's first "done" signal. Always run the Final Verification Checklist.

---

**Status:** Canonical Protocol (Hardened)  
**Version:** 2.0.0  
**Last Updated:** 2026-01-15
