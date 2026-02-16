# Anthropic MCP Registry Submission

**Service Name**: Nucleus MCP
**Description**: The Sovereign Agent Control Plane. Nucleus provides a unified memory layer (engrams) for AI agents across multiple platforms (Cursor, Claude Desktop, Windsurf). It ensures context continuity while maintaining local data sovereignty.

## Capabilities
- **Universal Sync**: Shared `.brain` folder for seamless handoffs between local IDEs and desktops.
- **Engram Storage**: Persistent, high-intensity memory storage with context-aware querying.
- **Sovereign Governance**: Cryptographic interaction logs and local-first data isolation.
- **Hypervisor Control**: Managed file/resource locking for agent safety.

## Installation
```bash
pip install nucleus-mcp
nucleus-init --scan
```

## JSON Configuration (Claude Desktop)
```json
{
  "mcpServers": {
    "nucleus-mcp": {
      "command": "python3",
      "args": ["-m", "mcp_server_nucleus"]
    }
  }
}
```

**GitHub**: [https://github.com/eidetic-works/nucleus-mcp](https://github.com/eidetic-works/nucleus-mcp)
**License**: MIT
**Author**: Nucleus OS
