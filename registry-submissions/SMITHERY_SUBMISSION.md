# Smithery.ai Submission Manifest: Nucleus MCP

## Submission Workflow (ACTION REQUIRED)
1. **Prepare URL**: Copy the GitHub repository link: `https://github.com/eidetic-works/mcp-server-nucleus`
2. **Visit Smithery**: Open [smithery.ai/new](https://smithery.ai/new) in your browser.
3. **Submit**: Paste the GitHub/NPM link and follow the on-screen prompts. Smithery will automatically scan the repo for configuration details.
4. **Verify**: Once indexed, your server will appear in the Smithery registry for easy installation.

## Server Details
- **Name:** Nucleus MCP
- **Description:** Power-user tools for the Nucleus OS sovereign agent control plane. Includes Task Ledger (Brain), Hypervisor security controls, and long-term memory (Engrams).
- **GitHub:** [https://github.com/eidetic-works/mcp-server-nucleus](https://github.com/eidetic-works/mcp-server-nucleus)
- **Primary Transport:** Stdio (via Python or NPX)

## Installation Methods

### Command (NPX)
```bash
npx -y @nucleus-os/nucleus-mcp
```

### Command (Python)
```bash
python -m mcp_server_nucleus
```

## Configuration (Claude Desktop)
```json
{
  "mcpServers": {
    "nucleus": {
      "command": "npx",
      "args": [
        "-y",
        "@nucleus-os/nucleus-mcp"
      ]
    }
  }
}
```

## Capabilities
- **Tools:** `brain_add_task`, `hypervisor_status`, `write_engram`, `lock_resource`, etc.
- **Resources:** Governance status, Audit logs.
- **Prompts:** Interactive task management and security auditing.
