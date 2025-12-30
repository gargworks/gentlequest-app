# Nucleus Development Modes Matrix
> **Purpose:** The Definitive Guide to "How We Work" in different scenarios.
> **Date:** December 29, 2025

This matrix defines the correct configuration for each type of work.

| **Work Mode** | **Goal** | **Installation** (`pip`) | **Brain Path** (`env`) | **Orchestration** | **Stdout Rule** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. GentleQuest Development**<br>*(Regular Work)* | Build features for the main app using our tools. | **Editable**<br>`pip install -e /path/to/nucleus` | **Warm / Production**<br>`ai-mvp-backend/.brain` | **MCP Config**<br>Via `mcp_config.json` | **STRICTLY CLEAN**<br>No prints. File logging only. |
| **2. Dogfood / Cold Test**<br>*(MCP QA)* | Verify Nucleus works on a fresh install/empty state. | **Editable**<br>`pip install -e /path/to/nucleus` | **Cold / Dogfood**<br>`dogfood-brain/.brain` | **MCP Config**<br>Via `mcp_config.json` | **STRICTLY CLEAN**<br>No prints. File logging only. |
| **3. MCP Server Development**<br>*(Building the Tool)* | Change Nucleus core logic (e.g. fix bugs, add tools). | **Editable**<br>`pip install -e .` | **Unit Test Mocks**<br>(No real brain needed for unit tests) | **Local Script**<br>Run `python -m mcp_server_nucleus` via Inspector | **Loose**<br>Prints ok allowed ONLY if isolated in debug script. |
| **4. Public User Usage**<br>*(Future State)* | How others will use Nucleus. | **Standard**<br>`pip install mcp-server-nucleus` | **User's Choice**<br>`/path/to/their/project/.brain` | **MCP Config**<br>Standard Claude/Antigravity setup | **Clean**<br>Logs via stderr. |

---

## The Columns Explained

### 1. Work Mode
- **GentleQuest Dev:** You are "Lokesh the App Developer". You use Nucleus to help you think.
- **Dogfood/Cold:** You are "Lokesh the Tester". You try to break Nucleus on a fresh machine simulation.
- **MCP Dev:** You are "Lokesh the Tool Builder". You are editing `__init__.py` in Nucleus.

### 2. Installation Mode
- **Editable (`-e`)**: A symlink. Edits to source take effect immediately (after restart). **WE USE THIS 99% OF THE TIME.**
- **Standard**: A copy. Edits to source are ignored. Only for public users.

### 3. Brain Path
- **Warm (`ai-mvp-backend/.brain`)**: Your precious data. Real memories.
- **Cold (`dogfood-brain/.brain`)**: Disposable. Wiped clean by `switch_brain.py dogfood`.

### 4. Orchestration
- **MCP Config**: The `mcp_config.json` file controls the environment. Requires **RESTART** to change.
- **Local Agents**: Multiple threads (Researcher, Critic, etc.) orchestrated via the Brain's generic state.

### 5. Stdout Hygiene
- **The Rule:** MCP communicates via `stdin/stdout`.
- **The Danger:** `print("DEBUG")` -> sends text to Claude -> Claude tries to parse as JSON -> **CRASH**.
- **The Fix:** ALWAYS write logs to a file (`/tmp/mcp_debug.log`) or use `sys.stderr`.

### 6. The "Dev MCP" Concept
**You are always running the "Dev" version.**
Because of the **Editable Install**, your "nucleus" server is pointing to your local source code.
- **You:** Can add experimental tools, debug logs, or internal hacks to `src/`.
- **Public:** Will only see what you explicitly publish to PyPI.
- **Advantage:** You can use your own "God Mode" tools while testing the public features in the same codebase.

---

## Helper Scripts

| Task | Command |
| :--- | :--- |
| **Switch to Mode 1 (Work)** | `python scripts/switch_brain.py warm` + **Restart** |
| **Switch to Mode 2 (Test)** | `python scripts/switch_brain.py dogfood` + **Restart** |
| **Verify Install Mode** | `pip list \| grep nucleus` (Look for path on right) |
| **Watch Logs** | `tail -f /tmp/mcp_debug.log` |
