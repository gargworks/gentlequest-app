# MCP Package Development vs Distribution Guide

> **Author:** TECH-DIRECTOR  
> **Date:** December 28, 2025  
> **Context:** Lessons learned from Nucleus MCP dogfooding

---

## The Two Modes

| Mode | Command | Who Uses It | Purpose |
|------|---------|-------------|---------|
| **Standard Install** | `pip install mcp-server-nucleus` | Public users | Consumption |
| **Editable Install** | `pip install -e .` | You (developer) | Development |

---

## How Python Finds Your Package

When an MCP client runs:
```bash
python3.11 -m mcp_server_nucleus
```

Python searches for `mcp_server_nucleus` in this order:
1. Current directory (usually not found)
2. `sys.path` entries
3. Global `site-packages` (e.g., `/opt/homebrew/lib/python3.11/site-packages/`)

**Problem:** If you have BOTH a local folder AND a pip-installed copy, Python uses the pip copy and ignores your local edits.

---

## Standard Install (For Public Users)

**How it works:**
```bash
pip install mcp-server-nucleus
```

This downloads from PyPI and copies files to:
```
/opt/homebrew/lib/python3.11/site-packages/mcp_server_nucleus/
```

**Pros:**
- One-command setup
- No source code needed
- Easy updates (`pip install --upgrade`)
- Clean, isolated

**Cons:**
- Editing source has no effect (wrong copy being run)
- Must re-publish to PyPI for changes

**Use when:** You are a PUBLIC USER consuming someone else's MCP server.

---

## Editable Install (For Developers)

**How it works:**
```bash
cd /path/to/mcp-server-nucleus
pip install -e .
```

This creates a symlink in site-packages pointing to YOUR folder:
```
site-packages/mcp_server_nucleus.egg-link → /your/local/folder
```

**Pros:**
- Edit code → changes take effect immediately (after restart)
- Debug logging works
- Test new features before publishing
- Dogfood your own changes

**Cons:**
- Only works on YOUR machine
- "Pollutes" global Python with dev version
- Can confuse standard users if misconfigured

**Use when:** You are DEVELOPING the MCP server.

---

## The Chronology of Our Cold Start Bug

### What Happened

1. **Earlier:** You published v0.2.3 to PyPI
2. **At some point:** `pip install mcp-server-nucleus` was run (maybe as dependency)
3. **Today:** I edited local code to add debug logging
4. **Bug:** Python kept running the pip copy, not my edits
5. **Result:** Logs never appeared, couldn't diagnose crash

### The Fix

```bash
pip uninstall mcp-server-nucleus
cd /path/to/mcp-server-nucleus
pip install -e .
```

Now Python runs your local code.

---

## Why PyPI Still Matters

**For OTHER people (the public):**

A random developer finds Nucleus on GitHub:

```bash
# Easy installation
pip install mcp-server-nucleus

# Initialize
nucleus init

# Configure MCP client
# Add to mcp_config.json
```

They don't need your source folder. They just want it to work.

**Without PyPI:** Users would need to:
1. Clone your repo
2. Set up Python paths
3. Install dependencies manually
4. Manage updates by pulling git

**With PyPI:** One command, done.

---

## Quick Reference

### Am I in the right mode?

```bash
pip list | grep mcp-server-nucleus
```

**Standard install:**
```
mcp-server-nucleus    0.2.3
```

**Editable install:**
```
mcp-server-nucleus    0.2.3    /path/to/your/folder
```
(Note the path on the right)

### Switch to Editable Mode

```bash
pip uninstall mcp-server-nucleus
cd /path/to/mcp-server-nucleus
pip install -e .
```

### Switch Back to Standard Mode

```bash
pip uninstall mcp-server-nucleus
pip install mcp-server-nucleus
```

---

## Summary

| Question | Answer |
|----------|--------|
| Why does pip install exist? | Distribution to public users |
| Why editable install? | Your local development/testing |
| Which should I use? | Editable (you're the developer) |
| When do I use standard? | Never (unless testing PyPI release) |

---

*This is a Python packaging concept, not specific to MCP. But MCP makes it visible because the client runs `python -m package` directly.*
