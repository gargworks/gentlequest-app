# Installer Strategy Reassessment

> **Question:** Is a dedicated installer (`nucleus-setup`) the right move? Or is it over-engineering?

---

## 🔬 First Principles Analysis

**Goal:** Reduce friction. Users want to use the tool, not configure it.
**User State:** They just `pip install`ed the package. They are at the command line.

### Option A: dedicated installer (`nucleus-setup`)
*   **Pros:** One command sets up everything. "It just works."
*   **Cons:** Hard to maintain. JSON parsing is fragile. What if Windsurf changes config location? What if user has complex existing config?
*   **Risk:** "It broke my existing config" = Critical failure.

### Option B: Built-in `nucleus init` enhancement
*   **Idea:** `nucleus init` already exists. Why make a separate command?
*   **Flow:**
    ```bash
    nucleus init
    > initializing brain... done.
    > Detect: Found Claude Desktop. Configure? [Y/n]
    > Detect: Found Cursor. Configure? [Y/n]
    ```
*   **Pros:** Integrated flow. One entry point.

### Option C: Manual Documentation (Status Quo)
*   **Pros:** Zero risk of breaking config. User learns how it works.
*   **Cons:** High friction. "Edit this JSON file" scares 50% of users.
*   **Reality:** Most users will bounce if they have to edit JSON manually.

---

## ⚠️ The "Config Merge" Problem

Automating config updates is dangerous.
User's existing config:
```json
{
  "mcpServers": {
    "git-mcp": {...},
    "postgres": {...} // Customized
  }
}
```

If we overwrite this → Disaster.
If we parse it wrongly (comments in JSON, trailing commas) → Disaster.

**Constraint:** JSON does not support comments, but many users (and VSCode) allow comments in configuration files (JSONC). `json.load()` fails on JSONC.

---

## 🎯 Recommendation: The Hybrid "Safe" Approach

**Don't build a full installer yet.** It's a rabbit hole of edge cases (Windows paths, JSONC parsing, permission errors).

**Instead: The "Copy-Paste" Generator**

Update `nucleus init` to **generate the configuration snippet** but not write it.

**New Flow:**
```bash
$ nucleus init
...
✅ Brain initialized at /Users/lokesh/my-brain

 👇 ADD THIS TO YOUR CONFIG:

  "nucleus-brain": {
    "command": "python3.11",
    "args": ["-m", "mcp_server_nucleus"],
    "env": {
      "NUCLEAR_BRAIN_PATH": "/Users/lokesh/my-brain"
    }
  }

 📍 Config Locations:
    Claude: ~/Library/Application Support/Claude/claude_desktop_config.json
    Cursor: ~/.cursor/mcp.json
```

**Why this is better:**
1.  **Zero Risk:** We never touch their files.
2.  **Educational:** They see what's being added.
3.  **Universal:** Works for any client (even ones we don't know).
4.  **Low Effort:** We can ship this in 10 minutes.

---

## 🏁 Verdict

**Do NOT build `nucleus-setup` or auto-config writers right now.**
It introduces:
1.  Parsing risks (JSON vs JSONC)
2.  OS-specific path complexity
3.  "You broke my setup" liability

**INSTEAD:** 
Modify `nucleus init` to print the **exact JSON snippet** with the correct absolute path pre-filled. This solves 90% of the friction (finding the path + writing the JSON) without the risk.
