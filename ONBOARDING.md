# 🚀 Nucleus Onboarding: Zero-Friction Setup

Welcome to the Sovereign Age. To ensure your development environment is coherent, isolated, and "Strike Ready," we standardize on [uv](https://github.com/astral-sh/uv) — the extremely fast Python package and project manager.

## 1. The Global Coherence Check
`pip install` is universal, but modern systems have "Sovereignty Guards" that can block it.

### Your Installation Matrix:

#### 🟢 macOS & Windows
`pip install nucleus-mcp` usually works out of the box. 
**Pro-tip**: Use `uv tool install nucleus-mcp` to avoid path confusion between `python` and `python3`.

#### 🟡 Modern Linux (Ubuntu 23.04+, Debian 12+)
These systems block `pip install` to global directories.
**The Fix**: Use `pipx install nucleus-mcp`. 
*If you don't have pipx: `sudo apt install pipx && pipx ensurepath`.*

#### 🔴 Experimental / Pro (Active Specialists)
If you have multiple Python versions (like 3.14-dev) or manage multiple AI projects:
**The Fix**: Use `uv tool install nucleus-mcp`. It is the only tool that guarantees your GentleQuest environment stays virgin while Nucleus runs in a hardened silo.

---

## 2. Developer Setup (Strike Ready)

If you have `uv` installed, setting up Nucleus takes seconds:

```bash
# 1. Clone the repo
git clone https://github.com/eidetic-works/nucleus-mcp.git
cd nucleus-mcp

# 2. Sync dependencies and create an isolated venv
uv sync

# 3. Run tests
uv run pytest
```

---

## 3. How to Build & Publish

Avoid using `python -m build` or `twine`. `uv` handles the entire pipeline. Always run this from the package directory:

```bash
# 1. Enter the server directory
cd mcp-server-nucleus

# 2. Clear stale builds
rm -rf dist/*

# 3. Build the package
uv build

# 4. Publish to PyPI
# Username: __token__
# Password: <pypi-token>
uv publish dist/*
```

---

## 4. User Installation (Coherence)

For users who just want to use the MCP server, the recommended way is still `pip install`, but if they experience versioning friction (like the Python 3.14 issue), suggest `uvx`:

```bash
# Run Nucleus directly without installation
uvx nucleus-mcp
```

## 5. Troubleshooting "Context Amnesia"
If you see errors like `No module named build` or `python command not found`:
1. **Check UV**: `uv --version`
2. **Re-sync**: `uv sync`
3. **Use UV Run**: prefix your commands with `uv run` (e.g., `uv run python scripts/sync_registry.py`).

**Welcome to the Vanguard. Let's build the shared brain.** 🧠🛡️
