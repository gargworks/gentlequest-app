---
description: Pre-release checklist for Nucleus MCP Server
---

# Nucleus MCP Server Release Protocol

## Pre-Release Checklist

// turbo-all

### 1. Version Bump
```bash
# Update version in pyproject.toml
cd mcp-server-nucleus
grep version pyproject.toml
```

### 2. Run Tests
```bash
# Verify all modules compile
python3 -m py_compile src/mcp_server_nucleus/__init__.py
python3 -m py_compile src/mcp_server_nucleus/runtime/*.py
```

### 3. Test Core Functions
```bash
export NUCLEAR_BRAIN_PATH=/path/to/.brain
python3 -c "from mcp_server_nucleus import brain_satellite_view; print(brain_satellite_view())"
```

### 4. Build Package
```bash
cd mcp-server-nucleus
python3 -m build
```

### 5. Test Install Locally
```bash
pip3 install --force-reinstall dist/*.whl
nucleus-init --help
```

### 6. Publish to PyPI
```bash
python3 -m twine upload dist/*
```

### 7. Tag Release
```bash
git tag -a v0.X.X -m "Release v0.X.X"
git push origin v0.X.X
```

## Post-Release
- [ ] Update CHANGELOG.md
- [ ] Test fresh install from PyPI
- [ ] Update Claude Desktop config if needed
