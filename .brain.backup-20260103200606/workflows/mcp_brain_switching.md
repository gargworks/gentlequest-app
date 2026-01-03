# MCP Brain Switching Protocol
> **Purpose:** One-command switch between Production (Warm) and Testing (Cold) brains vs Dogfood Thread.
> **Last Updated:** December 28, 2025

---

## ⚡️ The One-Button Way

We have automated the process. Run the helper script:

### 1. Switch to Warm Production Brain
*(Use this for real GentleQuest development)*

```bash
python scripts/switch_brain.py warm
```

### 2. Switch to Cold Empty Brain
*(Use this for 'Dogfood Thread' clean slate testing)*
**WARNING:** This DELETES data in the `dogfood-brain` folder to give you a truly fresh start.

```bash
python scripts/switch_brain.py cold
```

---

## What the Script Does

1.  **Kills Processes:** Runs `pkill -f mcp_server_nucleus` to stop old servers.
2.  **Updates Config:** Edits `mcp_config.json` to point `NUCLEAR_BRAIN_PATH` to the correct folder.
3.  **Cleans Data (Cold only):** Wipes the test directory for a fresh start.

---

## ⚠️ Critical Final Step

**You MUST Restart Antigravity/Claude** after running the script.
The IDE loads the config only at startup. The script cannot do this for you.

---

## Brain Locations

| Mode | Path | Purpose |
|------|------|---------|
| **Warm** | `/Users/lokeshgarg/ai-mvp-backend/.brain` | **Real Work.** Contains your project history, roadmap, and memories. |
| **Cold** | `/Users/lokeshgarg/dogfood-brain/.brain` | **Testing.** A disposable playground. The script wipes this clean on every switch! |

---

## Troubleshooting

If the script fails:
1. Check `mcp_config.json` structure.
2. Ensure you have permissions.
3. Fallback to manual steps (see `archive/old_mcp_switching.md` if needed).
