# MCP Debugging Field Guide: From Docs to Reality
> **Sources:** Official MCP Docs, Empirical Lessons from Nucleus Dogfooding
> **Date:** December 28, 2025

---

## 1. The Golden Priority of Logs

### Official Docs Say:
- "Check server logs" is step #1.
- In Claude Desktop: `tail -n 20 -F ~/Library/Logs/Claude/mcp*.log`

### Reality Check (Nucleus Lesson):
- **Problem:** If your local dev server crashes BEFORE Claude can attach, it writes NOTHING to Claude's logs.
- **Problem:** If you use `print()` in your Python code, it goes to `stdout`. Since MCP uses `stdio` (stdin/stdout) for JSON-RPC communication, **random print statements break the protocol.**
- **The Protocol Crash:**
  ```text
  Client: {json-rpc request}
  Server: "Hello world!" <-- NOT JSON!
  Client: ERROR: Parse Exception (CRASH)
  ```

### Field Recommendation:
1. **NEVER use `print()`** in an MCP server.
2. **Setup File Logging** immediately. Don't rely on Claude's capture.
   ```python
   # In your server's __init__.py
   import logging
   logging.basicConfig(filename='/tmp/my_mcp_server.log', level=logging.DEBUG)
   ```
3. **Use stderr** if you must print (FastMCP does this by default if configured right).

---

## 2. The "Ghost Code" Problem (Installation Modes)

### Official Docs Say:
- "Check working directory" and "Environment variables".

### Reality Check:
- Python has a strict package resolution order.
- If you `pip install my-package` (Standard Mode) AND have the source code folder...
- Running `python -m my_package` uses the **Standard Mode** copy.
- **Result:** You edit code, nothing happens. You add logs, no logs appear. You go crazy.

### Field Recommendation:
- **ALWAYS** use Editable Install for development:
  ```bash
  pip uninstall my-package
  cd /path/to/source
  pip install -e .
  ```
- Use `pip list | grep my-package` to verify it points to a **path**, not just a version.

---

## 3. The Inspector Tool

### Official Docs Say:
- "Test with Inspector"

### Reality Check:
- We didn't use it today, but we should have.
- The Inspector (`npx @modelcontextprotocol/inspector`) runs your server in a web UI sandbox.
- **Why it's better:** It shows the *raw* JSON-RPC messages. If we had used it, we would have seen:
  ```
  Invalid JSON received: "FastMCP Banner..."
  ```
  ...instantly diagnosing the stdout pollution bug.

### Field Recommendation:
- Before trying it in Claude, try it in Inspector:
  ```bash
  npx @modelcontextprotocol/inspector python -m mcp_server_nucleus
  ```

---

## 4. Environment Variables & Hard Resets

### Official Docs Say:
- "Verify environment"

### Reality Check:
- MCP servers in Claude are long-lived processes.
- Changing `mcp_config.json` doesn't always restart them cleanly if they are hung.
- `pkill -f mcp_server_nucleus` is your friend.
- **Cold Start Testing:** Requires 100% certainty that the env var `NUCLEAR_BRAIN_PATH` actually changed. You can't verify this easily inside Claude.
- **Fix:** Add a "Verify Config" tool or log the config on startup (to your file log).

---

## Summary Checklist for Broken MCP Servers

1. **Is `stdout` clean?** (No prints, no banners)
2. **Where is code running from?** (`pip list`)
3. **Are logs writing to a file?** (`/tmp/mcp_debug.log`)
4. **Is the process actually dead?** (`ps aux | grep mcp`)
5. **Did I try the Inspector?** (Standardizes the client)

---

*This guide stays in the Brain to prevent future debugging marathons.*
