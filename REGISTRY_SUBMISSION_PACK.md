# Nucleus MCP Registry Submission Pack

This document contains the metadata and instructions for listing Nucleus MCP across the major MCP registries.

## 1. Official MCP Registry (modelcontextprotocol/registry)
## 1. Official MCP Registry (modelcontextprotocol/registry)
**Status**: COMPLETED ✅
**Note**: Submitted and verified. PulseMCP has ingested the changes.

### PR Metadata (JSON)
Following the `server.schema.json` pattern:

```json
{
  "name": "Nucleus MCP",
  "description": "The Sovereign Agent Control Plane with Governance & Engrams.",
  "repository": {
    "url": "https://github.com/eidetic-works/nucleus-mcp",
    "source": "github"
  },
  "packages": [
    {
      "type": "pypi",
      "package": "nucleus-mcp"
    }
  ],
  "tags": ["governance", "memory", "agent-control-plane", "sovereign"]
}
```

---

## 2. Smithery.ai
**Status**: PENDING VERIFICATION
**Issue**: The slug `nucleus-mcp` is "taken" but the server isn't appearing in public search yet.
**Action**:
- Install the [Smithery GitHub App](https://smithery.ai/docs/build/publish#github-app) on the repository.
- This will automatically trigger a build from the `pyproject.toml`.

---

## 3. mcp-get.com (PR #168)
**Status**: FAILING (Package Validation)
**Issue**: The PR check fails because `nucleus-mcp` is not found on PyPI.
**Action**: Publish the package to PyPI.

### PyPI Publication Steps (Local)
1. Ensure `hatch` or `twine` is installed.
2. Build the package:
   ```bash
   cd mcp-server-nucleus
   hatch build
   ```
3. Publish (requires PyPI Token):
   ```bash
   hatch publish
   ```
   *Note: Once published, the mcp-get PR will automatically pass on the next retry.*

---

## 4. PulseMCP & MCP Market
- **MCP Market**: LIVE.
- **PulseMCP**: No action needed; it will automatically ingest Nucleus once the **Official Registry** PR is merged.
