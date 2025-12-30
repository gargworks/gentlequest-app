# MCP End-to-End UX Verification Checklist

> **Purpose:** Verify the complete user journey works before launch
> **Date:** December 27, 2025

---

## The Gap We Identified

| What We Tested | What We DIDN'T Test |
|----------------|---------------------|
| ✅ pip install | ❌ Claude Desktop sees the tools |
| ✅ nucleus init | ❌ Tools actually execute from Claude |
| ✅ pytest (11 tests) | ❌ Response format is user-friendly |
| ✅ GitHub synced | ❌ Error handling in real use |

---

## 🧪 End-to-End Test Script

### Phase 1: Installation (User as Tester)

**Step 1.1:** Fresh install from PyPI
```bash
python3.11 -m pip install --upgrade mcp-server-nucleus
```
✅ Expected: Installs without errors

**Step 1.2:** Initialize a test brain
```bash
cd /tmp
python3.11 -m mcp_server_nucleus.cli init test_brain
```
✅ Expected: Creates .brain/ structure with clear output

---

### Phase 2: Claude Desktop Configuration

**Step 2.1:** Edit Claude config
```bash
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Step 2.2:** Add nucleus-brain server:
```json
{
  "mcpServers": {
    "nucleus-brain": {
      "command": "python3.11",
      "args": ["-m", "mcp_server_nucleus"],
      "env": {
        "NUCLEAR_BRAIN_PATH": "/tmp/test_brain"
      }
    }
  }
}
```

**Step 2.3:** Restart Claude Desktop completely
- Cmd+Q to quit
- Reopen from Applications

---

### Phase 3: Tool Verification in Claude Desktop

Open Claude Desktop and test each scenario:

| # | User Says | Expected Tool Called | Expected Response |
|---|-----------|---------------------|-------------------|
| 1 | "What's my current sprint focus?" | `brain_get_state` | Shows "Sprint 1: Getting Started with Nucleus" |
| 2 | "List my artifacts" | `brain_list_artifacts` | Shows research/, strategy/ folders |
| 3 | "Show my triggers" | `brain_get_triggers` | Shows 2 triggers (task_completed, research_done) |
| 4 | "Log an event that I'm testing" | `brain_emit_event` | Confirms event written to events.jsonl |
| 5 | "Read the context file" | `brain_read_artifact` | Shows "# Project Context..." content |

---

### Phase 4: Error Handling

| # | User Says | Expected Behavior |
|---|-----------|-------------------|
| 1 | "Read artifact nonexistent.md" | Graceful error: "Artifact not found" |
| 2 | (With bad BRAIN_PATH) | Clear error message about missing path |

---

## 📊 Test Results Template

| Test | Pass/Fail | Notes |
|------|-----------|-------|
| Install from PyPI | | |
| nucleus init | | |
| Claude sees tools | | |
| brain_get_state | | |
| brain_list_artifacts | | |
| brain_get_triggers | | |
| brain_emit_event | | |
| brain_read_artifact | | |
| Error handling | | |

---

## 🎯 Success Criteria

- [ ] All 5 core tools work from Claude Desktop
- [ ] Response format is clear and helpful
- [ ] Error messages guide user to fix issues
- [ ] No crashes or hangs

---

## After Testing

If all passes:
1. ✅ Launch video
2. ✅ Post to Twitter/HN/Reddit
3. ✅ Open the floodgates

If issues found:
1. Document in this file
2. Fix before launch
3. Re-test
