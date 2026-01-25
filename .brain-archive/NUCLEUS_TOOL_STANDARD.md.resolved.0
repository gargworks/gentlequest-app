
# Nucleus Tool Standard (RFC 2026-01)

**Status:** Draft
**Context:** Phase 20 (Tool Marketplace)

## 1. Philosophy
Nucleus Tools are **Standalone Capabilities**.
They are not "scripts"; they are "micro-apps" that extend the Agent's body.
They must be:
- **Discoverable:** Self-describing via `manifest.json`.
- **Installable:** `nucleus install <tool_name>`.
- **Composable:** Can call other tools.

## 2. Directory Structure
All tools live in `<project_root>/tools/`.
Each tool is a self-contained folder:

```text
tools/
  brain_analyze_sentiment/
    __init__.py
    manifest.json       # Metadata & Permissions
    src/
        main.py         # Entry point (must expose @mcp.tool)
        logic.py
    tests/
    README.md
```

## 3. The Manifest (`manifest.json`)
Every tool must describe itself to the Nucleus OS.

```json
{
  "name": "brain_analyze_sentiment",
  "version": "1.0.0",
  "description": "Analyze emotional tone of user messages.",
  "author": "Nucleus Core Team",
  "capabilities": ["read_file", "llm_generate"],
  "entry_point": "src.main:analyze_sentiment"
}
```

## 4. The Interface
Tools must use the `mcp-server-nucleus` SDK (or FastMCP) to expose functions.
They must follow the naming convention `brain_<verb>_<noun>`.

```python
# tools/brain_analyze_sentiment/src/main.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Sentiment Analyzer")

@mcp.tool()
def brain_analyze_sentiment(text: str) -> str:
    """Analyze the sentiment of the text."""
    # Logic here
    return "POSITIVE"
```

## 5. Security & Isolation
- Tools run in the MCP Server process but are logically isolated.
- Future: Run in separate Docker containers (Phase 21).

## 6. Implementation Plan
1.  **Registry:** `tools/registry.json` will track installed tools.
2.  **Loader:** `mcp-server-nucleus` will dynamically load tools listed in Registry on startup.
3.  **Scaffolder:** A script to generate this structure.
