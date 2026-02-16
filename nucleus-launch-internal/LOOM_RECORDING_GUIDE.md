# 🧠 Nucleus 60-Second Demo: Recording Guide

This guide helps you record a high-impact, 60-second Loom for the community.

### 🎬 The Script (60 Seconds)

| Time | Action | What to Say |
|------|--------|-------------|
| **0:00-0:10** | Show Terminal (Ready to run) | "Hey everyone, this is Nucleus—the Agent Control Plane. I'm going to show you how to govern your agents in under 60 seconds." |
| **0:10-0:25** | Run `scripts/demo_60_seconds.py` (Step 1-2) | "First, we mount our tools. Nucleus starts with a **Default-Deny** policy, sandboxing every agent and every tool from day one." |
| **0:25-0:45** | Script Step 3-4 (Engrams) | "Next is memory. We can save architectural decisions as **Engrams**. These persist across sessions, so your agents never forget why you chose PostgreSQL over NoSQL." |
| **0:45-1:00** | Script Step 5 (Audit) | "Finally, every decision is cryptographically logged in an **Immutable Audit Trail**. You get zero-trust security plus perfect memory. That's Nucleus." |

### 🛠️ Prep Steps
1. **Clear Terminal**: Close all distracting tabs.
2. **Terminal Font**: Increase font size (Command + '+') for readability.
3. **Execution**:
   ```bash
   cd mcp-server-nucleus
   python3 scripts/demo_60_seconds.py
   ```

### 💡 Pro-Tip
The script has built-in pauses (2s) between steps to allow you to talk. If you need more time, you can edit the `pause(2)` calls in `scripts/demo_60_seconds.py` before recording.
