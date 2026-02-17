# 🗺️ Nucleus Version Reconciliation Map (SSoT: v1.0.7)

To avoid versioning amnesia and 403 errors, we have established a **Single Source of Truth (SSoT)**. 

## 🛡️ The Sentinel Protocol
All versions are now managed by the **Sentinel Engine**. There is no need for manual edits across the 10+ manifest files.

### 1. Update the Source of Truth
Edit the version and codename in:
`file:///Users/lokeshgarg/ai-mvp-backend/.registry/version.json`

### 2. Execute the Global Strike
Run the sync script from the root:
```bash
python3 scripts/sync_registry.py
```

## 📍 Automated Targets
The Sentinel Engine automatically patches:
- **PyPI**: `mcp-server-nucleus/pyproject.toml`
- **NPM (Root)**: `nucleus-mcp/package.json` & `package.json.real`
- **NPM (Wrapper)**: `mcp-server-nucleus/npm-wrapper/package.json`
- **Landing Page**: `nucleus-landing/src/App.jsx` (Header & Walkthrough)
- **Source Code**: `mcp_server_nucleus/__init__.py`
- **Registry Manifests**: `glama.json`, `pulsemcp.json`, `smithery.json`
- **Documentation**: Syncs badges in root `README.md`

## 🚀 Release Checklist
1. Update `.registry/version.json`.
2. Run `python3 scripts/sync_registry.py --dry-run`.
3. Run `python3 scripts/sync_registry.py --release` (Auto-commits and tags).
4. `npm publish` in `nucleus-mcp/`.
5. `twine upload dist/*` in `mcp-server-nucleus/`.

**Status**: HARDENED. 🛡️
