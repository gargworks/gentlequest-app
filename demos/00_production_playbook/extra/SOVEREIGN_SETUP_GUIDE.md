# 🏛️ Nucleus Sovereign OS: The Chairman's Protocol (v0.7.1)

**Classification**: TITAN / DARK WHEEL  
**Authorized**: Chairman (Lokesh Garg), Boss Opus  
**Context**: Full Cross-Project Orchestration (GentleQuest + Bereave it Bot + Nucleus)

## 1. The "God Mode" Environment
Unlike the public setup, we do NOT scope to `.brain`. We scope to the **Root Workspace** to enable Cross-Project Synthesis.

### Critical Environment Variables
```bash
# 1. Cross-Project Scope (The "Parent" Path)
# Allows reading GentleQuest/Bereave artifacts from one brain.
export NUCLEAR_BRAIN_PATH="/Users/lokeshgarg/ai-mvp-backend"

# 2. The Titanium Bypass
# Unlocks 150+ tools, bypassing the friction gate.
export NUCLEUS_BETA_TOKEN="titan-sovereign-godmode"

# 3. Sovereign Identity (v0.7.1)
# Updates automatically based on the agent (e.g. "windsurf_godmode")
export NUCLEUS_AGENT_ID="antigravity_titan"

# 4. Silence is Golden (Protocol Stability)
export FASTMCP_SHOW_CLI_BANNER="False"
export FASTMCP_LOG_LEVEL="WARNING"
```

## 2. Review: The Golden Config (v0.7.1)
Your master config at `.brain/config/nucleus.yaml` has been Hardened:
*   **Sync Mode**: `auto` (2s latency) guarantees "Thought-Speed" updates.
*   **Hygiene**: `v0.7.1` Auto-Patching is active.
*   **Orchestration**: Collision Detection is active.

## 3. IDE Configuration (MCP Settings)

### 🏄 Windsurf / Cursor (The Daily Driver)
Update your MCP config to inject the Titan token:

```json
{
  "mcpServers": {
    "nucleus": {
      "command": "python3",
      "args": ["-m", "mcp_server_nucleus"],
      "env": {
        "NUCLEUS_BETA_TOKEN": "titan-sovereign-godmode",
        "NUCLEAR_BRAIN_PATH": "/Users/lokeshgarg/ai-mvp-backend",
        "NUCLEUS_AGENT_ID": "windsurf_opus_titan",
        "FASTMCP_SHOW_CLI_BANNER": "False",
        "FASTMCP_LOG_LEVEL": "WARNING"
      }
    }
  }
}
```

### 🧠 Claude Desktop (The Analyst)
identical config, but set `NUCLEUS_AGENT_ID` to `claude_desktop_titan`.

## 4. Operational Mandates
1.  **Never commit `events.jsonl`**: The `.gitignore` patch handles this, but verify execution.
2.  **Cross-Project Reads**: You can now use `brain_read_file` to access `GentleQuest/README.md` because your scope is the parent root.
3.  **The "Kill Switch"**: If sync goes haywire, delete `.brain/.sync.lock` manually.

**Sovereignty is absolute.**
