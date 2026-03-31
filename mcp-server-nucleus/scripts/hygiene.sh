#!/bin/bash
# =============================================================================
# NUCLEUS HYGIENE CHECK — Weekly House Inspection
# =============================================================================
# A single-founder safety net. Run weekly (cron), before work sessions, or
# whenever something feels off. Zero interaction, pure diagnostics.
#
# Usage:
#   bash scripts/hygiene.sh            # Full check (~30s)
#   bash scripts/hygiene.sh --quick    # Critical checks only (~5s)
#   bash scripts/hygiene.sh --fix      # Auto-fix safe issues (stale pycache, etc.)
#
# Layers:
#   Pre-commit hook  → catches leaks at keystroke time
#   Pre-push hook    → blocks before anything leaves the machine
#   Release gates    → 17 gates before any publish
#   THIS SCRIPT      → catches drift, rot, and neglect between releases
#
# Output: stdout summary + .brain/hygiene/report.json (machine-readable)
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_DIR="$(dirname "$SCRIPT_DIR")"
MONO_DIR="$(dirname "$MCP_DIR")"
PUBLIC_DIR="$MONO_DIR/nucleus-mcp"
LANDING_DIR="$MONO_DIR/nucleus-landing"

QUICK=false
FIX=false
ISSUES=0
WARNINGS=0
FIXED=0

for arg in "$@"; do
    case $arg in
        --quick)  QUICK=true ;;
        --fix)    FIX=true ;;
        --help|-h)
            head -20 "$0" | grep -E '^\s*#' | sed 's/^# //' | sed 's/^#//'
            exit 0
            ;;
    esac
done

issue() {
    echo -e "  ${RED}✗${NC} $1"
    ISSUES=$((ISSUES + 1))
}
warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}
ok() {
    echo -e "  ${GREEN}✓${NC} $1"
}
fixed() {
    echo -e "  ${GREEN}⚡${NC} $1 (auto-fixed)"
    FIXED=$((FIXED + 1))
}

# Read version from pyproject.toml
cd "$MCP_DIR"
VERSION=$(python3 -c "
import re
with open('pyproject.toml') as f:
    for line in f:
        m = re.match(r'version\s*=\s*\"(.+?)\"', line)
        if m:
            print(m.group(1))
            break
" 2>/dev/null || echo "unknown")

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  NUCLEUS HYGIENE CHECK — v${VERSION}${NC}"
echo -e "${BOLD}  $(date '+%Y-%m-%d %H:%M')${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""

# =============================================================================
# H1. IDENTITY LEAK SCAN (most critical — catches what pre-commit might miss)
# =============================================================================
echo -e "${BLUE}[H1] Identity leak scan (tracked files)...${NC}"
cd "$MCP_DIR"

IDENTITY_PATTERNS='lokeshgarg\|lokesh\.iitr\|mailforlkgarg\|gentlequest\.app\|believe_it_bot'

# Scan source code only (src/ and README — the files that ship via PyPI/NPM)
IDENTITY_HITS=$(grep -rl --include='*.py' --include='*.md' --include='*.json' --include='*.toml' "$IDENTITY_PATTERNS" src/ README.md 2>/dev/null | grep -v '__pycache__' | head -10 || true)

if [ -n "$IDENTITY_HITS" ]; then
    issue "H1: Identity strings found in shippable source (src/ or README):"
    echo "$IDENTITY_HITS" | sed 's/^/    /'
else
    ok "H1: No identity leaks in shippable source"
fi

# Docs are export-ignored — identity there is expected (internal docs)
IDENTITY_DOCS=$(grep -rl --include='*.md' "$IDENTITY_PATTERNS" docs/ 2>/dev/null | head -5 || true)
if [ -n "$IDENTITY_DOCS" ]; then
    ok "H1: Identity in docs/ (export-ignored, expected)"
fi

# Also check the public repo if it exists
if [ -d "$PUBLIC_DIR/src" ]; then
    PUB_IDENTITY=$(grep -rl --include='*.py' --include='*.md' --include='*.json' "$IDENTITY_PATTERNS" "$PUBLIC_DIR/src/" 2>/dev/null | head -5 || true)
    if [ -n "$PUB_IDENTITY" ]; then
        issue "H1: Identity strings in PUBLIC repo:"
        echo "$PUB_IDENTITY" | sed "s|$PUBLIC_DIR/||" | sed 's/^/    /'
    else
        ok "H1: Public repo clean of identity strings"
    fi
fi

# =============================================================================
# H2. SECRET PATTERNS IN TRACKED FILES
# =============================================================================
echo -e "${BLUE}[H2] Secret pattern scan...${NC}"
cd "$MCP_DIR"

SECRET_HITS=$(grep -rn --include='*.py' --include='*.json' --include='*.yaml' --include='*.yml' --include='*.toml' --include='*.md' --include='*.js' -E 'AIzaSy[A-Za-z0-9_-]{33}|pplx-[A-Za-z0-9]{40,}|sk_[a-f0-9]{40,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|pypi-[A-Za-z0-9]{50,}' src/ 2>/dev/null | grep -v '__pycache__' | head -5 || true)

if [ -n "$SECRET_HITS" ]; then
    issue "H2: Potential secrets in tracked files:"
    echo "$SECRET_HITS" | sed 's/^/    /'
else
    ok "H2: No secret patterns in source"
fi

# =============================================================================
# H3. FORBIDDEN FILES IN STAGING/TRACKED
# =============================================================================
echo -e "${BLUE}[H3] Forbidden files check...${NC}"
cd "$MONO_DIR"

# Exclude .example files (templates, not secrets) and .brain/identity (node identity, expected)
FORBIDDEN=$(git ls-files -- '*.env' '*.env.*' '*/.env' '*/.env.*' '*.pem' '*.key' '*credentials*.json' '*client_secret*.json' '*.pypirc' 2>/dev/null | grep -v '\.example$' | grep -v '\.brain/identity/' | head -10 || true)
if [ -n "$FORBIDDEN" ]; then
    issue "H3: Forbidden files tracked by git:"
    echo "$FORBIDDEN" | sed 's/^/    /'
else
    ok "H3: No forbidden files tracked"
fi

# =============================================================================
# H4. PYTHON SYNTAX (fast py_compile)
# =============================================================================
echo -e "${BLUE}[H4] Python syntax check...${NC}"
cd "$MCP_DIR"

PY_BROKEN=0
PY_TOTAL=0
for pyfile in $(find src/ -name '*.py' -not -path '*/__pycache__/*' 2>/dev/null); do
    PY_TOTAL=$((PY_TOTAL + 1))
    if ! python3 -m py_compile "$pyfile" 2>/dev/null; then
        issue "H4: Syntax error: $pyfile"
        PY_BROKEN=$((PY_BROKEN + 1))
    fi
done

if [ "$PY_BROKEN" -eq 0 ]; then
    ok "H4: All $PY_TOTAL Python files compile"
fi

# =============================================================================
# H5. STALE __pycache__ IN PUBLIC REPO (identity can bake into bytecode)
# =============================================================================
echo -e "${BLUE}[H5] Stale bytecode check...${NC}"

PYCACHE_COUNT=0
if [ -d "$PUBLIC_DIR" ]; then
    PYCACHE_COUNT=$(find "$PUBLIC_DIR" -type d -name '__pycache__' 2>/dev/null | wc -l | tr -d ' ')
fi
PYCACHE_MCP=$(find "$MCP_DIR" -type d -name '__pycache__' 2>/dev/null | wc -l | tr -d ' ')

if [ "$PYCACHE_COUNT" -gt 0 ]; then
    if [ "$FIX" = true ]; then
        find "$PUBLIC_DIR" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
        fixed "H5: Removed $PYCACHE_COUNT __pycache__ dirs from public repo"
    else
        warn "H5: $PYCACHE_COUNT __pycache__ dirs in public repo (use --fix to clean)"
    fi
else
    ok "H5: No stale bytecode in public repo"
fi

if [ "$QUICK" = true ]; then
    echo ""
    echo -e "${BLUE}[Quick mode — skipping H6-H12]${NC}"
    echo ""
else

# =============================================================================
# H6. PUBLIC REPO DIVERGENCE
# =============================================================================
echo -e "${BLUE}[H6] Public repo divergence check...${NC}"

if [ -d "$PUBLIC_DIR/.git" ]; then
    cd "$PUBLIC_DIR"
    LOCAL_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "")
    REMOTE_HEAD=$(git ls-remote origin HEAD 2>/dev/null | awk '{print $1}' || echo "")

    if [ -n "$LOCAL_HEAD" ] && [ -n "$REMOTE_HEAD" ]; then
        if [ "$LOCAL_HEAD" = "$REMOTE_HEAD" ]; then
            ok "H6: Public repo in sync with remote"
        else
            # Check how many commits apart
            AHEAD=$(git rev-list "$REMOTE_HEAD".."$LOCAL_HEAD" --count 2>/dev/null || echo "?")
            BEHIND=$(git rev-list "$LOCAL_HEAD".."$REMOTE_HEAD" --count 2>/dev/null || echo "?")
            warn "H6: Public repo diverged — ahead: $AHEAD, behind: $BEHIND"
        fi
    else
        warn "H6: Could not check remote (offline?)"
    fi

    # Check for uncommitted changes in public repo
    PUB_DIRTY=$(git status --porcelain 2>/dev/null | head -3)
    if [ -n "$PUB_DIRTY" ]; then
        warn "H6: Uncommitted changes in public repo"
        echo "$PUB_DIRTY" | sed 's/^/    /'
    fi
else
    warn "H6: Public repo not found at $PUBLIC_DIR"
fi

# =============================================================================
# H7. VERSION CONSISTENCY
# =============================================================================
echo -e "${BLUE}[H7] Version consistency check...${NC}"
cd "$MCP_DIR"

# pyproject.toml (source of truth)
ok "H7: pyproject.toml = v${VERSION}"

# npm-wrapper
NPM_VER=$(node -p "require('./npm-wrapper/package.json').version" 2>/dev/null || echo "unknown")
if [ "$NPM_VER" = "$VERSION" ]; then
    ok "H7: npm-wrapper = v${NPM_VER}"
else
    warn "H7: npm-wrapper = v${NPM_VER} (expected v${VERSION})"
fi

# CLI header in __init__.py or main
CLI_VER=$(grep -oE 'version\s*=\s*"[0-9.]*"' src/mcp_server_nucleus/__init__.py 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "n/a")
if [ "$CLI_VER" != "n/a" ] && [ "$CLI_VER" != "$VERSION" ]; then
    warn "H7: __init__.py version = $CLI_VER (expected $VERSION)"
fi

# CHANGELOG
if ! grep -q "## v${VERSION}\|## \[${VERSION}\]\|## ${VERSION}" CHANGELOG.md 2>/dev/null; then
    warn "H7: CHANGELOG.md missing entry for v${VERSION}"
else
    ok "H7: CHANGELOG.md has v${VERSION} entry"
fi

# =============================================================================
# H8. TEST HEALTH
# =============================================================================
echo -e "${BLUE}[H8] Test health check...${NC}"
cd "$MCP_DIR"

if [ -d "tests" ]; then
    TEST_COUNT=$(PYTHONPATH=src python3 -m pytest tests/ --collect-only -q 2>/dev/null | tail -1 | grep -oE '^[0-9]+' || echo "0")
    TEST_COUNT=$(echo "$TEST_COUNT" | head -1 | tr -d '[:space:]')
    [ -z "$TEST_COUNT" ] && TEST_COUNT="0"
    if [ "$TEST_COUNT" -gt 0 ] 2>/dev/null; then
        ok "H8: $TEST_COUNT tests discoverable"
        # Quick pass/fail: run core tests only (60s kill)
        PYTEST_RESULT=$(PYTHONPATH=src python3 -m pytest tests/test_core.py -x -q --tb=line 2>&1 | tail -3 || true)
        if echo "$PYTEST_RESULT" | grep -q "passed"; then
            ok "H8: Core tests passing"
        else
            warn "H8: Core tests failing (run pytest for details)"
        fi
    else
        warn "H8: No tests discovered"
    fi
else
    warn "H8: No tests/ directory"
fi

# =============================================================================
# H9. REPO SIZE + .brain SIZE
# =============================================================================
echo -e "${BLUE}[H9] Size monitoring...${NC}"
cd "$MONO_DIR"

MONO_SIZE=$(du -sh . 2>/dev/null | cut -f1)
ok "H9: Mono-repo size: $MONO_SIZE"

if [ -d ".brain" ]; then
    BRAIN_SIZE=$(du -sh .brain 2>/dev/null | cut -f1)
    BRAIN_BYTES=$(du -s .brain 2>/dev/null | cut -f1)
    # Warn if .brain > 100MB (100000 KB)
    if [ "$BRAIN_BYTES" -gt 100000 ] 2>/dev/null; then
        warn "H9: .brain is $BRAIN_SIZE (>100MB — consider cleanup_ledger.py)"
    else
        ok "H9: .brain size: $BRAIN_SIZE"
    fi
fi

# Large files in git (>5MB)
LARGE_FILES=$(git ls-files -z 2>/dev/null | xargs -0 -I{} sh -c 'size=$(wc -c < "{}" 2>/dev/null); [ "$size" -gt 5242880 ] && echo "{} ($(echo $size | awk "{printf \"%.1fMB\", \$1/1048576}"))"' 2>/dev/null | head -5 || true)
if [ -n "$LARGE_FILES" ]; then
    warn "H9: Large files tracked by git (>5MB):"
    echo "$LARGE_FILES" | sed 's/^/    /'
fi

# =============================================================================
# H10. GIT HYGIENE
# =============================================================================
echo -e "${BLUE}[H10] Git hygiene...${NC}"
cd "$MONO_DIR"

# Uncommitted changes
DIRTY_COUNT=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ "$DIRTY_COUNT" -gt 50 ]; then
    warn "H10: $DIRTY_COUNT uncommitted changes in mono-repo (getting messy)"
elif [ "$DIRTY_COUNT" -gt 0 ]; then
    ok "H10: $DIRTY_COUNT uncommitted changes (normal)"
else
    ok "H10: Working tree clean"
fi

# Stale branches (>30 days old)
STALE_BRANCHES=$(git for-each-ref --sort=-committerdate --format='%(refname:short) %(committerdate:relative)' refs/heads/ 2>/dev/null | grep -E '(month|year)' | head -5 || true)
if [ -n "$STALE_BRANCHES" ]; then
    warn "H10: Stale branches (>1 month):"
    echo "$STALE_BRANCHES" | sed 's/^/    /'
fi

# Hooks integrity
if [ ! -f ".git/hooks/pre-commit" ] || [ ! -x ".git/hooks/pre-commit" ]; then
    issue "H10: Pre-commit hook missing or not executable"
else
    ok "H10: Pre-commit hook active"
fi

if [ ! -f ".git/hooks/pre-push" ] || [ ! -x ".git/hooks/pre-push" ]; then
    issue "H10: Pre-push hook missing or not executable"
else
    ok "H10: Pre-push hook active"
fi

# =============================================================================
# H11. DEPENDENCY HEALTH
# =============================================================================
echo -e "${BLUE}[H11] Dependency health...${NC}"
cd "$MCP_DIR"

if command -v pip &>/dev/null; then
    # Check for known vulnerabilities
    VULN_COUNT=$(pip audit 2>/dev/null | grep -c 'vulnerability' | tr -d '[:space:]' || echo "0")
    [ -z "$VULN_COUNT" ] && VULN_COUNT="0"
    if [ "$VULN_COUNT" -gt 0 ] 2>/dev/null; then
        warn "H11: $VULN_COUNT known vulnerabilities (run: pip audit)"
    else
        ok "H11: No known vulnerabilities"
    fi
else
    warn "H11: pip not available for audit"
fi

# =============================================================================
# H12. .gitattributes INTEGRITY
# =============================================================================
echo -e "${BLUE}[H12] Export-ignore integrity...${NC}"
cd "$MCP_DIR"

EXPORT_COUNT=$(grep -c 'export-ignore' .gitattributes 2>/dev/null || echo "0")
ROOT_EXPORT_COUNT=$(grep -c 'export-ignore' "$MONO_DIR/.gitattributes" 2>/dev/null || echo "0")

if [ "$EXPORT_COUNT" -lt 10 ]; then
    issue "H12: mcp-server-nucleus/.gitattributes has only $EXPORT_COUNT export-ignore rules"
else
    ok "H12: Package .gitattributes: $EXPORT_COUNT export-ignore rules"
fi

if [ "$ROOT_EXPORT_COUNT" -lt 20 ]; then
    issue "H12: Root .gitattributes safety net has only $ROOT_EXPORT_COUNT rules"
else
    ok "H12: Root .gitattributes safety net: $ROOT_EXPORT_COUNT rules"
fi

# Check critical files are in export-ignore
for MUST_IGNORE in "release.sh" "sync_public_repo.sh" "validate_public_surface.sh" "hygiene.sh"; do
    if ! grep -q "$MUST_IGNORE.*export-ignore" .gitattributes 2>/dev/null; then
        warn "H12: $MUST_IGNORE not in .gitattributes export-ignore"
    fi
done

fi  # end of non-quick checks

# =============================================================================
# REPORT
# =============================================================================
echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
if [ "$ISSUES" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e "${GREEN}  CLEAN HOUSE — 0 issues, 0 warnings${NC}"
elif [ "$ISSUES" -eq 0 ]; then
    echo -e "${YELLOW}  MOSTLY CLEAN — 0 issues, $WARNINGS warning(s)${NC}"
else
    echo -e "${RED}  NEEDS ATTENTION — $ISSUES issue(s), $WARNINGS warning(s)${NC}"
fi
[ "$FIXED" -gt 0 ] && echo -e "${GREEN}  Auto-fixed: $FIXED item(s)${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Write machine-readable report
REPORT_DIR="$MONO_DIR/.brain/hygiene"
mkdir -p "$REPORT_DIR" 2>/dev/null || true
cat > "$REPORT_DIR/report.json" 2>/dev/null <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "version": "$VERSION",
  "issues": $ISSUES,
  "warnings": $WARNINGS,
  "fixed": $FIXED,
  "mode": "$([ "$QUICK" = true ] && echo 'quick' || echo 'full')"
}
EOF

# Exit code: 1 if issues, 0 if clean/warnings only
[ "$ISSUES" -gt 0 ] && exit 1
exit 0
