# Multi-Client MCP Testing Guide

> Test mcp-server-nucleus across multiple MCP-compatible clients
> Date: December 27, 2025

---

## 🎯 Why Multi-Client Testing?

| Client | Audience | Proof Point |
|--------|----------|-------------|
| Claude Desktop | Power users | "Works with Claude" |
| Windsurf | Developers | "Works in your IDE" |
| Cursor | Developers | "Works with Cursor" |

---

## 1️⃣ Claude Desktop Configuration

**Config Path:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "nucleus-brain": {
      "command": "python3.11",
      "args": ["-m", "mcp_server_nucleus"],
      "env": {
        "NUCLEAR_BRAIN_PATH": "/Users/lokeshgarg/ai-mvp-backend/.brain"
      }
    }
  }
}
```

**Restart:** Cmd+Q then reopen

---

## 2️⃣ Windsurf Configuration

**Config Path:** `~/.codeium/windsurf/mcp_config.json`

**Access:** 
- Cmd+Shift+P → "Open Windsurf Settings" → Advanced → Cascade
- Or directly edit the file

```json
{
  "mcpServers": {
    "nucleus-brain": {
      "command": "python3.11",
      "args": ["-m", "mcp_server_nucleus"],
      "env": {
        "NUCLEAR_BRAIN_PATH": "/Users/lokeshgarg/ai-mvp-backend/.brain"
      }
    }
  }
}
```

**Restart:** Completely close and reopen Windsurf

---

## 3️⃣ Cursor Configuration

**Config Path:** `~/.cursor/mcp.json`

**Access:** 
- File → Preferences → Cursor Settings → MCP
- Or click "Add New MCP Server"

```json
{
  "mcpServers": {
    "nucleus-brain": {
      "command": "python3.11",
      "args": ["-m", "mcp_server_nucleus"],
      "env": {
        "NUCLEAR_BRAIN_PATH": "/Users/lokeshgarg/ai-mvp-backend/.brain"
      }
    }
  }
}
```

**Restart:** Required after adding

---

## 🧪 Test Matrix

Run these tests in EACH client:

| # | Command to AI | Expected Tool | ✅ Claude | ✅ Windsurf | ✅ Cursor |
|---|---------------|---------------|-----------|-------------|-----------|
| 1 | "What's my current sprint focus?" | brain_get_state | [ ] | [ ] | [ ] |
| 2 | "List my artifacts" | brain_list_artifacts | [ ] | [ ] | [ ] |
| 3 | "Show my triggers" | brain_get_triggers | [ ] | [ ] | [ ] |
| 4 | "Log an event: testing complete" | brain_emit_event | [ ] | [ ] | [ ] |
| 5 | "Read my context file" | brain_read_artifact | [ ] | [ ] | [ ] |

---

## 📊 Results Log

### Claude Desktop
- Date tested: ___
- Version: ___
- Pass/Fail: ___
- Notes: ___

### Windsurf
- Date tested: ___
- Version: ___
- Pass/Fail: ___
- Notes: ___

### Cursor
- Date tested: ___
- Version: ___
- Pass/Fail: ___
- Notes: ___

---

## 🚀 After All Pass

Update README.md to include:

```markdown
## Supported Clients

| Client | Status |
|--------|--------|
| Claude Desktop | ✅ Tested |
| Windsurf | ✅ Tested |
| Cursor | ✅ Tested |
```

This becomes a marketing asset!
