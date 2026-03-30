# Nucleus v1.6.1 Hotfix Release Summary

**Date:** 2026-03-14  
**Type:** Critical Hotfix  
**Versions:** Python 1.6.1 (PyPI), npm 1.4.1 (npm)

---

## Critical Issue in v1.6.0

**Problem:** `anon_telemetry.py` shipped as a 46-line stub (docstring + imports only)

**Impact:**
- `record_anon_command()` function missing
- All telemetry calls from `_dispatch.py` and `cli.py` silently failed via `except Exception: pass`
- **Zero Python SDK users sent anonymous telemetry in v1.6.0**
- 2,316 Cloudflare Worker requests were likely from npm package, health checks, or pre-v1.6.0 installations

**Root Cause:** Implementation was accidentally stripped before v1.6.0 release

---

## Fix Applied

### Restored Full Implementation (328 lines)

**Functions restored:**
- `record_anon_command(command, category, duration_ms, error_type=None)` — Main entry point
- `shutdown_anon_telemetry(timeout=2.0)` — Flush pending spans before exit
- `show_first_run_notice()` — One-time privacy notice
- `reset_anon_telemetry_state()` — Config cache reset
- `is_anon_telemetry_enabled()` — Config priority chain (env > yaml > default)

**Technical Implementation:**
- Lightweight HTTP OTLP sender using `urllib.request` (no heavy dependencies)
- Fire-and-forget background threads (never blocks user workflow)
- Proper OTLP JSON span format with service name `nucleus-anon`
- Attributes: `nucleus.command`, `nucleus.category`, `nucleus.duration_ms`, `nucleus.version`, `python.version`, `os.platform`
- Config priority: `NUCLEUS_ANON_TELEMETRY` env var > `nucleus.yaml` > default (enabled)
- First-run marker: `.nucleus_telemetry_notice_shown`

### Verification

**Tested and verified:**
```
✅ Python SDK → localhost:4318 → OTel Collector → Jaeger
✅ Service "nucleus-anon" visible in Jaeger
✅ Spans with correct attributes (command, category, duration)
✅ Config priority chain working
✅ Fire-and-forget background threads
✅ Shutdown flush with timeout
```

**Test command:**
```python
from mcp_server_nucleus.runtime.anon_telemetry import record_anon_command, shutdown_anon_telemetry
record_anon_command('test.ping', 'validation', 42.0)
shutdown_anon_telemetry(timeout=10)
```

---

## Release Artifacts

**Built packages:**
- `dist/nucleus_mcp-1.6.1-py3-none-any.whl` (660 KB)
- `dist/nucleus_mcp-1.6.1.tar.gz` (77 MB)

**Version updates:**
- `pyproject.toml`: 1.6.0 → 1.6.1
- `package.json`: 1.4.0 → 1.4.1
- `CHANGELOG.md`: Added v1.6.1 hotfix entry

---

## Publication Steps

### 1. Sync to Public Repo
```bash
cd /Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus
bash scripts/sync_public_repo.sh
```

### 2. Commit and Tag
```bash
cd /Users/lokeshgarg/ai-mvp-backend/nucleus-mcp
git add .
git commit -m "🔥 Hotfix v1.6.1: Restore missing anon_telemetry.py implementation"
git push origin main
git tag -a v1.6.1 -m "Hotfix v1.6.1: Critical telemetry fix"
git push origin v1.6.1
```

### 3. Publish to PyPI
```bash
cd /Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus
python3 -m twine upload dist/*
# Username: __token__
# Password: <your-pypi-token>
```

### 4. Publish to npm
```bash
cd /Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/npm-wrapper
npm publish --access public
```

### 5. Create GitHub Release
```bash
# Visit: https://github.com/eidetic-works/nucleus-mcp/releases/new
# Tag: v1.6.1
# Title: v1.6.1 - Critical Telemetry Hotfix
# Body: See CHANGELOG.md v1.6.1 entry
```

---

## Communication Plan

### User Notification

**Recommended channels:**
1. GitHub release notes (automatic for users watching releases)
2. PyPI release page (automatic)
3. npm release page (automatic)
4. Discord/Slack announcement (if applicable)

**Message template:**
```
🔥 Critical Hotfix: Nucleus v1.6.1 Released

We discovered that v1.6.0 shipped with a broken telemetry module. 
All v1.6.0 users should upgrade immediately:

pip install --upgrade nucleus-mcp==1.6.1
npm install nucleus-mcp@1.4.1

What was fixed:
- Restored missing record_anon_command() implementation
- Anonymous telemetry now works correctly
- Verified end-to-end: SDK → Cloudflare → OTel → Jaeger

No action required beyond upgrading. Telemetry is opt-out by default.
Opt out: export NUCLEUS_ANON_TELEMETRY=false

Full details: https://github.com/eidetic-works/nucleus-mcp/releases/tag/v1.6.1
```

---

## Lessons Learned

**What went wrong:**
- `anon_telemetry.py` was accidentally stripped to a stub before v1.6.0 release
- Pre-launch validation didn't catch missing function implementations
- Silent `except Exception: pass` blocks masked the issue

**Improvements for future releases:**
1. Add import smoke test: `from module import function` for all public APIs
2. Add runtime smoke test: actually call telemetry functions in CI
3. Review all `except Exception: pass` blocks for better error visibility
4. Add function existence checks to pre-launch validation

**Pre-launch validation enhancement:**
```python
# Add to tests/test_pre_launch_validation.py
def test_anon_telemetry_functions_exist():
    from mcp_server_nucleus.runtime.anon_telemetry import (
        record_anon_command,
        shutdown_anon_telemetry,
        show_first_run_notice,
        reset_anon_telemetry_state,
        is_anon_telemetry_enabled,
    )
    assert callable(record_anon_command)
    assert callable(shutdown_anon_telemetry)
    # ... etc
```

---

## Status

- [x] Root cause identified
- [x] Fix implemented and tested
- [x] Version bumped (1.6.1 / 1.4.1)
- [x] CHANGELOG updated
- [x] Package built successfully
- [ ] Sync to public repo
- [ ] Create Git tag v1.6.1
- [ ] Publish to PyPI
- [ ] Publish to npm
- [ ] Create GitHub release
- [ ] Notify users

**Ready for publication.**
