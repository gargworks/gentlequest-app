# Glama.ai Submission Manifest: Nucleus MCP

## Short Description
The Sovereign Agent Control Plane.

## Full Description
Nucleus MCP provides the "Super-Sovereign" interface for AI agents. It gives your favorite LLM (Claude, ChatGPT, etc.) a Task Ledger (Brain), a cryptographic Audit Log, a Hypervisor for resource security, and long-term memory via Engrams.

This server is designed for power-users who want to move beyond simple chat and into autonomous, secure agentic workflows.

## Source Code
[https://github.com/eidetic-works/mcp-server-nucleus](https://github.com/eidetic-works/mcp-server-nucleus)

## Configuration
**NPM (Recommended):**
```json
{
  "command": "npx",
  "args": ["-y", "@nucleus-os/nucleus-mcp"]
}
```

**Python (Manual):**
```json
{
  "command": "python",
  "args": ["-m", "mcp_server_nucleus"]
}
```

## Features
- **Brain Toolset:** Manage a persistent task ledger with priority and skill requirements.
- **Hypervisor:** Lock/Unlock sensitive files and monitor system health from within the chat.
- **Engrams:** Give your agent long-term memory that survives across threads.
- **Audit System:** View a cryptographic log of all high-privilege interactions.
