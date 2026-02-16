# 🚀 Walkthrough: Nucleus v1.0.5 "The Poison Pill"

The "Poison Pill" has been released. Nucleus is now the **first** MCP control plane to support **Recursive Mounting**, establishing a new standard for the "Internet of Agents."

## ✨ Changes Made

### 🔗 Recursive Mounting & Discovery
- **New Tool**: `brain_mount_server` enables mounting external MCP servers at runtime.
- **Recursive Discovery**: `brain_traverse_and_mount` allows automatic expansion of the agent network.
- **Namespacing**: Seamless integration via `mount_id:tool_name` syntax.

### 💾 Persistence Layer
- **Persistent Mounts**: Added `mounts.json` to store configurations.
- **Auto-Restoration**: Implementation of `restore_mounts()` ensures connections are re-established on server restart.

### 🛠️ CLI Enhancements
- **Command**: `nucleus mount` added for manual management.
- **Subcommands**: `list`, `add`, `remove`.
- **Bug Fix**: Refactored argument parsing to resolve collisions between subparser and command arguments.

### 📦 Release Status
- **PyPI Package**: [nucleus-mcp 1.0.5](https://pypi.org/project/nucleus-mcp/1.0.5/)
- **Strategy**: Established the "Browser for agents" narrative through `PROTOCOL_SPEC.md` and `ECOSYSTEM.md`.

## ✅ Verification Results

| Requirement | Test Method | Result |
|-------------|-------------|--------|
| Recursive Mounting | `verify_mounting.py` | ✅ Success |
| Persistence | `test_mount_cli.py` + manual check | ✅ Success |
| CLI Functionality | End-to-end `mount add` test | ✅ Success |
| PyPI Integrity | `twine check` | ✅ PASSED |

## 📦 Build Artifacts
Verified artifacts from the final build:
- `nucleus_mcp-1.0.5-py3-none-any.whl` (323K)
- `nucleus_mcp-1.0.5.tar.gz` (6.7M)

---
*Nucleus is now the stable anchor for your agentic ecosystem.*
