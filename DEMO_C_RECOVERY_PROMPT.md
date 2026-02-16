# Demo C Context Recovery Prompt (BEST CHANCE)

> **Use this exact prompt in a NEW Antigravity chat (same workspace)**
> **Success Rate: Based on verified agent_pool.py recovery pattern**

---

## The Prompt

```markdown
Continue the Nucleus Demo Series / Demo C: Recursive Mounting thread (conversation b95f3ae4-2e33-4132-a8c3-8ecf4024f5ae) where we were implementing mounter_ops.py and the agent got interrupted due to UI/context limits.

## Context Recovery Sources

**Brain Record (Task State):**
/Users/lokeshgarg/.gemini/antigravity/brain/b95f3ae4-2e33-4132-a8c3-8ecf4024f5ae/task.md.resolved

**Workspace Root:**
/Users/lokeshgarg/ai-mvp-backend (MOTHER repo - already exists, DO NOT create new folders)

**Active Codebase:**
/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/

## Recovery Protocol

1. **Read** the brain record (task.md.resolved) to understand:
   - What was completed (✅ marks)
   - What was in-progress (⏳ marks)
   - What Demo C requires (mounter_ops.py, recursive mounting)

2. **Analyze** the current state:
   - Check if mounter_ops.py exists and its completion level
   - Identify pending implementation steps
   - Verify test coverage status

3. **Resume** from the exact interruption point:
   - Complete any partial implementations
   - Generate missing tests/documentation
   - Run verification

4. **Confirm** workspace wiring:
   - Current workspace path = /Users/lokeshgarg/ai-mvp-backend
   - Can access mcp-server-nucleus/ files
   - Can read task.md.resolved from brain record

## Critical Rules

- ❌ DO NOT create new folders (no ai-mvp-backend-v2, no mcp-server-nucleus-new)
- ❌ DO NOT re-implement completed work
- ❌ DO NOT ask "shall I start fresh?" or "redesign from scratch"
- ✅ DO read existing files and continue where the previous conversation stopped
- ✅ DO use the brain record as the single source of truth for task state
- ✅ DO verify you can access the workspace before proceeding

## First Actions

Before any implementation, execute these checks:

1. Confirm: `pwd` shows /Users/lokeshgarg/ai-mvp-backend
2. List: Files in mcp-server-nucleus/runtime/
3. Read: /Users/lokeshgarg/.gemini/antigravity/brain/b95f3ae4-2e33-4132-a8c3-8ecf4024f5ae/task.md.resolved
4. Summarize: What's ✅ done vs ⏳ pending for Demo C
5. Propose: Next 2 concrete implementation steps

Only proceed with implementation after I confirm the wiring is correct.
```

---

## Why This Prompt Works

### Pattern Elements (Verified from agent_pool.py Success)

1. **"Continue [thread name] where we were [specific task]"** 
   - Triggers agent's continuation mode, not fresh start
   - References concrete work artifact (mounter_ops.py)

2. **"agent got interrupted due to [reason]"**
   - Acknowledges the interruption explicitly
   - Sets expectation to resume, not restart

3. **Brain record path**
   - Gives exact file location for state reconstruction
   - task.md.resolved is the authoritative task ledger

4. **Workspace declaration**
   - Prevents new folder creation
   - Makes it explicit this is continuation in same codebase

5. **Verification steps**
   - Forces agent to prove wiring before implementing
   - Gives you a checkpoint to catch mis-wiring early

### What the Agent Will Do

Based on the agent_pool.py recovery pattern, expect:

```
## 📊 Current State Analysis

From the documents, I can see:
- ✅ Step X.X: [Component] - COMPLETE 
- ✅ Step X.X: [Component] - COMPLETE
- 🔄 Step X.X: [Component] - IN PROGRESS (mounter_ops.py partially written)

The file was being generated but got interrupted. I can see it's already quite complete at ~XXX lines. Let me now:

1. Complete any missing pieces in mounter_ops.py
2. Generate the test suite (test_mounter_ops.py)
3. Create the checklist (DEMO_C_CHECKLIST.md)

[Agent proceeds with implementation]
```

Then the agent will:
- Complete the interrupted file
- Generate tests
- Run verification
- Provide next-step instructions

---

## Usage Instructions

### Step 1: Prepare New Chat
1. Open Antigravity UI
2. Select workspace: `/Users/lokeshgarg/ai-mvp-backend`
3. Start NEW chat in that workspace (don't open old stuck chat)

### Step 2: Paste Prompt
- Copy the entire prompt from the markdown block above
- Paste into new chat
- Send

### Step 3: Verify Wiring
Agent should respond with:
- Confirmation of workspace path
- Summary of task.md.resolved contents
- List of what's done vs pending
- Proposed next steps

**If agent says "I'll start fresh" or "create new folder" → STOP and clarify workspace**

### Step 4: Proceed
Once wiring is confirmed correct, tell agent:
```
Wiring confirmed. Proceed with the next pending implementation step for Demo C.
```

---

## Fallback: If Prompt Doesn't Work

If the agent still seems confused or wants to start fresh:

**Immediate clarification:**
```
STOP. You are in a CONTINUATION, not a fresh start.

Workspace: /Users/lokeshgarg/ai-mvp-backend (already exists)
Previous work: conversation b95f3ae4-2e33-4132-a8c3-8ecf4024f5ae
Task state: ~/.gemini/antigravity/brain/b95f3ae4-2e33-4132-a8c3-8ecf4024f5ae/task.md.resolved

Read the task.md.resolved file first. Tell me:
1. What is the Demo C goal?
2. What files already exist in mcp-server-nucleus/runtime/?
3. What is marked as IN PROGRESS?

Do NOT create new folders or rewrite completed work.
```

---

## Success Indicators

You'll know the recovery worked when:

✅ Agent confirms workspace = /Users/lokeshgarg/ai-mvp-backend
✅ Agent reads and summarizes task.md.resolved correctly
✅ Agent identifies specific pending work (e.g., "complete mounter_ops.py lines 450-600")
✅ Agent does NOT suggest creating new folders or starting over
✅ Agent proceeds with implementation of the next incomplete piece

---

*This prompt maximizes recovery success by combining the verified agent_pool.py pattern with explicit Demo C context and anti-duplication safeguards.*
