# Antigravity Context Recovery Guide

> **Purpose:** Recover from "black hole" UI state where Antigravity stops rendering responses but conversation still exists.
> **Last Updated:** February 13, 2026

---

## Problem: The "Black Hole" State

### Symptoms
- You send a prompt to Antigravity
- The UI accepts it but shows no response
- The conversation appears "stuck" or "frozen"
- Previous messages are visible but no new output renders

### Root Cause
- The conversation `.pb` (protobuf) file in `~/.gemini/antigravity/conversations/` has grown too large (20-30+ MB)
- The UI cannot efficiently render/stream from such large conversation histories
- The backend is still working and appending to the file, but the frontend chokes

### What's NOT Lost
- Your work is still saved in the conversation file
- Brain records in `~/.gemini/antigravity/brain/<conversation-id>/` are intact
- All code changes in the workspace are preserved
- The task state in `task.md.resolved` is safe

---

## Solution: Start Fresh Chat with Context Inheritance

### Step 1: Identify the Stuck Conversation

Find the conversation ID from the brain folder:
```bash
ls -lh ~/.gemini/antigravity/brain/
# Look for most recent folder, e.g. b95f3ae4-2e33-4132-a8c3-8ecf4024f5ae

cat ~/.gemini/antigravity/brain/<conversation-id>/task.md.resolved
# Verify this is the right task
```

Verify the conversation file is bloated:
```bash
ls -lh ~/.gemini/antigravity/conversations/<conversation-id>.pb
# If >20MB, this is the black hole culprit
```

### Step 2: Open New Chat in SAME Workspace

**Critical:** Do not create a new workspace/folder.

1. In Antigravity UI, select/open the **`/Users/lokeshgarg/ai-mvp-backend`** workspace
2. Start a **new chat** within that workspace (not a new task, just new conversation)
3. This ensures the new chat inherits the workspace root automatically

### Step 3: Bootstrap the New Chat

Use this prompt template (adapt conversation ID and task name):

```markdown
Workspace: /Users/lokeshgarg/ai-mvp-backend (MOTHER repo - do not create new folders)

Context inheritance from previous conversation:
- Previous conversation ID: b95f3ae4-2e33-4132-a8c3-8ecf4024f5ae
- Task: Nucleus Demo Series Completion → Demo C: Recursive Mounting (Aggregator)

Shared state sources (DO NOT DUPLICATE, READ ONLY):
1. /Users/lokeshgarg/.gemini/antigravity/brain/b95f3ae4-2e33-4132-a8c3-8ecf4024f5ae/task.md.resolved
2. /Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/ (existing codebase)
3. /Users/lokeshgarg/ai-mvp-backend/nucleus-launch-internal/LOOM_RECORDING_GUIDE_v2.md

Rules:
- DO NOT create new folders like ai-mvp-backend-v2 or mcp-server-nucleus-new
- DO NOT start from scratch or re-design anything
- DO use existing files and continue where the previous conversation left off
- .gemini/antigravity/ is global shared state across all sessions

First action:
1. Confirm workspace is /Users/lokeshgarg/ai-mvp-backend
2. Read task.md.resolved from the old brain record
3. Summarize what's done vs pending for Demo C
4. Propose next 2 concrete implementation steps
```

### Step 4: Verify Wiring

Before proceeding with work, ask the agent:
```
Confirm:
1. What is your current workspace path?
2. Can you list files in mcp-server-nucleus/?
3. What does the task.md.resolved say about Demo C status?
```

If answers are correct, the new chat is properly wired to the old context.

---

## How Antigravity Context Wiring Works

### Three-Layer Architecture

1. **Conversation files** (`~/.gemini/antigravity/conversations/<uuid>.pb`)
   - Stores full chat transcript, tool calls, responses
   - When >20MB, UI performance degrades catastrophically
   - These are conversation-specific, NOT shared

2. **Brain records** (`~/.gemini/antigravity/brain/<uuid>/task.md.resolved`)
   - Stores task definition, checklist, high-level state
   - Much smaller files, always readable
   - The UUID links brain → conversation (same ID)

3. **Workspace folder** (e.g. `/Users/lokeshgarg/ai-mvp-backend`)
   - Set when you open a project in Antigravity UI
   - All file operations are relative to this root
   - Shared across all conversations in that workspace

### The "Glue"

- **UUID** connects conversation ↔ brain: both use same ID
- **Workspace path** is stored in Antigravity's internal metadata (not visible in files)
- When you start a new chat in the same workspace, it inherits the workspace root
- You manually wire to old brain records by pointing to the old UUID path in your prompt

### What's Shared vs Isolated

| Resource | Shared Across Chats? | Notes |
|----------|---------------------|-------|
| Workspace files (code, docs) | ✅ Yes | Same folder on disk |
| Brain records (`brain/`) | ✅ Yes | Any chat can read any brain folder |
| Conversation history (`.pb`) | ❌ No | Each chat has its own transcript |
| Context state | ⚠️ Manual | New chat must explicitly read old brain record |

---

## Prevention: Avoid Black Holes

### Early Warning Signs
- Conversation `.pb` file >15MB
- UI starts to lag when scrolling history
- Responses take >5 seconds to start rendering

### Mitigation
- When you see warning signs, proactively start a fresh chat using the bootstrap prompt above
- Do NOT wait until the UI fully blacks out
- Archive old conversation ID in your notes for reference

### Long-Term
- Keep conversations focused on specific tasks (Demo A, Demo B, Demo C as separate chats)
- Use brain records (`task.md.resolved`) as the "source of truth," not chat history
- Treat conversations as disposable transcripts; brain + code are the durable assets

---

## Reference: Related Docs

- **`ANTIGRAVITY_BOOTSTRAP.md`** - Role definitions and file reading order for new threads
- **`~/apps/believe-it-bot/CONTEXT_RECOVERY.md`** - Example context snapshot for another project
- **`/Users/lokeshgarg/OS.md`** - Studio-wide workspace rules (useful for playground setup)

---

## Quick Command Reference

```bash
# Find active brain records
ls -lht ~/.gemini/antigravity/brain/ | head

# Check conversation file sizes
ls -lhS ~/.gemini/antigravity/conversations/*.pb | head

# Read task state for a specific conversation
cat ~/.gemini/antigravity/brain/<uuid>/task.md.resolved

# Verify current workspace in code
pwd
ls mcp-server-nucleus/  # Should exist if wired correctly
```

---

*This document enables recovery from Antigravity black hole states without losing context or duplicating work.*
