# 🦅 Master Execution Plan: The "How-To" of Sovereignty

**Status**: `.env` has been auto-patched by Antigravity.
**Objective**: Synchronize all terminals and tools to the v0.7.1 Protocol.

---

## 🖥️ Step 1: Terminal / Shell (The Foundation)
I have updated your `/Users/lokeshgarg/ai-mvp-backend/.env` with **Base Infrastructure** (Path + Token).
*   **Identity**: Defaults to `terminal_user`.
*   **Path**: Defaults to Root Workspace.

**Run this in your terminal:**
*(Note: This is for Terminal scripts only. Windsurf ignores this file.)*
```bash
source .env
echo $NUCLEUS_BETA_TOKEN
# Expected Output: titan-sovereign-godmode
```

---

## 🏄 Step 2: Windsurf / Cursor (The Daily Driver)
Your IDE needs to know the secrets. Update your `settings.json` or "MCP Server" configuration block.

**Copy-Paste this Block:**
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
```
*Note: This enables "Cross-Project Synthesis".*

**Identity Matrix (Choose One):**
*   **Primary (Recommended)**: `"NUCLEUS_AGENT_ID": "windsurf_opus_titan"` (The Surgeon / God Mode)
*   **Alternate (Strict Role)**: `"NUCLEUS_AGENT_ID": "windsurf_product"` (Pure GentleQuest Builder)
*   **Why?**: The Strategy assigns Windsurf as the "Product Surgeon". Use Primary unless you want strict separation in logs.


---

## 🦅 Step 3: Antigravity (The Architect)
Antigravity does not read `.env` automatically in all contexts. You must **Declare Identity** at the start of a thread.

**For this thread (`antigravity_core`), you are already set.**
For new threads, paste the prompt from **[ANTIGRAVITY_SETUP_GUIDE.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/b95f3ae4-2e33-4132-a8c3-8ecf4024f5ae/ANTIGRAVITY_SETUP_GUIDE.md)**:

*   **Audit/Strategy**: Paste "Red Team Protocol"
*   **Coding/Product**: Paste "Blue Team Protocol"

4.  **Confirm Identity**: `brain_identify_agent` is called automatically by the prompt.

### ⚡ How Red Teaming Works (Without Config Edits)
**You do NOT need to edit files to switch Antigravity roles.**
The **Startup Prompts** (Step 3) do the magic.

*   When you paste the "Red Team Prompt", Antigravity reads "Identity: antigravity_core".
*   Antigravity then calls the tool `brain_identify_agent("antigravity_core")`.
*   This **dynamically overwrites** the default identity for that session.

**Windsurf stays fixed. Antigravity shapeshifts.**


---

## ✅ Verification Checklist
1.  [ ] Terminal: `echo $NUCLEAR_BRAIN_PATH` shows `/Users/lokeshgarg/ai-mvp-backend`.
2.  [ ] Windsurf: Restart MCP server. Check logs for "Titan Token Accepted".
3.  [ ] Antigravity: Create a new file in Windsurf. Ask Antigravity "Did you see the new file?".

**System is Ready.**
