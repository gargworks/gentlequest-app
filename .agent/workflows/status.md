---
description: Check pending tasks and session identity
---

# Status Check

Use this workflow to see what work is pending and who is working on what.

## Steps

1. Call `brain_session_briefing` with your conversation ID:
   ```
   brain_session_briefing(conversation_id="YOUR_CONVERSATION_ID")
   ```

2. If starting new work, register your session:
   ```
   brain_register_session(conversation_id="YOUR_CONVERSATION_ID", focus_area="What you're working on")
   ```

## When to Use

- At the start of any new conversation
- When you want to see pending tasks
- Before asking "How can I help?"
