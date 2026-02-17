# Nucleus MCP Repository Status Report

**Generated**: Feb 17, 2026 12:42 AM IST (v1.0.5 Stability Check)

---

## Public Repository: nucleus-mcp

**URL**: https://github.com/eidetic-works/nucleus-mcp

### ✅ Author Attribution Fixed
- ALL commits now show: **"Nucleus Team <hello@nucleus-mcp.com>"**
- Local git config set for future commits
- No personal names anywhere in history

### Files (17 total)
```
.github/workflows/ci.yml
.gitignore
CHANGELOG.md
CODE_OF_CONDUCT.md
CONTRIBUTING.md
DEVELOPMENT.md
LICENSE
README.md
SECURITY.md
docs/DEMO_SCRIPT.md
examples/basic_usage.py
pyproject.toml
src/mcp_server_nucleus/__init__.py
src/mcp_server_nucleus/__main__.py
src/mcp_server_nucleus/cli.py
tests/__init__.py
tests/test_core.py
```

### Git Status
- **Commits**: 8 (all by "Nucleus Team")
- **Branches**: main, dev (synced)
- **Tags**: v1.0.5 (points to latest commit)
- **Remote**: origin → github.com/eidetic-works/nucleus-mcp
- **CI Status**: ✅ Passing
- **Author**: Nucleus Team <hello@nucleus-mcp.com>

### GitHub Features
- ✅ Issues enabled (5 starter issues created)
- ✅ Discussions enabled
- ✅ Release v1.0.5 published
- ✅ Topics: mcp, ai-agents, cursor, claude, windsurf, memory-sync

### Protection Mechanisms
1. **`.gitignore`** blocks internal docs patterns:
   - `docs/*LAUNCH*.md`
   - `docs/*STRATEGY*.md`
   - `*_INTERNAL.md`, `*_PRIVATE.md`
   - `GTM*.md`, `OUTREACH*.md`

2. **Pre-commit hook** rejects forbidden files

3. **Author attribution**: "Nucleus Team" (no personal names)

---

## PyPI Package

**URL**: https://pypi.org/project/nucleus-mcp/

- **Version**: 1.0.5
- **Install**: `pip install nucleus-mcp`
- **CLI**: `nucleus-init`
- **Status**: ✅ Working

### Exported Functions
- `brain_health` - Health check
- `brain_write_engram` - Store memory
- `brain_query_engrams` - Query memories
- `brain_get_state` / `brain_set_state` - State management
- `brain_sync_now` / `brain_sync_status` - Sync operations
- `hypervisor_status` - Security status
- `lock_resource` / `unlock_resource` - File locking
- `watch_resource` - File monitoring
- `brain_audit_log` - Audit logging
- `brain_identify_agent` - Agent identification
- `brain_list_artifacts` - List artifacts

---

## Internal Monorepo: mcp-server-nucleus

**URL**: https://github.com/eidetic-works/mcp-server-nucleus
**Visibility**: 🔒 PRIVATE

- Contains GentleQuest and internal development code
- NOT for public use
- README points to public nucleus-mcp repo

---

## Internal Docs Location

**Path**: `/Users/lokeshgarg/ai-mvp-backend/nucleus-launch-internal/`

**Contents**:
- `MASTER_LAUNCH.md` - Consolidated launch guide
- `REDDIT_LAUNCH.md` - Reddit posts
- `HACKER_NEWS.md` - HN strategy
- `TWITTER_LAUNCH.md` - Twitter thread
- `PRODUCT_HUNT.md` - PH listing
- `MCP_COMMUNITY.md` - Community outreach
- `SOCIAL_PREVIEW.md` - Image specs
- `PYPI_PUBLISH.md` - Publishing guide
- `LAUNCH_CHECKLIST.md` - Checklist
- `README.md` - Index

---

## Launch Readiness

### ✅ Complete
- Clean open source repo
- PyPI package published
- GitHub configured (issues, discussions, release)
- Internal docs separated
- Protection mechanisms in place
- Dev workflow documented

### 🔲 Before Launch
- [ ] Create social preview image (1280x640)
- [ ] Upload to GitHub settings
- [ ] Submit PR to awesome-mcp-servers

### ⏰ Launch Sequence
1. **Reddit** (r/LocalLLaMA first)
2. **Twitter/X** (2-3 hours after)
3. **Hacker News** (Day 2)
4. **Product Hunt** (Week 2, if momentum)

**Optimal Time**: Tuesday-Thursday, 9-11am PST

---

## Quick Commands

```bash
# Clone and work
git clone https://github.com/eidetic-works/nucleus-mcp.git
cd nucleus-mcp
git checkout dev
git checkout -b feature/my-feature

# Test installation
pip install nucleus-mcp
nucleus-init --version

# View internal launch docs
ls /Users/lokeshgarg/ai-mvp-backend/nucleus-launch-internal/
```

---

**Status**: 🚀 READY FOR LAUNCH
