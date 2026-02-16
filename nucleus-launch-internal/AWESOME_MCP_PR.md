# awesome-mcp-servers PR Template

## Fork & Clone
```bash
# Fork https://github.com/punkpeye/awesome-mcp-servers first on GitHub
git clone https://github.com/YOUR_USERNAME/awesome-mcp-servers.git
cd awesome-mcp-servers
```

## Find Section
Open `README.md` and find the `🧠 Knowledge & Memory` section.

## Add Entry
Add this line in alphabetical order (after entries starting with 'e'):

```markdown
- [eidetic-works/nucleus-mcp](https://github.com/eidetic-works/nucleus-mcp) 🐍 🏠 🍎 - Cross-platform memory sync for Cursor, Claude Desktop, and Windsurf. One brain across all MCP-compatible AI tools with persistent engrams, multi-agent sync, and audit logging.
```

## Commit & Push
```bash
git add README.md
git commit -m "Add eidetic-works/nucleus-mcp to Knowledge & Memory"
git push origin main
```

## Create PR

### Title
```
Add eidetic-works/nucleus-mcp to Knowledge & Memory
```

### Description
```markdown
## New Server: nucleus-mcp

**Repository**: https://github.com/eidetic-works/nucleus-mcp
**PyPI**: https://pypi.org/project/nucleus-mcp/
**Category**: 🧠 Knowledge & Memory

### What it does
Nucleus MCP provides cross-platform memory sync for AI coding tools. It enables:
- **Cross-platform sync** between Cursor, Claude Desktop, Windsurf, and any MCP client
- **Persistent engrams** (memories) that survive across sessions
- **Multi-agent sync** with conflict detection
- **Audit logging** for all operations
- **Hypervisor security** layer

### Why it belongs in Knowledge & Memory
Unlike single-platform memory solutions, Nucleus specifically solves the problem of syncing context across DIFFERENT AI tools. It's the "universal brain" that connects all MCP-compatible clients.

### Installation
```bash
pip install nucleus-mcp
nucleus-init
```

### License
MIT

### Checklist
- [x] Link is valid and working
- [x] Description is concise
- [x] Correct category (Knowledge & Memory)
- [x] Icons are accurate (🐍 Python, 🏠 Local, 🍎 macOS)
- [x] Open source (MIT license)
```

## After PR Submitted
1. Monitor for maintainer feedback
2. Respond quickly to any requests
3. Update our status once merged
