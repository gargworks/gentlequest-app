---
description: Install and update Nucleus MCP Server package
---

# Update Nucleus Package

## Steps

// turbo
1. Create virtual environment (if not exists):
```bash
python3 -m venv /tmp/nucleus_venv
```

// turbo
2. Activate and install:
```bash
source /tmp/nucleus_venv/bin/activate && pip install -e ./mcp-server-nucleus
```

// turbo
3. Verify installation:
```bash
python3 -c "from mcp_server_nucleus import brain_file_changes, brain_gcloud_status; print('Nucleus v0.5.0 OK')"
```

## Current Version
- **Package:** `mcp-server-nucleus`
- **Version:** `0.5.0`
- **New Features:**
  - `brain_file_changes` - File watching for native sync
  - `brain_gcloud_status` - GCloud auth status
  - `brain_gcloud_services` - Cloud Run service listing

## Dependencies
- `fastmcp`
- `pydantic`
- `watchdog>=3.0.0`
